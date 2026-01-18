"""Gene Ontology client."""
import json
from typing import List, Optional, Dict
from ..core.models import Term
from ..core.constants import GO_API_URL, GO_QUICKGO_URL, DEFAULT_RATE_LIMIT
from ..core.exceptions import NotFoundError
from ..http.client import HTTPClient
from ..storage.go_db import GOAnnotationDB, download_go_annotations_filtered


class GO:
    """Gene Ontology client with dedicated storage."""
    
    def __init__(
        self, 
        cache_dir: Optional[str] = None,
        storage_path: Optional[str] = None
    ):
        self.base_url = GO_API_URL
        self.client = HTTPClient(cache_dir=cache_dir, rate_limit=DEFAULT_RATE_LIMIT)
        self.storage = GOAnnotationDB(storage_path) if storage_path else None
    
    def get_term(self, term_id: str) -> Term:
        """Get GO term details."""
        url = f"{self.base_url}/bioentity/term/{term_id}"
        
        try:
            response = self.client.get(url)
            data = json.loads(response)
        except Exception as e:
            raise NotFoundError(f"GO term {term_id} not found: {e}")
        
        return self._parse_term(data)
    
    def download_annotations(
        self,
        species: str = 'human',
        evidence_codes: Optional[List[str]] = None
    ) -> GOAnnotationDB:
        """Download and store GO annotations."""
        if not self.storage:
            raise ValueError("No storage_path configured")
        
        download_go_annotations_filtered(
            species=species,
            evidence_codes=evidence_codes,
            output_path=self.storage.db_path,
            return_db=False
        )
        
        return self.storage
    
    def query_by_gene(self, gene: str, id_type: str = 'symbol'):
        """
        Query GO terms for a specific gene.

        Args:
            gene: Gene identifier (symbol or ID)
            id_type: 'symbol' or 'id' (default: 'symbol')

        Returns:
            List of GO annotation records

        Example:
            >>> go = GO(species='human', storage_path='go_human.db')
            >>> results = go.query_by_gene('BRCA1')
            >>> print(f"BRCA1 has {len(results)} GO annotations")
        """
        if not self.storage:
            raise ValueError("No storage configured. Set storage_path in __init__")

        return self.storage.query_by_gene([gene], id_type=id_type)

    def query_annotations(
        self,
        gene_symbols: Optional[List[str]] = None,
        go_ids: Optional[List[str]] = None,
        evidence_codes: Optional[List[str]] = None,
        aspect: Optional[str] = None
    ):
        """Query stored annotations."""
        if not self.storage:
            raise ValueError("No storage configured")

        return self.storage.filter(
            gene_symbols=gene_symbols,
            go_ids=go_ids,
            evidence_codes=evidence_codes,
            aspect=aspect
        )

    def filter(
        self,
        gene_symbols: Optional[List[str]] = None,
        go_ids: Optional[List[str]] = None,
        evidence_codes: Optional[List[str]] = None,
        aspect: Optional[str] = None,
        namespace: Optional[str] = None
    ):
        """
        Filter GO annotations by various criteria.

        Note: 'namespace' is an alias for 'aspect' for user convenience.
        """
        if not self.storage:
            raise ValueError("No storage configured")

        # Map namespace to aspect if provided
        if namespace:
            aspect_map = {
                'biological_process': 'P',
                'molecular_function': 'F',
                'cellular_component': 'C'
            }
            aspect = aspect_map.get(namespace, namespace)

        return self.storage.filter(
            gene_symbols=gene_symbols,
            go_ids=go_ids,
            evidence_codes=evidence_codes,
            aspect=aspect
        )

    def to_dataframe(self, limit: Optional[int] = None):
        """
        Export annotations to DataFrame-compatible format.

        Args:
            limit: Optional limit on number of rows

        Returns:
            List of dicts with keys: GeneID, TERM, Aspect, Evidence

        Example:
            >>> go = GO(species='human', storage_path='go_human.db')
            >>> df_data = go.to_dataframe()
            >>> import pandas as pd
            >>> df = pd.DataFrame(df_data)
        """
        if not self.storage:
            raise ValueError("No storage configured. Set storage_path in __init__")

        return self.storage.to_dataframe(limit=limit)

    def stats(self):
        """Get database statistics."""
        if not self.storage:
            raise ValueError("No storage configured. Set storage_path in __init__")

        return self.storage.stats()

    def export_gene_sets(self) -> Dict[str, List[str]]:
        """Export as gene sets."""
        if not self.storage:
            raise ValueError("No storage configured")
        
        return self.storage.to_gene_sets()
    
    def _parse_term(self, data: dict) -> Term:
        """Parse GO term JSON."""
        return Term(
            id=data.get('id', ''),
            name=data.get('label', ''),
            namespace=data.get('namespace', ''),
            definition=data.get('definition', {}).get('val', '') if isinstance(data.get('definition'), dict) else '',
            is_obsolete=data.get('deprecated', False),
            parents=data.get('parents', []),
            children=data.get('children', [])
        )

