"""KEGG annotation storage with DataFrame-like interface."""
import sqlite3
from typing import List, Optional, Dict, Union
from dataclasses import dataclass, asdict


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
        
        # Get as list of dicts (like DataFrame.to_dict('records'))
        records = db.to_records()
        
        # Get as dict of lists (like DataFrame.to_dict('list'))
        data = db.to_dict()
        
        # Filter
        filtered = db.filter(gene_symbols=['TP53'], pathway_ids=['hsa05200'])
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def query_by_gene(
        self, 
        gene_ids: List[str], 
        id_type: str = 'symbol'
    ) -> List[KEGGAnnotationRecord]:
        """
        Query annotations by gene identifiers.
        
        Args:
            gene_ids: List of gene identifiers
            id_type: 'symbol' or 'id' (KEGG gene ID)
        
        Returns:
            List of KEGGAnnotationRecord objects
        """
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
        """
        Flexible filtering with multiple criteria.
        
        Example:
            # Get TP53 pathways in cancer-related categories
            db.filter(
                gene_symbols=['TP53'],
                pathway_ids=['hsa05200', 'hsa05210']
            )
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
        """
        Export as list of dictionaries (like pandas DataFrame.to_dict('records')).
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            [{'gene_id': 'hsa:7157', 'gene_symbol': 'TP53', ...}, ...]
        """
        query = "SELECT * FROM kegg_annotations"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def to_dict(self, limit: Optional[int] = None) -> Dict[str, List[str]]:
        """
        Export as dictionary of lists (like pandas DataFrame.to_dict('list')).
        
        Returns:
            {
                'gene_id': ['hsa:7157', 'hsa:672', ...],
                'gene_symbol': ['TP53', 'BRCA1', ...],
                'pathway_id': ['hsa05200', 'hsa05210', ...],
                ...
            }
        """
        query = "SELECT * FROM kegg_annotations"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            return {}
        
        # Initialize dict with column names
        result = {key: [] for key in rows[0].keys()}
        
        # Populate lists
        for row in rows:
            for key in result:
                result[key].append(row[key])
        
        return result
    
    def to_gene_sets(self) -> Dict[str, List[str]]:
        """
        Convert to gene sets format for enrichment analysis.
        
        Returns:
            {
                'hsa05200': ['TP53', 'MYC', 'EGFR', ...],
                'hsa05210': ['TP53', 'BRCA1', ...],
                ...
            }
        """
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
    return_db: bool = True,
    kegg_client = None  # Will be KEGG instance
) -> Optional[KEGGAnnotationDB]:
    """
    Download KEGG annotations and return queryable database.
    
    Args:
        organism: KEGG organism code (e.g., 'hsa' for human)
        output_path: SQLite database output path
        return_db: If True, return KEGGAnnotationDB instance
        kegg_client: KEGG client instance (if None, creates new one)
    
    Returns:
        KEGGAnnotationDB instance if return_db=True, else None
    
    Example:
        # Download and get database
        db = download_kegg_annotations(
            organism='hsa',
            output_path='kegg_human.db'
        )
        
        # Query immediately
        tp53_pathways = db.query_by_gene(['TP53'])
        
        # Export as records
        records = db.to_records(limit=1000)
    """
    # Import here to avoid circular dependency
    if kegg_client is None:
        from ..connectors.kegg import KEGG
        kegg_client = KEGG(species=organism)
    
    db = sqlite3.connect(output_path)
    db.execute("""
        CREATE TABLE IF NOT EXISTS kegg_annotations (
            gene_id TEXT,
            gene_symbol TEXT,
            pathway_id TEXT,
            pathway_name TEXT,
            organism TEXT,
            PRIMARY KEY (gene_id, pathway_id)
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_kegg_gene_id ON kegg_annotations(gene_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_kegg_gene_symbol ON kegg_annotations(gene_symbol)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_kegg_pathway ON kegg_annotations(pathway_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_kegg_organism ON kegg_annotations(organism)")
    
    print(f"Downloading KEGG pathway annotations for {organism}...")
    
    # Get all pathways first for pathway names
    pathway_names = {}
    try:
        pathways = kegg_client.list_pathways()
        for pw in pathways:
            pathway_names[pw.id] = pw.name
    except Exception as e:
        print(f"Warning: Could not fetch pathway names: {e}")
    
    # Get pathway-gene links
    url = f"https://rest.kegg.jp/link/pathway/{organism}"
    from urllib.request import urlopen
    
    count = 0
    try:
        with urlopen(url, timeout=300) as response:
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
                
                db.execute(
                    "INSERT OR IGNORE INTO kegg_annotations VALUES (?, ?, ?, ?, ?)",
                    (gene_id, gene_symbol, pathway_id, pathway_names.get(pathway_id), organism)
                )
                
                count += 1
                if count % 1000 == 0:
                    db.commit()
                    print(f"  Processed {count:,} annotations...")
        
        db.commit()
        print(f"✓ Stored {count:,} annotations in {output_path}")
        
    finally:
        db.close()
    
    if return_db:
        return KEGGAnnotationDB(output_path)
    return None


def load_kegg_annotations(db_path: str) -> KEGGAnnotationDB:
    """Load existing KEGG annotation database."""
    return KEGGAnnotationDB(db_path)


