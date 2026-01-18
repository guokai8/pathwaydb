# Changelog

All notable changes to PathwayDB will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-18

### Added
- **Unified filtering system** across all three databases (KEGG, GO, MSigDB)
- **Description-based filtering** for KEGG, GO, and MSigDB annotations
- **Automatic GO term name fetching** - term names now fetched automatically during `download_annotations()` (no separate step needed!)
- **Centralized GO annotation caching** - download once, reuse across all projects
- **Bundled GO term name mapping** - lightweight (~1-2 MB) GO ID → term name mapping included in package for instant term name access
- `pathway_name` parameter in KEGG `filter()` method for case-insensitive substring search
- `term_name` parameter in GO `filter()` method for case-insensitive substring search
- `gene_set_name` and `description` parameters in MSigDB `filter()` method
- `fetch_term_names` parameter in GO `download_annotations()` to control automatic term name fetching (default: True)
- `populate_term_names()` method for GO to manually fetch term descriptions from QuickGO API (now optional)
- GO term name storage in database with indexed column for fast filtering
- `download_to_cache()` function to download GO annotations to centralized cache (~/.pathwaydb_cache/go_annotations/)
- `load_from_cache()` function to load GO annotations from cache (auto-downloads if missing)
- `copy_from_cache()` function to copy cached annotations to project-specific database
- `get_cache_path()` function to get cache file path for a species
- `GO.from_cache()` class method to create GO instance using cached annotations
- `GO.from_package_data()` class method to load bundled package data
- `GO.load()` class method with automatic source detection (package data > cache > download)
- `list_bundled_species()` function to list species with bundled data
- `has_go_data()` function to check if species data is bundled
- `get_go_data_path()` function to get path to bundled data
- `prepare_package_data.py` script to download and prepare full GO databases for packaging (optional)
- `prepare_go_term_names.py` script to fetch and prepare GO term name mapping for packaging (recommended)
- `to_dataframe()` method for KEGG returning GeneID, PATH, Annot columns
- `to_dataframe()` method for GO returning GeneID, TERM, Aspect, Evidence columns
- `to_dataframe()` method for MSigDB returning GeneID, GeneSet, Collection, Description columns
- `query_by_gene()` method for KEGG and GO connectors
- `stats()` method for KEGG, GO, and MSigDB connectors
- `filter()` method for MSigDB with comprehensive filtering options
- Comprehensive filter examples and documentation

### Enhanced
- GO filter now supports filtering by gene symbols, GO IDs, evidence codes, namespace, and term names
- MSigDB filter now supports filtering by gene symbols, gene set name, description, collection, and organism
- All filters can be combined for complex queries across all databases
- Consistent API design across KEGG, GO, and MSigDB
- Simplified user experience - GO term names are now automatic (no manual `populate_term_names()` call needed)

### Documentation
- Added GO_TERM_NAME_GUIDE.md with complete term name filtering guide
- Added GO_CACHE_GUIDE.md with comprehensive caching guide
- Added PACKAGING_GUIDE.md with instructions for bundling GO data with package
- Added FILTERING_SUMMARY.md with side-by-side KEGG vs GO comparison
- Added FILTER_GUIDE.md with detailed filter comparison
- Added DATABASE_FILTERING_GUIDE.md with complete filtering guide for all databases
- Added example scripts: go_filter_examples.py, test_go_term_name_filter.py, test_msigdb_filter.py, test_go_cache.py, test_go_automatic_term_names.py, test_package_data.py

## [0.1.0] - 2026-01-18

### Added
- Initial release of PathwayDB
- KEGG pathway annotations support
- Gene Ontology (GO) annotations support
- MSigDB gene sets support
- Gene ID conversion (Entrez, Symbol, Ensembl, UniProt)
- Local SQLite storage with caching
- HTTP client with rate limiting and disk caching
- Zero external dependencies (stdlib only)

### Features
- Download once, query offline workflow
- Automatic gene ID conversion from Entrez to Symbol
- pandas-compatible DataFrame export
- Smart caching for API responses and ID mappings
- Rate limiting for respectful API usage
- DataFrame-like query interface

### Documentation
- Comprehensive README with examples
- Quick start guide
- DataFrame export examples
- API reference
- Contributing guidelines
- Development guide (CLAUDE.md)
- Example scripts in `examples/` directory

### Infrastructure
- MIT License
- Python 3.8+ support
- GitHub repository setup
- setup.py for package installation
- .gitignore for Python projects

## [Unreleased]

### Planned for v0.2.0
- WikiPathways connector
- Enhanced DataFrame export with metadata
- Batch download utilities
- Comprehensive test suite

### Future Considerations
- STRING protein-protein interactions
- DisGeNET disease-gene associations
- Human Phenotype Ontology (HPO)
- Integration helpers for GSEA/enrichR
- REST API server mode
- Command-line interface (CLI)
