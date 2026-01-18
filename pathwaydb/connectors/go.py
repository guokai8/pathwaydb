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

