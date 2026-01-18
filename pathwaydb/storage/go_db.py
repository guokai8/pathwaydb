"""GO annotation storage with DataFrame-like interface."""
import gzip
import sqlite3
from typing import List, Optional, Dict, Union
from urllib.request import urlopen
from dataclasses import dataclass, asdict


@dataclass
class GOAnnotationRecord:
    """Single GO annotation record."""
    gene_id: str
    gene_symbol: str
    go_id: str
    evidence_code: str
    aspect: str  # P=biological_process, F=molecular_function, C=cellular_component
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return asdict(self)


class GOAnnotationDB:
    """
    SQLite-backed GO annotation database with DataFrame-like query interface.
    
    Usage:
        db = GOAnnotationDB('go_annotations.db')
        
        # Query methods
        annotations = db.query_by_gene(['TP53', 'BRCA1'])
        annotations = db.query_by_go_term('GO:0006915')
        annotations = db.query_by_evidence(['EXP', 'IDA'])
        
        # Get as list of dicts
        records = db.to_records()
        
        # Get as dict of lists
        data = db.to_dict()
        
        # Filter and export
        filtered = db.filter(gene_symbols=['TP53'], aspect='P')
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def query_by_gene(
        self, 
        gene_ids: List[str], 
        id_type: str = 'symbol'
    ) -> List[GOAnnotationRecord]:
        """Query annotations by gene identifiers."""
        column = 'gene_symbol' if id_type == 'symbol' else 'gene_id'
        placeholders = ','.join('?' * len(gene_ids))
        
        query = f"""
            SELECT gene_id, gene_symbol, go_id, evidence_code, aspect
            FROM go_annotations
            WHERE {column} IN ({placeholders})
        """
        
        cursor = self.conn.execute(query, gene_ids)
        return [GOAnnotationRecord(**dict(row)) for row in cursor.fetchall()]
    
    def query_by_go_term(self, go_ids: Union[str, List[str]]) -> List[GOAnnotationRecord]:
        """Query genes annotated with specific GO terms."""
        if isinstance(go_ids, str):
            go_ids = [go_ids]
        
        placeholders = ','.join('?' * len(go_ids))
        query = f"""
            SELECT gene_id, gene_symbol, go_id, evidence_code, aspect
            FROM go_annotations
            WHERE go_id IN ({placeholders})
        """
        
        cursor = self.conn.execute(query, go_ids)
        return [GOAnnotationRecord(**dict(row)) for row in cursor.fetchall()]
    
    def query_by_evidence(self, evidence_codes: List[str]) -> List[GOAnnotationRecord]:
        """Query annotations with specific evidence codes."""
        placeholders = ','.join('?' * len(evidence_codes))
        query = f"""
            SELECT gene_id, gene_symbol, go_id, evidence_code, aspect
            FROM go_annotations
            WHERE evidence_code IN ({placeholders})
        """
        
        cursor = self.conn.execute(query, evidence_codes)
        return [GOAnnotationRecord(**dict(row)) for row in cursor.fetchall()]
    
    def filter(
        self,
        gene_ids: Optional[List[str]] = None,
        gene_symbols: Optional[List[str]] = None,
        go_ids: Optional[List[str]] = None,
        evidence_codes: Optional[List[str]] = None,
        aspect: Optional[str] = None
    ) -> List[GOAnnotationRecord]:
        """
        Flexible filtering with multiple criteria.
        
        Example:
            db.filter(
                gene_symbols=['TP53'],
                evidence_codes=['EXP', 'IDA'],
                aspect='P'
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
        
        if go_ids:
            placeholders = ','.join('?' * len(go_ids))
            conditions.append(f"go_id IN ({placeholders})")
            params.extend(go_ids)
        
        if evidence_codes:
            placeholders = ','.join('?' * len(evidence_codes))
            conditions.append(f"evidence_code IN ({placeholders})")
            params.extend(evidence_codes)
        
        if aspect:
            conditions.append("aspect = ?")
            params.append(aspect)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT gene_id, gene_symbol, go_id, evidence_code, aspect
            FROM go_annotations
            WHERE {where_clause}
        """
        
        cursor = self.conn.execute(query, params)
        return [GOAnnotationRecord(**dict(row)) for row in cursor.fetchall()]
    
    def to_records(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Export as list of dictionaries."""
        query = "SELECT * FROM go_annotations"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def to_dict(self, limit: Optional[int] = None) -> Dict[str, List[str]]:
        """Export as dictionary of lists."""
        query = "SELECT * FROM go_annotations"
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
            SELECT go_id, GROUP_CONCAT(gene_symbol) as genes
            FROM go_annotations
            GROUP BY go_id
        """

        cursor = self.conn.execute(query)
        return {row['go_id']: row['genes'].split(',') for row in cursor.fetchall()}

    def to_dataframe(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Export to DataFrame-compatible format for enrichment analysis.

        Returns data in format compatible with pandas DataFrame:
        - GeneID: Gene symbol
        - TERM: GO term ID (e.g., 'GO:0006915')
        - Aspect: Namespace (P=biological_process, F=molecular_function, C=cellular_component)
        - Evidence: Evidence code (e.g., 'EXP', 'IDA', 'IEA')

        Args:
            limit: Optional limit on number of rows

        Returns:
            List of dicts with keys: GeneID, TERM, Aspect, Evidence

        Example:
            >>> db = GOAnnotationDB('go_human.db')
            >>> df_data = db.to_dataframe()
            >>> # If you have pandas installed:
            >>> import pandas as pd
            >>> df = pd.DataFrame(df_data)
            >>> print(df.head())
               GeneID        TERM Aspect Evidence
            0     A2M  GO:0002576      P      IBA
            1     A2M  GO:0006953      P      IEA
        """
        query = """
            SELECT
                gene_symbol as GeneID,
                go_id as TERM,
                aspect as Aspect,
                evidence_code as Evidence
            FROM go_annotations
            ORDER BY gene_symbol, go_id
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
                COUNT(DISTINCT go_id) as unique_terms,
                COUNT(DISTINCT evidence_code) as unique_evidence_codes
            FROM go_annotations
        """)
        
        return dict(cursor.fetchone())
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def download_go_annotations_filtered(
    species: str = 'human',
    evidence_codes: Optional[List[str]] = None,
    output_path: str = 'go_annotations.db',
    return_db: bool = True
) -> Optional[GOAnnotationDB]:
    """Download GO annotations with filtering."""
    TAXID_MAP = {'human': '9606', 'mouse': '10090', 'rat': '10116'}
    taxid = TAXID_MAP.get(species, '9606')
    
    url = f"http://geneontology.org/gene-associations/goa_{species}.gaf.gz"
    valid_evidence = set(evidence_codes) if evidence_codes else None
    
    db = sqlite3.connect(output_path)
    db.execute("""
        CREATE TABLE IF NOT EXISTS go_annotations (
            gene_id TEXT,
            gene_symbol TEXT,
            go_id TEXT,
            evidence_code TEXT,
            aspect TEXT,
            PRIMARY KEY (gene_id, go_id)
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_gene ON go_annotations(gene_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON go_annotations(gene_symbol)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_go ON go_annotations(go_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_evidence ON go_annotations(evidence_code)")
    
    print(f"Downloading GO annotations from {url}...")
    count = 0
    
    try:
        with urlopen(url, timeout=300) as response:
            with gzip.open(response, 'rt') as f:
                for line in f:
                    if line.startswith('!'):
                        continue
                    
                    fields = line.strip().split('\t')
                    if len(fields) < 17:
                        continue
                    
                    gene_id = fields[1]
                    symbol = fields[2]
                    go_id = fields[4]
                    evidence = fields[6]
                    aspect = fields[8]
                    
                    if valid_evidence and evidence not in valid_evidence:
                        continue
                    
                    db.execute(
                        "INSERT OR IGNORE INTO go_annotations VALUES (?, ?, ?, ?, ?)",
                        (gene_id, symbol, go_id, evidence, aspect)
                    )
                    
                    count += 1
                    if count % 100000 == 0:
                        db.commit()
                        print(f"  Processed {count:,} annotations...")
        
        db.commit()
        print(f"✓ Stored {count:,} annotations in {output_path}")
        
    finally:
        db.close()
    
    if return_db:
        return GOAnnotationDB(output_path)
    return None


def load_go_annotations(db_path: str) -> GOAnnotationDB:
    """Load existing GO annotation database."""
    return GOAnnotationDB(db_path)

