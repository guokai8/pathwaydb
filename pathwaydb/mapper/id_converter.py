"""Gene ID conversion using MyGene.info API (stdlib only)."""
import json
import sqlite3
from typing import List, Dict, Optional
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from pathlib import Path
from ..core.exceptions import NetworkError


class IDConverter:
    """
    Gene ID converter with caching.
    
    Supports conversion between:
    - Entrez ID (NCBI)
    - Gene Symbol
    - Ensembl ID
    - UniProt ID
    
    Uses MyGene.info API with local SQLite cache.
    """
    
    def __init__(
        self, 
        species: str = 'human',
        cache_path: Optional[str] = None
    ):
        """
        Args:
            species: Species name ('human', 'mouse', etc.)
            cache_path: Path to SQLite cache database
        """
        self.species = species
        self.taxid = self._get_taxid(species)
        
        # Setup cache
        if cache_path is None:
            cache_path = f'.pathwaydb_cache/id_mapping_{species}.db'
        
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_cache()
    
    def _get_taxid(self, species: str) -> str:
        """Get NCBI taxonomy ID for species."""
        taxid_map = {
            'human': '9606',
            'mouse': '10090',
            'rat': '10116',
            'zebrafish': '7955',
            'fly': '7227',
            'worm': '6239',
            'yeast': '4932',
        }
        return taxid_map.get(species.lower(), '9606')
    
    def _init_cache(self):
        """Initialize SQLite cache database."""
        conn = sqlite3.connect(str(self.cache_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS id_mappings (
                input_id TEXT,
                input_type TEXT,
                output_id TEXT,
                output_type TEXT,
                PRIMARY KEY (input_id, input_type, output_type)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_input ON id_mappings(input_id, input_type)")
        conn.commit()
        conn.close()
    
    def _get_from_cache(
        self, 
        ids: List[str], 
        from_type: str, 
        to_type: str
    ) -> Dict[str, Optional[str]]:
        """Get mappings from cache."""
        conn = sqlite3.connect(str(self.cache_path))
        result = {}
        
        for id_val in ids:
            cursor = conn.execute(
                "SELECT output_id FROM id_mappings WHERE input_id = ? AND input_type = ? AND output_type = ?",
                (str(id_val), from_type, to_type)
            )
            row = cursor.fetchone()
            result[str(id_val)] = row[0] if row else None
        
        conn.close()
        return result
    
    def _save_to_cache(
        self, 
        mappings: Dict[str, Optional[str]], 
        from_type: str, 
        to_type: str
    ):
        """Save mappings to cache."""
        conn = sqlite3.connect(str(self.cache_path))
        
        for input_id, output_id in mappings.items():
            if output_id:
                conn.execute(
                    "INSERT OR REPLACE INTO id_mappings VALUES (?, ?, ?, ?)",
                    (str(input_id), from_type, str(output_id), to_type)
                )
        
        conn.commit()
        conn.close()
    
    def convert(
        self,
        ids: List[str],
        from_type: str = 'entrezgene',
        to_type: str = 'symbol',
        use_cache: bool = True
    ) -> Dict[str, Optional[str]]:
        """
        Convert gene IDs from one type to another.
        
        Args:
            ids: List of input IDs
            from_type: Input ID type ('entrezgene', 'symbol', 'ensembl.gene', 'uniprot')
            to_type: Output ID type ('entrezgene', 'symbol', 'ensembl.gene', 'uniprot')
            use_cache: Use cached results
        
        Returns:
            Dictionary mapping input IDs to output IDs
        
        Example:
            converter = IDConverter(species='human')
            result = converter.convert(['7157', '672'], from_type='entrezgene', to_type='symbol')
            # Returns: {'7157': 'TP53', '672': 'BRCA1'}
        """
        if not ids:
            return {}
        
        # Normalize input
        ids = [str(id_val).strip() for id_val in ids]
        
        # Check cache
        result = {}
        uncached_ids = []
        
        if use_cache:
            cached = self._get_from_cache(ids, from_type, to_type)
            result.update(cached)
            uncached_ids = [id_val for id_val in ids if cached.get(id_val) is None]
        else:
            uncached_ids = ids
        
        # Query API for uncached IDs
        if uncached_ids:
            api_result = self._query_mygene_batch(uncached_ids, from_type, to_type)
            result.update(api_result)
            
            # Save to cache
            if use_cache:
                self._save_to_cache(api_result, from_type, to_type)
        
        return result
    
    def _query_mygene_batch(
        self, 
        ids: List[str], 
        from_type: str, 
        to_type: str
    ) -> Dict[str, Optional[str]]:
        """Query MyGene.info API using batch POST endpoint."""
        # Map field names
        field_map = {
            'entrezgene': 'entrezgene',
            'symbol': 'symbol',
            'ensembl': 'ensembl.gene',
            'ensembl.gene': 'ensembl.gene',
            'uniprot': 'uniprot.Swiss-Prot',
        }
        
        output_field = field_map.get(to_type, to_type)
        
        # Use gene annotation endpoint for batch queries
        url = "https://mygene.info/v3/gene"
        
        result = {}
        batch_size = 100
        
        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]
            
            # Prepare POST data
            params = {
                'ids': ','.join(batch),
                'fields': output_field,
                'species': self.taxid
            }
            
            data = urlencode(params).encode('utf-8')
            
            try:
                request = Request(
                    url,
                    data=data,
                    headers={
                        'User-Agent': 'pathwaydb/1.0',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    method='POST'
                )
                
                with urlopen(request, timeout=30) as response:
                    response_data = json.loads(response.read().decode('utf-8'))
                
                # Parse results
                # Response is a list of gene objects
                for gene_obj in response_data:
                    # Get the query/input ID
                    query_id = gene_obj.get('query', '')
                    
                    # Get the output field value
                    output_val = None
                    if output_field in gene_obj:
                        value = gene_obj[output_field]
                        if isinstance(value, list):
                            output_val = str(value[0]) if value else None
                        elif isinstance(value, (str, int)):
                            output_val = str(value)
                    
                    if query_id:
                        result[str(query_id)] = output_val
            
            except Exception as e:
                print(f"Warning: MyGene.info batch query failed: {e}")
                # Mark as unmapped
                for id_val in batch:
                    if id_val not in result:
                        result[id_val] = None
        
        # Fill in unmapped IDs
        for id_val in ids:
            if id_val not in result:
                result[id_val] = None
        
        return result
    
    def convert_dataframe_dict(
        self,
        data: Dict[str, List],
        id_column: str,
        from_type: str = 'entrezgene',
        to_type: str = 'symbol',
        new_column: str = 'gene_symbol'
    ) -> Dict[str, List]:
        """
        Convert IDs in a dict-of-lists (DataFrame-like) structure.
        
        Args:
            data: Dictionary of lists
            id_column: Column name containing IDs to convert
            from_type: Input ID type
            to_type: Output ID type
            new_column: Name for new column with converted IDs
        
        Returns:
            Updated dictionary with new column
        
        Example:
            data = {'gene_id': ['hsa:7157', 'hsa:672'], 'pathway': ['p53', 'BRCA']}
            converter = IDConverter()
            data = converter.convert_dataframe_dict(
                data, 
                id_column='gene_id',
                from_type='entrezgene',
                to_type='symbol',
                new_column='gene_symbol'
            )
        """
        if id_column not in data:
            raise ValueError(f"Column '{id_column}' not found in data")
        
        # Extract IDs and clean KEGG format (remove 'hsa:' prefix)
        raw_ids = data[id_column]
        clean_ids = [str(id_val).split(':')[-1] if ':' in str(id_val) else str(id_val) 
                     for id_val in raw_ids]
        
        # Convert
        mapping = self.convert(clean_ids, from_type=from_type, to_type=to_type)
        
        # Add new column
        data[new_column] = [mapping.get(id_val, id_val) for id_val in clean_ids]
        
        return data


def bulk_convert_entrez_to_symbol(
    entrez_ids: List[str],
    species: str = 'human'
) -> Dict[str, str]:
    """
    Convenience function for quick Entrez to Symbol conversion.
    
    Args:
        entrez_ids: List of Entrez gene IDs
        species: Species name
    
    Returns:
        Dictionary mapping Entrez IDs to gene symbols
    
    Example:
        from pathwaydb.mapper import bulk_convert_entrez_to_symbol
        symbols = bulk_convert_entrez_to_symbol(['7157', '672'])
        # Returns: {'7157': 'TP53', '672': 'BRCA1'}
    """
    converter = IDConverter(species=species)
    result = converter.convert(entrez_ids, from_type='entrezgene', to_type='symbol')
    # Filter out None values
    return {k: v for k, v in result.items() if v is not None}

