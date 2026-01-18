"""pathwaydb: Pathway and Gene Set Database Toolkit."""

__version__ = "0.2.0"

from pathwaydb.connectors.kegg import KEGG
from pathwaydb.connectors.go import GO
from pathwaydb.connectors.msigdb import MSigDB
from pathwaydb.storage.kegg_db import KEGGAnnotationDB
from pathwaydb.storage.go_db import (
    GOAnnotationDB,
    download_to_cache,
    load_from_cache,
    copy_from_cache,
    get_cache_path
)
from pathwaydb.mapper.id_converter import IDConverter, bulk_convert_entrez_to_symbol
from pathwaydb.core.models import Gene, Pathway, Term
from pathwaydb.data import (
    list_bundled_species,
    has_go_data,
    get_go_data_path
)

__all__ = [
    'KEGG',
    'GO',
    'MSigDB',
    'KEGGAnnotationDB',
    'GOAnnotationDB',
    'IDConverter',
    'bulk_convert_entrez_to_symbol',
    'Gene',
    'Pathway',
    'Term',
    # GO cache functions
    'download_to_cache',
    'load_from_cache',
    'copy_from_cache',
    'get_cache_path',
    # Package data functions
    'list_bundled_species',
    'has_go_data',
    'get_go_data_path',
]

