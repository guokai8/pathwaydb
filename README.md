**pathwaydb** is a biological annotation package for querying and storing gene/pathway annotations from major databases (KEGG, GO, MSigDB). It provides a Python library with HTTP clients, local SQLite storage, gene ID conversion, and DataFrame-like query interfaces.

## Core Architecture

### 3-Layer Design

1. **Connectors Layer** (`pathwaydb/connectors/`)
   - API clients for external databases (KEGG, GO, MSigDB)
   - Each connector handles HTTP requests, rate limiting, and API-specific parsing
   - Key classes: `KEGG`, `GO`, `MSigDB`
   - All connectors can download data and optionally initialize local storage

2. **Storage Layer** (`pathwaydb/storage/`)
   - SQLite-backed annotation databases with DataFrame-like interfaces
   - Each database type has dedicated schema and query methods
   - Key classes: `KEGGAnnotationDB`, `GOAnnotationDB`
   - Storage classes are independent and can be used standalone via functions like `download_kegg_annotations()` (avoids circular imports)

3. **HTTP Layer** (`pathwaydb/http/`)
   - Centralized HTTP client with retry logic, rate limiting, and disk caching
   - `HTTPClient` handles all external requests
   - `DiskCache` provides persistent caching for API responses
   - `RateLimiter` enforces per-client rate limits

### Core Data Models (`pathwaydb/core/models.py`)

- `Gene`: Gene representation with ID, symbol, name, synonyms, species
- `Pathway`: Pathway/gene set with ID, name, description, genes list, species
- `Term`: Ontology term (GO, etc.) with ID, name, namespace, definition, hierarchy
- `Annotation`: Gene-to-term annotation with evidence codes
- All models are frozen dataclasses with `to_dict()` methods

### ID Conversion (`pathwaydb/mapper/id_converter.py`)

- `IDConverter`: Converts between gene ID types (Entrez, Symbol, Ensembl, UniProt)
- Uses MyGene.info API with local SQLite caching
- Batch processing support for efficient conversion of large ID lists
- Cache location: `.pathwaydb_cache/id_mapping_{species}.db`

## Key Patterns

### Connector-Storage Separation

Connectors can operate independently or with storage. When initialized with `storage_path`, connectors can download and persist data locally:

```python
# Connector with storage
kegg = KEGG(species='hsa', storage_path='kegg_human.db')
kegg.download_annotations()  # Downloads and stores

# Standalone storage usage (no HTTP client)
from pathwaydb.storage.kegg_db import download_kegg_annotations
db = download_kegg_annotations(organism='hsa', output_path='kegg.db')
```

### DataFrame-like Query Interface

All storage classes provide consistent query methods:
- `filter()`: Multi-criteria filtering
- `query_by_gene()`: Query by gene IDs/symbols
- `to_records()`: Export as list of dicts
- `to_dict()`: Export as dict of lists
- `to_gene_sets()`: Export for enrichment analysis
- `stats()`: Database statistics

### Caching Strategy

Two-level caching:
1. **HTTP Cache** (`.cache/` or custom): Caches raw API responses (gzipped JSON)
2. **ID Mapping Cache** (`.pathwaydb_cache/`): Caches ID conversions permanently

### Species Handling

- KEGG uses organism codes (e.g., 'hsa' for human)
- GO/MSigDB use common names ('human', 'mouse')
- Constants defined in `pathwaydb/core/constants.py`: `SPECIES_TAXID`, `KEGG_ORGANISM`

## Common Development Workflows

### Adding a New Database Connector

1. Create connector class in `pathwaydb/connectors/`
2. Inherit from or use `HTTPClient` for API calls
3. Create corresponding storage class in `pathwaydb/storage/` with schema and query methods
4. Add data models to `pathwaydb/core/models.py` if needed
5. Export public API in `pathwaydb/__init__.py`

### Working with Storage

Storage classes use SQLite with proper indexing. Key patterns:
- Primary keys prevent duplicates
- Indexes on commonly queried columns (gene_symbol, pathway_id, etc.)
- `INSERT OR REPLACE` for upserts
- `INSERT OR IGNORE` for many-to-many mappings
- Batch commits for performance (commit every 100-1000 records)

### Gene ID Conversion

ID conversion is centralized in `IDConverter`. When connectors download data with non-symbol IDs:
1. Download raw data with original IDs (e.g., Entrez from KEGG)
2. Store original IDs in database
3. Convert IDs using `IDConverter` (automatically cached)
4. Update database with symbols: `kegg.convert_ids_to_symbols()`
