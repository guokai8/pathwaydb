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
    
    def filter(
        self,
        gene_symbols: Optional[List[str]] = None,
        gene_set_name: Optional[str] = None,
        description: Optional[str] = None,
        collection: Optional[str] = None,
        organism: Optional[str] = None
    ) -> List[MSigDBRecord]:
        """
        Filter gene sets by multiple criteria.

        Args:
            gene_symbols: List of gene symbols (returns sets containing ANY of these genes)
            gene_set_name: Gene set name substring (case-insensitive)
            description: Description substring (case-insensitive)
            collection: Collection code (H, C1, C2, etc.)
            organism: Organism name (human, mouse)

        Returns:
            List of matching MSigDBRecord objects

        Example:
            # Find Hallmark apoptosis gene sets
            results = db.filter(gene_set_name='apoptosis', collection='H')

            # Find gene sets containing TP53
            results = db.filter(gene_symbols=['TP53'])

            # Complex query
            results = db.filter(
                gene_symbols=['TP53', 'MYC'],
                collection='C2',
                description='cancer'
            )
        """
        # If filtering by genes, use gene_geneset_map table
        if gene_symbols:
            placeholders = ','.join('?' * len(gene_symbols))
            query = f"""
                SELECT DISTINCT gs.*
                FROM gene_sets gs
                JOIN gene_geneset_map gm ON gs.gene_set_id = gm.gene_set_id
                WHERE gm.gene_symbol IN ({placeholders})
            """
            params = list(gene_symbols)
        else:
            query = "SELECT * FROM gene_sets WHERE 1=1"
            params = []

        # Add other filters
        if gene_set_name:
            query += " AND gene_set_name LIKE ? COLLATE NOCASE"
            params.append(f"%{gene_set_name}%")

        if description:
            query += " AND description LIKE ? COLLATE NOCASE"
            params.append(f"%{description}%")

        if collection:
            query += " AND collection = ?"
            params.append(collection)

        if organism:
            query += " AND organism = ?"
            params.append(organism)

        query += " ORDER BY gene_set_name"

        cursor = self.conn.execute(query, params)

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

    def to_dataframe(self, collection: Optional[str] = None) -> List[Dict]:
        """
        Export gene sets in DataFrame-compatible format for enrichment analysis.

        Format: Each row is a gene-to-geneset mapping
        Columns: GeneID, GeneSet, Collection, Description

        Args:
            collection: Optional collection filter (H, C1, C2, etc.)

        Returns:
            List of dicts with keys: GeneID, GeneSet, Collection, Description

        Example:
            import pandas as pd

            db = MSigDBAnnotationDB('msigdb.db')
            data = db.to_dataframe(collection='H')
            df = pd.DataFrame(data)

            # Use for enrichment analysis
            print(df.head())
            #   GeneID              GeneSet Collection  Description
            # 0   ABCA1  HALLMARK_ADIPOGENESIS          H  Genes up-regulated...
            # 1   ABCB8  HALLMARK_ADIPOGENESIS          H  Genes up-regulated...
        """
        # Build query to join gene_geneset_map with gene_sets
        query = """
            SELECT
                gm.gene_symbol,
                gs.gene_set_name,
                gs.collection,
                gs.description
            FROM gene_geneset_map gm
            JOIN gene_sets gs ON gm.gene_set_id = gs.gene_set_id
        """
        params = []

        if collection:
            query += " WHERE gs.collection = ?"
            params.append(collection)

        query += " ORDER BY gs.gene_set_name, gm.gene_symbol"

        cursor = self.conn.execute(query, params)

        results = []
        for row in cursor.fetchall():
            results.append({
                'GeneID': row[0],
                'GeneSet': row[1],
                'Collection': row[2],
                'Description': row[3]
            })

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

    def stats(self) -> Dict:
        """Get database statistics."""
        cursor = self.conn.execute("""
            SELECT
                COUNT(*) as total_gene_sets,
                COUNT(DISTINCT collection) as total_collections,
                COUNT(DISTINCT organism) as organisms
            FROM gene_sets
        """)
        row = cursor.fetchone()

        stats = {
            'total_gene_sets': row['total_gene_sets'],
            'total_collections': row['total_collections'],
            'organisms': row['organisms']
        }

        # Collection breakdown
        cursor = self.conn.execute("""
            SELECT collection, COUNT(*) as count
            FROM gene_sets
            GROUP BY collection
            ORDER BY collection
        """)

        stats['by_collection'] = {row['collection']: row['count'] for row in cursor.fetchall()}

        return stats

    def close(self):
        """Close database connection."""
        self.conn.close()

