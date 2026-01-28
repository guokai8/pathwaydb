"""KEGG annotation storage with DataFrame-like interface."""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass, asdict
from urllib.request import urlopen, Request


@dataclass
class KEGGAnnotationRecord:
    """Single KEGG pathway-gene annotation record."""
    gene_id: str
    gene_symbol: str
    pathway_id: str
    pathway_name: Optional[str] = None
    organism: Optional[str] = None
    level1: Optional[str] = None  # Top-level category (e.g., "Metabolism")
    level2: Optional[str] = None  # Sub-category (e.g., "Carbohydrate metabolism")
    level3: Optional[str] = None  # Pathway name (same as pathway_name)

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return asdict(self)


class KEGGAnnotationDB:
    """
    SQLite-backed KEGG annotation database with DataFrame-like query interface.
    
    Usage:
        db = KEGGAnnotationDB('kegg_annotations.db')
        
        # Query methods
        annotations = db.query_by_gene(['TP53', 'BRCA1'])
        annotations = db.query_by_pathway('hsa05200')
        
        # Get as list of dicts
        records = db.to_records()
        
        # Get as dict of lists
        data = db.to_dict()
        
        # Filter
        filtered = db.filter(gene_symbols=['TP53'])
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Create annotation tables with indexes."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS kegg_annotations (
                gene_id TEXT NOT NULL,
                gene_symbol TEXT,
                pathway_id TEXT NOT NULL,
                pathway_name TEXT,
                organism TEXT,
                level1 TEXT,
                level2 TEXT,
                level3 TEXT,
                PRIMARY KEY (gene_id, pathway_id)
            );

            CREATE INDEX IF NOT EXISTS idx_kegg_gene_id ON kegg_annotations(gene_id);
            CREATE INDEX IF NOT EXISTS idx_kegg_gene_symbol ON kegg_annotations(gene_symbol);
            CREATE INDEX IF NOT EXISTS idx_kegg_pathway_id ON kegg_annotations(pathway_id);
            CREATE INDEX IF NOT EXISTS idx_kegg_organism ON kegg_annotations(organism);
            CREATE INDEX IF NOT EXISTS idx_kegg_level1 ON kegg_annotations(level1);
            CREATE INDEX IF NOT EXISTS idx_kegg_level2 ON kegg_annotations(level2);

            CREATE TABLE IF NOT EXISTS pathway_hierarchy (
                pathway_id TEXT PRIMARY KEY,
                pathway_name TEXT,
                level1 TEXT,
                level2 TEXT,
                level3 TEXT
            );

            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        self.conn.commit()
    
    def insert_batch(self, records: List[KEGGAnnotationRecord]):
        """Batch insert annotations."""
        cursor = self.conn.cursor()
        for record in records:
            cursor.execute("""
                INSERT OR REPLACE INTO kegg_annotations
                (gene_id, gene_symbol, pathway_id, pathway_name, organism, level1, level2, level3)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.gene_id,
                record.gene_symbol,
                record.pathway_id,
                record.pathway_name,
                record.organism,
                record.level1,
                record.level2,
                record.level3
            ))
        self.conn.commit()
    
    def query_by_gene(
        self, 
        gene_ids: List[str], 
        id_type: str = 'symbol'
    ) -> List[KEGGAnnotationRecord]:
        """Query annotations by gene identifiers."""
        column = 'gene_symbol' if id_type == 'symbol' else 'gene_id'
        placeholders = ','.join('?' * len(gene_ids))
        
        query = f"""
            SELECT gene_id, gene_symbol, pathway_id, pathway_name, organism
            FROM kegg_annotations
            WHERE {column} IN ({placeholders})
        """
        
        cursor = self.conn.execute(query, gene_ids)
        return [KEGGAnnotationRecord(**dict(row)) for row in cursor.fetchall()]
    
    def query_by_pathway(self, pathway_ids: Union[str, List[str]]) -> List[KEGGAnnotationRecord]:
        """Query genes annotated with specific pathways."""
        if isinstance(pathway_ids, str):
            pathway_ids = [pathway_ids]
        
        placeholders = ','.join('?' * len(pathway_ids))
        query = f"""
            SELECT gene_id, gene_symbol, pathway_id, pathway_name, organism
            FROM kegg_annotations
            WHERE pathway_id IN ({placeholders})
        """
        
        cursor = self.conn.execute(query, pathway_ids)
        return [KEGGAnnotationRecord(**dict(row)) for row in cursor.fetchall()]
    
    def filter(
        self,
        gene_ids: Optional[List[str]] = None,
        gene_symbols: Optional[List[str]] = None,
        pathway_ids: Optional[List[str]] = None,
        pathway_name: Optional[str] = None,
        organism: Optional[str] = None
    ) -> List[KEGGAnnotationRecord]:
        """
        Flexible filtering with multiple criteria.

        Args:
            gene_ids: Filter by gene IDs (exact match)
            gene_symbols: Filter by gene symbols (exact match)
            pathway_ids: Filter by pathway IDs (exact match)
            pathway_name: Filter by pathway name (case-insensitive substring match)
            organism: Filter by organism code

        Returns:
            List of KEGGAnnotationRecord objects

        Example:
            >>> db = KEGGAnnotationDB('kegg_human.db')
            >>> # Find all cancer-related pathways
            >>> results = db.filter(pathway_name='cancer')
            >>> # Find specific genes in specific pathways
            >>> results = db.filter(gene_symbols=['TP53', 'BRCA1'], pathway_name='cancer')
        """
        conditions = []
        params = []

        if gene_ids:
            placeholders = ','.join('?' * len(gene_ids))
            conditions.append(f"gene_id IN ({placeholders})")
            params.extend(gene_ids)

        if gene_symbols:
            placeholders = ','.join('?' * len(gene_symbols))
            conditions.append(f"gene_symbol IN ({placeholders})")
            params.extend(gene_symbols)

        if pathway_ids:
            placeholders = ','.join('?' * len(pathway_ids))
            conditions.append(f"pathway_id IN ({placeholders})")
            params.extend(pathway_ids)

        if pathway_name:
            conditions.append("pathway_name LIKE ?")
            params.append(f"%{pathway_name}%")

        if organism:
            conditions.append("organism = ?")
            params.append(organism)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT gene_id, gene_symbol, pathway_id, pathway_name, organism
            FROM kegg_annotations
            WHERE {where_clause}
        """

        cursor = self.conn.execute(query, params)
        return [KEGGAnnotationRecord(**dict(row)) for row in cursor.fetchall()]
    
    def to_records(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Export as list of dictionaries."""
        query = "SELECT * FROM kegg_annotations"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def to_dict(self, limit: Optional[int] = None) -> Dict[str, List[str]]:
        """Export as dictionary of lists."""
        query = "SELECT * FROM kegg_annotations"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            return {}
        
        result = {key: [] for key in rows[0].keys()}
        for row in rows:
            for key in result:
                result[key].append(row[key])
        
        return result
    
    def to_gene_sets(self) -> Dict[str, List[str]]:
        """Convert to gene sets format for enrichment analysis."""
        query = """
            SELECT pathway_id, GROUP_CONCAT(gene_symbol) as genes
            FROM kegg_annotations
            GROUP BY pathway_id
        """

        cursor = self.conn.execute(query)
        return {row['pathway_id']: row['genes'].split(',') for row in cursor.fetchall()}

    def to_dataframe(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Export to DataFrame-compatible format for enrichment analysis.

        Returns data in format compatible with pandas DataFrame:
        - GeneID: Gene symbol
        - PATH: Pathway ID (e.g., 'hsa04110')
        - Annot: Pathway name/description
        - Level1: Top-level category (e.g., 'Metabolism')
        - Level2: Sub-category (e.g., 'Carbohydrate metabolism')
        - Level3: Pathway name (same as Annot)

        Args:
            limit: Optional limit on number of rows

        Returns:
            List of dicts with keys: GeneID, PATH, Annot, Level1, Level2, Level3

        Example:
            >>> db = KEGGAnnotationDB('kegg_human.db')
            >>> df_data = db.to_dataframe()
            >>> import pandas as pd
            >>> df = pd.DataFrame(df_data)
            >>> print(df.head())
               GeneID    PATH                          Annot            Level1
            0     A2M  hsa4610  Complement and coagulation...  Organismal Systems
        """
        query = """
            SELECT
                gene_symbol as GeneID,
                pathway_id as PATH,
                pathway_name as Annot,
                level1 as Level1,
                level2 as Level2,
                level3 as Level3
            FROM kegg_annotations
            ORDER BY gene_symbol, pathway_id
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor = self.conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def stats(self) -> Dict[str, int]:
        """Get database statistics."""
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total_annotations,
                COUNT(DISTINCT gene_id) as unique_genes,
                COUNT(DISTINCT pathway_id) as unique_pathways,
                COUNT(DISTINCT organism) as organisms
            FROM kegg_annotations
        """)
        
        return dict(cursor.fetchone())
    
    def set_metadata(self, key: str, value: str):
        """Set metadata key-value pair."""
        self.conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()
    
    def get_metadata(self, key: str) -> Optional[str]:
        """Get metadata value."""
        cursor = self.conn.execute(
            "SELECT value FROM metadata WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        return row['value'] if row else None
    
    def populate_pathway_hierarchy(self):
        """
        Populate KEGG pathway hierarchy (Level1, Level2, Level3) from KEGG BRITE.

        Downloads the KEGG pathway classification hierarchy and updates
        all annotations with their category information.

        Level1: Top-level category (e.g., "Metabolism", "Human Diseases")
        Level2: Sub-category (e.g., "Carbohydrate metabolism", "Cancer")
        Level3: Pathway name (same as pathway_name)

        Example:
            >>> db = KEGGAnnotationDB('kegg_human.db')
            >>> db.populate_pathway_hierarchy()
            >>> # Now annotations include Level1, Level2, Level3 columns
        """
        print("Downloading KEGG pathway hierarchy...")

        # Download KEGG BRITE hierarchy for pathways
        url = "https://rest.kegg.jp/get/br:br08901"
        request = Request(url, headers={'User-Agent': 'pathwaydb/0.2.0 (Python)'})

        try:
            with urlopen(request, timeout=60) as response:
                content = response.read().decode('utf-8')
        except Exception as e:
            print(f"Warning: Could not download pathway hierarchy: {e}")
            return

        # Parse the BRITE hierarchy format
        hierarchy = {}  # pathway_number -> (level1, level2, pathway_name)
        current_level1 = None
        current_level2 = None

        for line in content.split('\n'):
            if not line or line.startswith('#') or line.startswith('!'):
                continue

            # Count leading spaces to determine level
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            if indent == 0 and stripped.startswith('A'):
                # Level 1: Top category (e.g., "A Metabolism")
                current_level1 = stripped[1:].strip().lstrip('<b>').rstrip('</b>').strip()
            elif indent == 1 or (indent == 0 and stripped.startswith('B')):
                # Level 2: Sub-category (e.g., "B  Carbohydrate metabolism")
                if stripped.startswith('B'):
                    current_level2 = stripped[1:].strip()
                else:
                    current_level2 = stripped.strip()
            elif indent >= 2 or stripped.startswith('C'):
                # Level 3: Pathway (e.g., "C    00010 Glycolysis")
                if stripped.startswith('C'):
                    stripped = stripped[1:].strip()
                parts = stripped.split(None, 1)
                if len(parts) >= 2 and parts[0].isdigit():
                    pathway_num = parts[0]  # e.g., "00010"
                    pathway_name = parts[1].split('[')[0].strip()  # Remove [PATH:xxx]
                    hierarchy[pathway_num] = (current_level1, current_level2, pathway_name)

        print(f"  Parsed {len(hierarchy)} pathway categories")

        # Update annotations with hierarchy
        # Get all unique pathway IDs from the database
        cursor = self.conn.execute("SELECT DISTINCT pathway_id FROM kegg_annotations")
        pathway_ids = [row[0] for row in cursor.fetchall()]

        updated = 0
        for pathway_id in pathway_ids:
            # Extract pathway number (e.g., "hsa00010" -> "00010")
            pathway_num = pathway_id.replace('path:', '')
            # Remove organism prefix (e.g., "hsa00010" -> "00010")
            if len(pathway_num) > 5:
                pathway_num = pathway_num[-5:]  # Last 5 digits

            if pathway_num in hierarchy:
                level1, level2, level3 = hierarchy[pathway_num]
                self.conn.execute("""
                    UPDATE kegg_annotations
                    SET level1 = ?, level2 = ?, level3 = ?
                    WHERE pathway_id = ?
                """, (level1, level2, level3, pathway_id))
                updated += 1

        # Also store in pathway_hierarchy table for reference
        for pathway_num, (level1, level2, level3) in hierarchy.items():
            self.conn.execute("""
                INSERT OR REPLACE INTO pathway_hierarchy
                (pathway_id, pathway_name, level1, level2, level3)
                VALUES (?, ?, ?, ?, ?)
            """, (pathway_num, level3, level1, level2, level3))

        self.conn.commit()
        print(f"✓ Updated {updated} pathways with hierarchy information")

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def download_kegg_annotations(
    organism: str = 'hsa',
    output_path: str = 'kegg_annotations.db',
    return_db: bool = True
) -> Optional[KEGGAnnotationDB]:
    """
    Download KEGG annotations and return queryable database.
    
    This is a STANDALONE function that does NOT import from connectors.kegg
    to avoid circular imports.
    
    Args:
        organism: KEGG organism code (e.g., 'hsa' for human)
        output_path: SQLite database output path
        return_db: If True, return KEGGAnnotationDB instance
    
    Returns:
        KEGGAnnotationDB instance if return_db=True, else None
    
    Example:
        # Standalone usage
        from pathwaydb.storage.kegg_db import download_kegg_annotations
        
        db = download_kegg_annotations(
            organism='hsa',
            output_path='kegg_human.db'
        )
        
        # Query immediately
        tp53_pathways = db.query_by_gene(['7157'], id_type='symbol')
        print(f"Found {len(tp53_pathways)} pathways")
    """
    print(f"Downloading KEGG pathway annotations for {organism}...")
    
    # Initialize database
    db_obj = KEGGAnnotationDB(output_path)
    
    # Download pathway names first
    pathway_url = f"https://rest.kegg.jp/list/pathway/{organism}"
    pathway_names = {}
    
    try:
        print("Fetching pathway names...")
        request = Request(pathway_url, headers={'User-Agent': 'pathwaydb/0.2.0 (Python)'})
        with urlopen(request, timeout=300) as response:
            for line in response:
                line = line.decode('utf-8').strip()
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) >= 2:
                    pathway_id = parts[0].replace('path:', '')
                    name = parts[1]
                    pathway_names[pathway_id] = name
        
        print(f"  Found {len(pathway_names)} pathways")
    except Exception as e:
        print(f"Warning: Could not fetch pathway names: {e}")
    
    # Download pathway-gene links
    link_url = f"https://rest.kegg.jp/link/pathway/{organism}"
    
    annotations = []
    count = 0
    
    try:
        print("Downloading pathway-gene links...")
        request = Request(link_url, headers={'User-Agent': 'pathwaydb/0.2.0 (Python)'})
        with urlopen(request, timeout=300) as response:
            for line in response:
                line = line.decode('utf-8').strip()
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) != 2:
                    continue
                
                gene_id = parts[0]
                pathway_id = parts[1].replace('path:', '')
                gene_symbol = gene_id.split(':')[1] if ':' in gene_id else gene_id
                
                annotations.append(KEGGAnnotationRecord(
                    gene_id=gene_id,
                    gene_symbol=gene_symbol,
                    pathway_id=pathway_id,
                    pathway_name=pathway_names.get(pathway_id),
                    organism=organism
                ))
                
                count += 1
                if count % 1000 == 0:
                    print(f"  Processed {count:,} annotations...")
        
        print(f"✓ Downloaded {len(annotations)} annotations")
        
        # Store in database
        db_obj.insert_batch(annotations)
        db_obj.set_metadata('kegg_organism', organism)
        print(f"✓ Stored annotations in {output_path}")
    
    except Exception as e:
        db_obj.close()
        raise Exception(f"Failed to download KEGG annotations: {e}")
    
    if return_db:
        return db_obj
    else:
        db_obj.close()
        return None


def load_kegg_annotations(db_path: str) -> KEGGAnnotationDB:
    """Load existing KEGG annotation database."""
    return KEGGAnnotationDB(db_path)

