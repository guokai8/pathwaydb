# Changelog

All notable changes to PathwayDB will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-18

### Added
- **Description-based filtering** for both KEGG and GO annotations
- `pathway_name` parameter in KEGG `filter()` method for case-insensitive substring search
- `term_name` parameter in GO `filter()` method for case-insensitive substring search
- `populate_term_names()` method for GO to fetch term descriptions from QuickGO API
- GO term name storage in database with indexed column for fast filtering
- `to_dataframe()` method for KEGG returning GeneID, PATH, Annot columns
- `to_dataframe()` method for GO returning GeneID, TERM, Aspect, Evidence columns
- `query_by_gene()` method for KEGG and GO connectors
- `stats()` method for KEGG and GO connectors
- Comprehensive filter examples and documentation

### Enhanced
- GO filter now supports filtering by gene symbols, GO IDs, evidence codes, namespace, and term names
- All filters can be combined for complex queries

### Documentation
- Added GO_TERM_NAME_GUIDE.md with complete term name filtering guide
- Added FILTERING_SUMMARY.md with side-by-side KEGG vs GO comparison
- Added FILTER_GUIDE.md with detailed filter comparison
- Added example scripts: go_filter_examples.py, test_go_term_name_filter.py

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
