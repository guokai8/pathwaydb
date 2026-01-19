"""KEGG REST API client with local storage support."""
from typing import List, Dict, Optional
from ..core.models import Gene, Pathway
from ..core.constants import KEGG_BASE_URL, KEGG_RATE_LIMIT
from ..core.exceptions import NotFoundError
from ..http.client import HTTPClient
from ..storage.kegg_db import KEGGAnnotationDB, KEGGAnnotationRecord


class KEGG:
    """KEGG database client with DataFrame-like annotation storage."""
    
    def __init__(
        self, 
        species: str = 'hsa', 
        cache_dir: Optional[str] = None,
        storage_path: Optional[str] = None
    ):
        self.species = species
        self.base_url = KEGG_BASE_URL
        self.client = HTTPClient(cache_dir=cache_dir, rate_limit=KEGG_RATE_LIMIT)
        self.storage = KEGGAnnotationDB(storage_path) if storage_path else None
    
    def get_pathway(self, pathway_id: str) -> Pathway:
        """Get pathway details."""
        url = f"{self.base_url}/get/{pathway_id}"
        try:
            response = self.client.get(url)
        except Exception as e:
            raise NotFoundError(f"Pathway {pathway_id} not found: {e}")
        
        return self._parse_pathway(response, pathway_id)
    
    def list_pathways(self, organism: Optional[str] = None) -> List[Pathway]:
        """List all pathways for an organism."""
        org = organism or self.species
        url = f"{self.base_url}/list/pathway/{org}"
        
        response = self.client.get(url)
        pathways = []
        
        for line in response.strip().split('\n'):
            if not line:
                continue
            
            parts = line.split('\t')
            if len(parts) >= 2:
                pathway_id = parts[0].replace('path:', '')
                name = parts[1]
                pathways.append(Pathway(
                    id=pathway_id,
                    name=name,
                    species=org,
                    source='kegg'
                ))
        
        return pathways
    
    def get_pathway_genes(self, pathway_id: str) -> List[Gene]:
        """Get all genes in a pathway."""
        url = f"{self.base_url}/link/genes/{pathway_id}"
        response = self.client.get(url)
        
        genes = []
        for line in response.strip().split('\n'):
            if not line:
                continue
            
            parts = line.split('\t')
            if len(parts) == 2:
                gene_id = parts[1]
                symbol = gene_id.split(':')[1] if ':' in gene_id else gene_id
                genes.append(Gene(
                    id=gene_id,
                    symbol=symbol,
                    species=self.species,
                    source='kegg'
                ))
        
        return genes
    
    def download_annotations(self, organism: Optional[str] = None) -> KEGGAnnotationDB:
        """
        Download and store KEGG annotations.
        
        Args:
            organism: KEGG organism code (default: uses self.species)
        
        Returns:
            KEGGAnnotationDB instance for querying
        """
        if not self.storage:
            raise ValueError("No storage_path configured. Set storage_path in __init__")
        
        org = organism or self.species
        
        print(f"Downloading KEGG pathway annotations for {org}...")
        
        # Get pathway names first
        pathway_names = {}
        try:
            pathways = self.list_pathways(organism=org)
            for pw in pathways:
                pathway_names[pw.id] = pw.name
        except Exception as e:
            print(f"Warning: Could not fetch pathway names: {e}")
        
        # Get pathway-gene links
        url = f"{self.base_url}/link/pathway/{org}"
        response = self.client.get(url)
        
        # Parse and store annotations
        annotations = []
        for line in response.strip().split('\n'):
            if not line:
                continue
            
            parts = line.split('\t')
            if len(parts) != 2:
                continue
            
            gene_id = parts[0]
            pathway_id = parts[1].replace('path:', '')
            gene_symbol = gene_id.split(':')[1] if ':' in gene_id else gene_id
            
            annotations.append(KEGGAnnotationRecord(
                gene_id=gene_id,
                gene_symbol=gene_symbol,
                pathway_id=pathway_id,
                pathway_name=pathway_names.get(pathway_id),
                organism=org
            ))
        
        print(f"✓ Downloaded {len(annotations)} pathway-gene annotations")
        
        # Store in database
        self.storage.insert_batch(annotations)
        self.storage.set_metadata('kegg_organism', org)
        print(f"✓ Stored annotations in {self.storage.db_path}")
        
        return self.storage
    
    def convert_ids_to_symbols(self):
        """Convert Entrez IDs to gene symbols using MyGene.info."""
        if not self.storage:
            raise ValueError("No storage configured. Set storage_path in __init__")
        
        from ..mapper.id_converter import IDConverter
        
        species_map = {
            'hsa': 'human',
            'mmu': 'mouse',
            'rno': 'rat',
            'dre': 'zebrafish',
            'dme': 'fly',
            'cel': 'worm',
            'sce': 'yeast'
        }
        species_name = species_map.get(self.species, 'human')
        
        print("Fetching Entrez IDs from database...")
        cursor = self.storage.conn.execute(
            "SELECT DISTINCT gene_symbol FROM kegg_annotations"
        )
        entrez_ids = [row[0] for row in cursor.fetchall()]
        
        print(f"Converting {len(entrez_ids)} Entrez IDs to gene symbols...")
        print("(First run ~2-3 min, subsequent runs ~10 sec via cache)")
        
        converter = IDConverter(species=species_name)
        mapping = converter.convert(entrez_ids, from_type='entrezgene', to_type='symbol')
        
        print("\nUpdating database...")
        converted_count = 0
        
        for entrez_id, symbol in mapping.items():
            if symbol and symbol != entrez_id:
                self.storage.conn.execute(
                    "UPDATE kegg_annotations SET gene_symbol = ? WHERE gene_symbol = ?",
                    (symbol, entrez_id)
                )
                converted_count += 1
        
        self.storage.conn.commit()
        print(f"✓ Converted {converted_count} Entrez IDs to gene symbols")
        
        return self.storage
    
    def query_by_gene(self, gene: str, id_type: str = 'symbol'):
        """
        Query pathways for a specific gene.

        Args:
            gene: Gene identifier (symbol or ID)
            id_type: 'symbol' or 'id' (default: 'symbol')

        Returns:
            List of pathway annotation records

        Example:
            >>> kegg = KEGG(species='hsa', storage_path='kegg_human.db')
            >>> results = kegg.query_by_gene('TP53')
            >>> print(f"TP53 is in {len(results)} pathways")
        """
        if not self.storage:
            raise ValueError("No storage configured. Set storage_path in __init__")

        return self.storage.query_by_gene([gene], id_type=id_type)

    def filter(
        self,
        gene_symbols: Optional[List[str]] = None,
        gene_ids: Optional[List[str]] = None,
        pathway_ids: Optional[List[str]] = None,
        pathway_name: Optional[str] = None,
        organism: Optional[str] = None
    ):
        """
        Filter annotations by multiple criteria.

        Args:
            gene_symbols: Filter by gene symbols (e.g., ['TP53', 'BRCA1'])
            gene_ids: Filter by gene IDs (e.g., ['hsa:7157'])
            pathway_ids: Filter by pathway IDs (e.g., ['hsa04110'])
            pathway_name: Filter by pathway name (case-insensitive substring match)
            organism: Filter by organism code (e.g., 'hsa')

        Returns:
            List of KEGGAnnotationRecord objects

        Example:
            >>> kegg = KEGG(species='hsa', storage_path='kegg_human.db')
            >>> # Filter by pathway name
            >>> cancer_pathways = kegg.filter(pathway_name='cancer')
            >>> # Combine filters
            >>> tp53_cancer = kegg.filter(gene_symbols=['TP53'], pathway_name='cancer')
        """
        if not self.storage:
            raise ValueError("No storage configured. Set storage_path in __init__")

        return self.storage.filter(
            gene_symbols=gene_symbols,
            gene_ids=gene_ids,
            pathway_ids=pathway_ids,
            pathway_name=pathway_name,
            organism=organism
        )

    def query_annotations(
        self,
        gene_symbols: Optional[List[str]] = None,
        gene_ids: Optional[List[str]] = None,
        pathway_ids: Optional[List[str]] = None
    ):
        """
        Query stored annotations (legacy method - use filter() instead).

        This method is kept for backwards compatibility.
        Use filter() for more options including pathway_name filtering.
        """
        if not self.storage:
            raise ValueError("No storage configured. Set storage_path in __init__")

        return self.storage.filter(
            gene_symbols=gene_symbols,
            gene_ids=gene_ids,
            pathway_ids=pathway_ids
        )

    def to_dataframe(self, limit: Optional[int] = None):
        """
        Export annotations to DataFrame-compatible format.

        Args:
            limit: Optional limit on number of rows

        Returns:
            List of dicts with keys: GeneID, PATH, Annot

        Example:
            >>> kegg = KEGG(species='hsa', storage_path='kegg_human.db')
            >>> df_data = kegg.to_dataframe()
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
        """Export stored annotations as gene sets for enrichment analysis."""
        if not self.storage:
            raise ValueError("No storage configured")
        
        return self.storage.to_gene_sets()
    
    def _parse_pathway(self, text: str, pathway_id: str) -> Pathway:
        """Parse KEGG pathway flat file format."""
        lines = text.split('\n')
        name = ""
        description = ""
        genes: List[str] = []
        
        in_gene_section = False
        
        for line in lines:
            line = line.rstrip()
            
            if line.startswith('NAME'):
                name = line.split(maxsplit=1)[1] if len(line.split(maxsplit=1)) > 1 else ""
            elif line.startswith('DESCRIPTION'):
                description = line.split(maxsplit=1)[1] if len(line.split(maxsplit=1)) > 1 else ""
            elif line.startswith('GENE'):
                in_gene_section = True
                parts = line.split(maxsplit=1)
                if len(parts) > 1:
                    gene_entry = parts[1].strip()
                    gene_id = gene_entry.split()[0] if gene_entry else ""
                    if gene_id:
                        genes.append(f"{self.species}:{gene_id}")
            elif in_gene_section and line.startswith(' '):
                gene_entry = line.strip()
                gene_id = gene_entry.split()[0] if gene_entry else ""
                if gene_id and not gene_id.startswith('///'):
                    genes.append(f"{self.species}:{gene_id}")
            elif in_gene_section and not line.startswith(' '):
                in_gene_section = False
        
        return Pathway(
            id=pathway_id,
            name=name,
            description=description,
            genes=genes,
            species=self.species,
            source='kegg'
        )

