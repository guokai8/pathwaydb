"""MSigDB (Molecular Signatures Database) connector."""
import json
import sqlite3
from typing import List, Dict, Optional, Set
from urllib.request import urlopen, Request
from pathlib import Path
from ..core.models import Pathway
from ..core.constants import DEFAULT_RATE_LIMIT
from ..core.exceptions import NotFoundError, NetworkError
from ..http.client import HTTPClient


class MSigDB:
    """
    MSigDB (Molecular Signatures Database) client.
    
    Provides access to curated gene sets from:
    - Hallmark gene sets (H)
    - Curated gene sets (C1-C8)
    - GO gene sets (C5)
    - Oncogenic signatures (C6)
    - Immunologic signatures (C7)
    - Cell type signatures (C8)
    
    Features:
    - Download gene sets by collection
    - Store locally for fast access
    - Query by gene or gene set name
    - Export for enrichment analysis
    """
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        storage_path: Optional[str] = None
    ):
        """
        Args:
            cache_dir: HTTP cache directory
            storage_path: SQLite database path for storing gene sets
        """
        self.base_url = "https://www.gsea-msigdb.org/gsea/msigdb"
        self.client = HTTPClient(cache_dir=cache_dir, rate_limit=DEFAULT_RATE_LIMIT)
        
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path('.pathwaydb_cache') / 'msigdb.db'
        
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_storage()
    
    def _init_storage(self):
        """Initialize SQLite storage."""
        conn = sqlite3.connect(str(self.storage_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gene_sets (
                gene_set_id TEXT PRIMARY KEY,
                gene_set_name TEXT,
                collection TEXT,
                description TEXT,
                genes TEXT,
                organism TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_collection ON gene_sets(collection)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON gene_sets(gene_set_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_organism ON gene_sets(organism)")
        
        # Table for gene-to-geneset mapping
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gene_geneset_map (
                gene_symbol TEXT,
                gene_set_id TEXT,
                collection TEXT,
                PRIMARY KEY (gene_symbol, gene_set_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gene ON gene_geneset_map(gene_symbol)")
        
        conn.commit()
        conn.close()
    
    def download_collection(
        self,
        collection: str = 'H',
        species: str = 'human',
        force_refresh: bool = False
    ) -> int:
        """
        Download MSigDB gene set collection.
        
        Args:
            collection: Collection code:
                - 'H': Hallmark gene sets
                - 'C1': Positional gene sets
                - 'C2': Curated gene sets (includes KEGG, Reactome, BioCarta)
                - 'C3': Regulatory target gene sets
                - 'C4': Computational gene sets
                - 'C5': Ontology gene sets (GO)
                - 'C6': Oncogenic signature gene sets
                - 'C7': Immunologic signature gene sets
                - 'C8': Cell type signature gene sets
            species: 'human' or 'mouse'
            force_refresh: Re-download even if already cached
        
        Returns:
            Number of gene sets downloaded
        
        Example:
            msigdb = MSigDB(storage_path='msigdb.db')
            
            # Download Hallmark gene sets
            count = msigdb.download_collection('H')
            print(f"Downloaded {count} Hallmark gene sets")
            
            # Download KEGG/Reactome (C2)
            count = msigdb.download_collection('C2')
        """
        conn = sqlite3.connect(str(self.storage_path))
        
        # Check if already downloaded
        if not force_refresh:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM gene_sets WHERE collection = ? AND organism = ?",
                (collection, species)
            )
            existing_count = cursor.fetchone()[0]
            if existing_count > 0:
                print(f"Collection {collection} already downloaded ({existing_count} gene sets)")
                conn.close()
                return existing_count
        
        print(f"Downloading MSigDB collection {collection} for {species}...")
        
        # Download GMT file from MSigDB
        # Note: This uses the public GMT files from MSigDB
        species_code = 'Hs' if species == 'human' else 'Mm'
        
        # MSigDB provides collections as GMT files
        # Format: https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2024.1.Hs/
        version = "2024.1"
        gmt_url = f"https://data.broadinstitute.org/gsea-msigdb/msigdb/release/{version}.{species_code}/{collection.lower()}.all.v{version}.{species_code}.symbols.gmt"
        
        try:
            gene_sets = self._download_gmt(gmt_url)
        except Exception as e:
            conn.close()
            raise NetworkError(f"Failed to download MSigDB collection {collection}: {e}")
        
        # Store gene sets
        count = 0
        for gs in gene_sets:
            gene_set_id = gs['name']
            gene_set_name = gs['name']
            description = gs.get('description', '')
            genes = gs['genes']
            
            # Store gene set
            conn.execute(
                "INSERT OR REPLACE INTO gene_sets VALUES (?, ?, ?, ?, ?, ?)",
                (gene_set_id, gene_set_name, collection, description, ','.join(genes), species)
            )
            
            # Store gene-to-geneset mappings
            for gene in genes:
                conn.execute(
                    "INSERT OR IGNORE INTO gene_geneset_map VALUES (?, ?, ?)",
                    (gene, gene_set_id, collection)
                )
            
            count += 1
            if count % 100 == 0:
                conn.commit()
                print(f"  Processed {count} gene sets...")
        
        conn.commit()
        conn.close()
        
        print(f"✓ Downloaded {count} gene sets from collection {collection}")
        return count
    
    def _download_gmt(self, url: str) -> List[Dict]:
        """
        Download and parse GMT file.
        
        GMT format:
        GENESET_NAME    DESCRIPTION    GENE1    GENE2    GENE3    ...
        """
        gene_sets = []
        
        request = Request(url, headers={'User-Agent': 'pathwaydb/1.0'})
        
        with urlopen(request, timeout=300) as response:
            for line in response:
                line = line.decode('utf-8').strip()
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) < 3:
                    continue
                
                gene_set_name = parts[0]
                description = parts[1] if len(parts) > 1 else ''
                genes = [g.strip() for g in parts[2:] if g.strip()]
                
                gene_sets.append({
                    'name': gene_set_name,
                    'description': description,
                    'genes': genes
                })
        
        return gene_sets
    
    def query_by_gene(
        self,
        gene_symbols: List[str],
        collection: Optional[str] = None,
        min_overlap: int = 1
    ) -> List[Dict]:
        """
        Find gene sets containing specified genes.
        
        Args:
            gene_symbols: List of gene symbols
            collection: Filter by collection (e.g., 'H', 'C2')
            min_overlap: Minimum number of genes that must overlap
        
        Returns:
            List of gene sets with overlap information
        
        Example:
            results = msigdb.query_by_gene(['TP53', 'MYC', 'BRCA1'])
            for r in results[:5]:
                print(f"{r['gene_set_name']}: {r['overlap_count']} genes overlap")
        """
        conn = sqlite3.connect(str(self.storage_path))
        conn.row_factory = sqlite3.Row
        
        # Find gene sets containing these genes
        placeholders = ','.join('?' * len(gene_symbols))
        query = f"""
            SELECT 
                gene_set_id,
                collection,
                COUNT(*) as overlap_count
            FROM gene_geneset_map
            WHERE gene_symbol IN ({placeholders})
        """
        params = list(gene_symbols)
        
        if collection:
            query += " AND collection = ?"
            params.append(collection)
        
        query += " GROUP BY gene_set_id HAVING COUNT(*) >= ?"
        params.append(min_overlap)
        query += " ORDER BY overlap_count DESC"
        
        cursor = conn.execute(query, params)
        overlaps = cursor.fetchall()
        
        # Get full gene set details
        results = []
        for row in overlaps:
            gene_set_id = row['gene_set_id']
            overlap_count = row['overlap_count']
            
            cursor2 = conn.execute(
                "SELECT * FROM gene_sets WHERE gene_set_id = ?",
                (gene_set_id,)
            )
            gs_row = cursor2.fetchone()
            
            if gs_row:
                genes = gs_row['genes'].split(',')
                overlapping_genes = [g for g in gene_symbols if g in genes]
                
                results.append({
                    'gene_set_id': gs_row['gene_set_id'],
                    'gene_set_name': gs_row['gene_set_name'],
                    'collection': gs_row['collection'],
                    'description': gs_row['description'],
                    'total_genes': len(genes),
                    'overlap_count': overlap_count,
                    'overlapping_genes': overlapping_genes
                })
        
        conn.close()
        return results
    
    def query_by_name(
        self,
        name_pattern: str,
        collection: Optional[str] = None
    ) -> List[Dict]:
        """
        Search gene sets by name pattern.
        
        Args:
            name_pattern: Search pattern (case-insensitive, supports %)
            collection: Filter by collection
        
        Returns:
            List of matching gene sets
        
        Example:
            # Find all apoptosis-related gene sets
            results = msigdb.query_by_name('%APOPTOSIS%')
            
            # Find Hallmark gene sets about metabolism
            results = msigdb.query_by_name('%METABOL%', collection='H')
        """
        conn = sqlite3.connect(str(self.storage_path))
        conn.row_factory = sqlite3.Row
        
        query = """
            SELECT 
                gene_set_id,
                gene_set_name,
                collection,
                description,
                genes,
                organism
            FROM gene_sets
            WHERE gene_set_name LIKE ? COLLATE NOCASE
        """
        params = [name_pattern]
        
        if collection:
            query += " AND collection = ?"
            params.append(collection)
        
        query += " ORDER BY gene_set_name"
        
        cursor = conn.execute(query, params)
        results = []
        
        for row in cursor.fetchall():
            genes = row['genes'].split(',')
            results.append({
                'gene_set_id': row['gene_set_id'],
                'gene_set_name': row['gene_set_name'],
                'collection': row['collection'],
                'description': row['description'],
                'genes': genes,
                'total_genes': len(genes),
                'organism': row['organism']
            })
        
        conn.close()
        return results
    
    def get_gene_set(self, gene_set_id: str) -> Optional[Dict]:
        """
        Get full details of a gene set.
        
        Args:
            gene_set_id: Gene set identifier
        
        Returns:
            Gene set details or None if not found
        """
        conn = sqlite3.connect(str(self.storage_path))
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute(
            "SELECT * FROM gene_sets WHERE gene_set_id = ?",
            (gene_set_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        genes = row['genes'].split(',')
        result = {
            'gene_set_id': row['gene_set_id'],
            'gene_set_name': row['gene_set_name'],
            'collection': row['collection'],
            'description': row['description'],
            'genes': genes,
            'total_genes': len(genes),
            'organism': row['organism']
        }
        
        conn.close()
        return result
    
    def export_gene_sets(
        self,
        collection: Optional[str] = None,
        format: str = 'dict'
    ) -> Dict[str, List[str]]:
        """
        Export gene sets for enrichment analysis.
        
        Args:
            collection: Filter by collection (None = all)
            format: 'dict' or 'gmt'
        
        Returns:
            Dictionary mapping gene set IDs to gene lists
        
        Example:
            # Export Hallmark gene sets
            gene_sets = msigdb.export_gene_sets(collection='H')
            
            # Use for enrichment
            from scipy.stats import hypergeom
            # ... enrichment analysis
        """
        conn = sqlite3.connect(str(self.storage_path))
        
        query = "SELECT gene_set_id, genes FROM gene_sets"
        params = []
        
        if collection:
            query += " WHERE collection = ?"
            params.append(collection)
        
        cursor = conn.execute(query, params)
        
        if format == 'dict':
            result = {}
            for row in cursor.fetchall():
                gene_set_id = row[0]
                genes = row[1].split(',')
                result[gene_set_id] = genes
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        conn.close()
        return result

    def stats(self) -> Dict:
        """Get database statistics."""
        conn = sqlite3.connect(str(self.storage_path))
        conn.row_factory = sqlite3.Row  # Enable Row factory
    
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_gene_sets,
                COUNT(DISTINCT collection) as total_collections,
                COUNT(DISTINCT organism) as organisms
            FROM gene_sets
        """)
        row = cursor.fetchone()
    
    # Convert Row to dict properly
        stats = {
            'total_gene_sets': row['total_gene_sets'],
            'total_collections': row['total_collections'],
            'organisms': row['organisms']
        }
    
    # Collection breakdown
        cursor = conn.execute("""
            SELECT collection, COUNT(*) as count
            FROM gene_sets
            GROUP BY collection
            ORDER BY collection
        """)
    
        stats['by_collection'] = {row['collection']: row['count'] for row in cursor.fetchall()}
    
        conn.close()
        return stats    

