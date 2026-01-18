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

    @classmethod
    def from_cache(cls, species: str = 'human', cache_dir: Optional[str] = None):
        """
        Create GO instance using centralized cache.

        This loads GO annotations from the cache directory (~/.pathwaydb_cache/go_annotations/).
        If the cache doesn't exist, it will be downloaded automatically.

        Args:
            species: Species name ('human', 'mouse', 'rat')
            cache_dir: Optional HTTP cache directory

        Returns:
            GO instance connected to the cached database

        Example:
            # Load from cache (auto-downloads if not cached)
            go = GO.from_cache(species='human')

            # Query directly from cache
            annotations = go.filter(gene_symbols=['TP53'])
            print(f"Found {len(annotations)} TP53 annotations")
        """
        from ..storage.go_db import get_cache_path, download_to_cache
        from pathlib import Path

        cache_path = get_cache_path(species)

        # Download if cache doesn't exist
        if not Path(cache_path).exists():
            print(f"Cache not found for {species}. Downloading...")
            download_to_cache(species=species, fetch_term_names=True)

        # Create GO instance with cache as storage
        instance = cls(cache_dir=cache_dir, storage_path=cache_path)
        print(f"✓ Loaded GO annotations for {species} from cache")
        return instance

    @classmethod
    def from_package_data(cls, species: str = 'human', cache_dir: Optional[str] = None):
        """
        Create GO instance using bundled package data.

        This loads GO annotations that are bundled with the PathwayDB package.
        No downloads required! If data is not bundled for the species, raises an error.

        Args:
            species: Species name ('human', 'mouse', 'rat')
            cache_dir: Optional HTTP cache directory

        Returns:
            GO instance connected to bundled database

        Raises:
            FileNotFoundError: If data is not bundled for the species

        Example:
            # Load from bundled data (instant, no download)
            go = GO.from_package_data(species='human')

            # Query directly
            annotations = go.filter(gene_symbols=['TP53'])
        """
        from ..data import get_go_data_path, has_go_data

        if not has_go_data(species):
            raise FileNotFoundError(
                f"GO annotations for {species} are not bundled with this package. "
                f"Use GO.from_cache('{species}') to download, or "
                f"use GO() with storage_path to specify a custom database."
            )

        data_path = get_go_data_path(species)
        instance = cls(cache_dir=cache_dir, storage_path=str(data_path))
        print(f"✓ Loaded GO annotations for {species} from package data")
        return instance

    @classmethod
    def load(cls, species: str = 'human', cache_dir: Optional[str] = None, use_package_data: bool = True):
        """
        Load GO annotations with automatic source detection.

        This method checks for GO data in the following order:
        1. Package data (if use_package_data=True and data is bundled)
        2. User cache (~/.pathwaydb_cache/go_annotations/)
        3. Download if not found

        Args:
            species: Species name ('human', 'mouse', 'rat')
            cache_dir: Optional HTTP cache directory
            use_package_data: If True, prefer bundled package data (default: True)

        Returns:
            GO instance connected to available database

        Example:
            # Automatically uses best available source
            go = GO.load(species='human')
            # Will use: bundled data > cache > download

            # Skip package data, use cache only
            go = GO.load(species='human', use_package_data=False)
        """
        from ..data import has_go_data

        # Try package data first (if enabled)
        if use_package_data and has_go_data(species):
            return cls.from_package_data(species=species, cache_dir=cache_dir)

        # Fall back to cache (downloads if needed)
        return cls.from_cache(species=species, cache_dir=cache_dir)
    
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
        evidence_codes: Optional[List[str]] = None,
        fetch_term_names: bool = True
    ) -> GOAnnotationDB:
        """
        Download and store GO annotations.

        Args:
            species: Species name ('human', 'mouse', etc.)
            evidence_codes: Optional list of evidence codes to filter by
            fetch_term_names: If True, automatically fetch term names from QuickGO API
                             (default: True). Set to False to skip this step and
                             fetch term names later with populate_term_names()

        Returns:
            GOAnnotationDB instance

        Example:
            >>> go = GO(storage_path='go_human.db')
            >>> go.download_annotations(species='human')  # Includes term names
            >>> # Term names are now available in all queries
            >>> results = go.filter(gene_symbols=['BRCA1'])
            >>> print(results[0].term_name)  # Will show the term name
        """
        if not self.storage:
            raise ValueError("No storage_path configured")

        print(f"Downloading GO annotations for {species}...")
        download_go_annotations_filtered(
            species=species,
            evidence_codes=evidence_codes,
            output_path=self.storage.db_path,
            return_db=False
        )

        # Automatically fetch term names unless user opts out
        if fetch_term_names:
            print("\nFetching GO term names from QuickGO API...")
            print("(This takes a few minutes but only needs to be done once)")
            self.populate_term_names()
            print("✓ Term names populated successfully!")

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
        namespace: Optional[str] = None,
        term_name: Optional[str] = None
    ):
        """
        Filter GO annotations by various criteria.

        Args:
            gene_symbols: Filter by gene symbols
            go_ids: Filter by GO term IDs
            evidence_codes: Filter by evidence codes
            aspect: Filter by aspect code (P/F/C)
            namespace: Filter by namespace (biological_process/molecular_function/cellular_component)
            term_name: Filter by term name (case-insensitive substring match)

        Note: 'namespace' is an alias for 'aspect' for user convenience.

        Example:
            >>> go = GO(storage_path='go_human.db')
            >>> # Find DNA repair terms
            >>> dna_repair = go.filter(term_name='DNA repair')
            >>> # Find TP53 apoptosis annotations
            >>> tp53_apoptosis = go.filter(gene_symbols=['TP53'], term_name='apoptosis')
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
            aspect=aspect,
            term_name=term_name
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

    def populate_term_names(self):
        """
        Fetch and populate GO term names from QuickGO API.

        This method downloads term names for all unique GO IDs in the database.
        Term names enable filtering by description instead of just GO IDs.

        Example:
            >>> go = GO(storage_path='go_human.db')
            >>> go.download_annotations(species='human')
            >>> go.populate_term_names()  # Fetch term names
            >>> # Now you can filter by term name
            >>> dna_repair = go.filter(term_name='DNA repair')
        """
        if not self.storage:
            raise ValueError("No storage configured. Set storage_path in __init__")

        return self.storage.populate_term_names()

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

