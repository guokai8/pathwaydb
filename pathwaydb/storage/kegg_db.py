"""KEGG annotation storage with DataFrame-like interface."""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass, asdict
from urllib.request import urlopen


@dataclass
class KEGGAnnotationRecord:
    """Single KEGG pathway-gene annotation record."""
    gene_id: str
    gene_symbol: str
    pathway_id: str
    pathway_name: Optional[str] = None
    organism: Optional[str] = None
    
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
                PRIMARY KEY (gene_id, pathway_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_kegg_gene_id ON kegg_annotations(gene_id);
            CREATE INDEX IF NOT EXISTS idx_kegg_gene_symbol ON kegg_annotations(gene_symbol);
            CREATE INDEX IF NOT EXISTS idx_kegg_pathway_id ON kegg_annotations(pathway_id);
            CREATE INDEX IF NOT EXISTS idx_kegg_organism ON kegg_annotations(organism);
            
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
                (gene_id, gene_symbol, pathway_id, pathway_name, organism)
                VALUES (?, ?, ?, ?, ?)
            """, (
                record.gene_id,
                record.gene_symbol,
                record.pathway_id,
                record.pathway_name,
                record.organism
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
        organism: Optional[str] = None
    ) -> List[KEGGAnnotationRecord]:
        """Flexible filtering with multiple criteria."""
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
        with urlopen(pathway_url, timeout=300) as response:
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
        with urlopen(link_url, timeout=300) as response:
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

