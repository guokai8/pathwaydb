"""Constants and defaults."""
from typing import Dict

# Species taxonomy IDs
SPECIES_TAXID: Dict[str, str] = {
    'human': '9606',
    'mouse': '10090',
    'rat': '10116',
    'zebrafish': '7955',
    'fly': '7227',
    'worm': '6239',
    'yeast': '4932',
}

# KEGG organism codes
KEGG_ORGANISM: Dict[str, str] = {
    'human': 'hsa',
    'mouse': 'mmu',
    'rat': 'rno',
    'zebrafish': 'dre',
    'fly': 'dme',
    'worm': 'cel',
    'yeast': 'sce',
}

# API endpoints
KEGG_BASE_URL = "https://rest.kegg.jp"
GO_API_URL = "http://api.geneontology.org/api"
GO_QUICKGO_URL = "https://www.ebi.ac.uk/QuickGO/services/annotation/downloadSearch"
GO_GAF_URL = "http://geneontology.org/gene-associations/goa_{species}.gaf.gz"

# Rate limits (requests per second)
DEFAULT_RATE_LIMIT = 3.0
KEGG_RATE_LIMIT = 10.0

# Cache settings
DEFAULT_CACHE_DIR = ".pathwaydb_cache"
CACHE_MAX_AGE_DAYS = 30

