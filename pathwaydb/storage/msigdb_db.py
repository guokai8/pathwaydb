"""MSigDB storage with DataFrame-like interface."""
import sqlite3
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class MSigDBRecord:
    """Single MSigDB gene set record."""
    gene_set_id: str
    gene_set_name: str
    collection: str
    description: str
    genes: List[str]
    organism: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class MSigDBAnnotationDB:
    """
    MSigDB annotation database with DataFrame-like interface.
    
    Usage:
        db = MSigDBAnnotationDB('msigdb.db')
        
        # Query methods
        hallmark_sets = db.query_by_collection('H')
        apoptosis_sets = db.query_by_name('%APOPTOSIS%')
        
        # Export as records
        records = db.to_records(collection='H')
    """
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
    
    def query_by_collection(self, collection: str) -> List[MSigDBRecord]:
        """Query gene sets by collection."""
        cursor = self.conn.execute(
            "SELECT * FROM gene_sets WHERE collection = ?",
            (collection,)
        )
        
        results = []
        for row in cursor.fetchall():
            genes = row['genes'].split(',')
            results.append(MSigDBRecord(
                gene_set_id=row['gene_set_id'],
                gene_set_name=row['gene_set_name'],
                collection=row['collection'],
                description=row['description'],
                genes=genes,
                organism=row['organism']
            ))
        
        return results
    
    def query_by_name(self, name_pattern: str) -> List[MSigDBRecord]:
        """Query gene sets by name pattern."""
        cursor = self.conn.execute(
            "SELECT * FROM gene_sets WHERE gene_set_name LIKE ? COLLATE NOCASE",
            (name_pattern,)
        )
        
        results = []
        for row in cursor.fetchall():
            genes = row['genes'].split(',')
            results.append(MSigDBRecord(
                gene_set_id=row['gene_set_id'],
                gene_set_name=row['gene_set_name'],
                collection=row['collection'],
                description=row['description'],
                genes=genes,
                organism=row['organism']
            ))
        
        return results
    
    def to_records(
        self,
        collection: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Export as list of dictionaries."""
        query = "SELECT * FROM gene_sets"
        params = []
        
        if collection:
            query += " WHERE collection = ?"
            params.append(collection)
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result['genes'] = result['genes'].split(',')
            results.append(result)
        
        return results
    
    def close(self):
        """Close database connection."""
        self.conn.close()

