"""SQLite-backed annotation storage with DataFrame-like interface."""
import sqlite3
from typing import List, Optional, Dict, Union
from dataclasses import asdict
from ..core.models import Annotation
from ..core.exceptions import StorageError


class AnnotationDB:
    """
    Generic annotation database with query interface.
    
    Supports both KEGG and GO annotations with unified schema.
    """
    
    def __init__(self, db_path: str, create: bool = True):
        """
        Args:
            db_path: Path to SQLite database
            create: Create tables if they don't exist
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        if create:
            self._create_tables()
    
    def _create_tables(self):
        """Create annotation tables with indexes."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS annotations (
                gene_id TEXT NOT NULL,
                gene_symbol TEXT,
                term_id TEXT NOT NULL,
                evidence_code TEXT,
                aspect TEXT,
                species TEXT,
                source TEXT,
                PRIMARY KEY (gene_id, term_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_gene_id ON annotations(gene_id);
            CREATE INDEX IF NOT EXISTS idx_gene_symbol ON annotations(gene_symbol);
            CREATE INDEX IF NOT EXISTS idx_term_id ON annotations(term_id);
            CREATE INDEX IF NOT EXISTS idx_evidence ON annotations(evidence_code);
            CREATE INDEX IF NOT EXISTS idx_aspect ON annotations(aspect);
            CREATE INDEX IF NOT EXISTS idx_species ON annotations(species);
            CREATE INDEX IF NOT EXISTS idx_source ON annotations(source);
            
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        self.conn.commit()
    
    def insert_batch(self, annotations: List[Annotation], source: str = 'unknown'):
        """
        Batch insert annotations.
        
        Args:
            annotations: List of Annotation objects
            source: Data source ('kegg', 'go', etc.)
        """
        try:
            cursor = self.conn.cursor()
            for ann in annotations:
                cursor.execute("""
                    INSERT OR REPLACE INTO annotations 
                    (gene_id, gene_symbol, term_id, evidence_code, aspect, species, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    ann.gene_id,
                    ann.gene_symbol,
                    ann.term_id,
                    ann.evidence_code,
                    ann.aspect,
                    ann.species,
                    source
                ))
            
            self.conn.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to insert annotations: {e}")
    
    def query_by_gene(
        self, 
        gene_ids: List[str], 
        id_type: str = 'symbol',
        source: Optional[str] = None
    ) -> List[Annotation]:
        """Query annotations by gene identifiers."""
        column = 'gene_symbol' if id_type == 'symbol' else 'gene_id'
        placeholders = ','.join('?' * len(gene_ids))
        
        query = f"""
            SELECT * FROM annotations
            WHERE {column} IN ({placeholders})
        """
        params = list(gene_ids)
        
        if source:
            query += " AND source = ?"
            params.append(source)
        
        cursor = self.conn.execute(query, params)
        return [self._row_to_annotation(row) for row in cursor.fetchall()]
    
    def query_by_term(
        self, 
        term_ids: Union[str, List[str]],
        source: Optional[str] = None
    ) -> List[Annotation]:
        """Query genes annotated with specific terms."""
        if isinstance(term_ids, str):
            term_ids = [term_ids]
        
        placeholders = ','.join('?' * len(term_ids))
        query = f"""
            SELECT * FROM annotations
            WHERE term_id IN ({placeholders})
        """
        params = list(term_ids)
        
        if source:
            query += " AND source = ?"
            params.append(source)
        
        cursor = self.conn.execute(query, params)
        return [self._row_to_annotation(row) for row in cursor.fetchall()]
    
    def filter(
        self,
        gene_ids: Optional[List[str]] = None,
        gene_symbols: Optional[List[str]] = None,
        term_ids: Optional[List[str]] = None,
        evidence_codes: Optional[List[str]] = None,
        aspect: Optional[str] = None,
        species: Optional[str] = None,
        source: Optional[str] = None
    ) -> List[Annotation]:
        """Flexible multi-criteria filtering."""
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
        
        if term_ids:
            placeholders = ','.join('?' * len(term_ids))
            conditions.append(f"term_id IN ({placeholders})")
            params.extend(term_ids)
        
        if evidence_codes:
            placeholders = ','.join('?' * len(evidence_codes))
            conditions.append(f"evidence_code IN ({placeholders})")
            params.extend(evidence_codes)
        
        if aspect:
            conditions.append("aspect = ?")
            params.append(aspect)
        
        if species:
            conditions.append("species = ?")
            params.append(species)
        
        if source:
            conditions.append("source = ?")
            params.append(source)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM annotations WHERE {where_clause}"
        
        cursor = self.conn.execute(query, params)
        return [self._row_to_annotation(row) for row in cursor.fetchall()]
    
    def to_records(self, limit: Optional[int] = None, source: Optional[str] = None) -> List[Dict]:
        """Export as list of dictionaries."""
        query = "SELECT * FROM annotations"
        params = []
        
        if source:
            query += " WHERE source = ?"
            params.append(source)
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def to_dict(self, limit: Optional[int] = None, source: Optional[str] = None) -> Dict[str, List]:
        """Export as dictionary of lists."""
        records = self.to_records(limit=limit, source=source)
        
        if not records:
            return {}
        
        result = {key: [] for key in records[0].keys()}
        for record in records:
            for key in result:
                result[key].append(record[key])
        
        return result
    
    def to_gene_sets(self, source: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Convert to gene sets format for enrichment analysis.
        
        Returns:
            {term_id: [gene_symbols]}
        """
        query = """
            SELECT term_id, GROUP_CONCAT(gene_symbol) as genes
            FROM annotations
        """
        params = []
        
        if source:
            query += " WHERE source = ?"
            params.append(source)
        
        query += " GROUP BY term_id"
        
        cursor = self.conn.execute(query, params)
        result = {}
        for row in cursor.fetchall():
            if row['genes']:
                result[row['term_id']] = row['genes'].split(',')
        
        return result
    
    def stats(self, source: Optional[str] = None) -> Dict[str, int]:
        """Get database statistics."""
        query = """
            SELECT 
                COUNT(*) as total_annotations,
                COUNT(DISTINCT gene_id) as unique_genes,
                COUNT(DISTINCT gene_symbol) as unique_symbols,
                COUNT(DISTINCT term_id) as unique_terms,
                COUNT(DISTINCT evidence_code) as unique_evidence_codes
            FROM annotations
        """
        params = []
        
        if source:
            query += " WHERE source = ?"
            params.append(source)
        
        cursor = self.conn.execute(query, params)
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
    
    def _row_to_annotation(self, row: sqlite3.Row) -> Annotation:
        """Convert SQLite row to Annotation object."""
        return Annotation(
            gene_id=row['gene_id'],
            gene_symbol=row['gene_symbol'],
            term_id=row['term_id'],
            evidence_code=row['evidence_code'],
            aspect=row['aspect'],
            species=row['species']
        )
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

