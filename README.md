# PathwayDB

A lightweight Python library for querying and storing biological pathway and gene set annotations from major databases.

## Features

- **Multiple Database Support**: KEGG, Gene Ontology (GO), and MSigDB
- **Zero External Dependencies**: Uses only Python standard library
- **Local SQLite Storage**: Download once, query offline forever
- **Smart Caching**: HTTP response caching and gene ID mapping cache
- **Rate Limiting**: Built-in rate limiting for respectful API usage
- **Gene ID Conversion**: Convert between Entrez, Symbol, Ensembl, and UniProt IDs
- **DataFrame-like Interface**: Familiar query patterns for bioinformaticians

## Installation

### From Source

```bash
git clone https://github.com/guokai8/pathwaydb.git
cd pathwaydb
pip install -e .
```

### From PyPI (coming soon)

```bash
pip install pathwaydb
```

## Quick Start

### KEGG Pathways

```python
from pathwaydb import KEGG

# Initialize KEGG client with local storage
kegg = KEGG(species='hsa', storage_path='kegg_human.db')

# Download all pathway annotations (first time only)
kegg.download_annotations()

# Query by gene
results = kegg.query_by_gene('TP53')
print(f"TP53 is in {len(results)} pathways")

# Get pathway details
pathway = kegg.get_pathway('hsa05200')  # Cancer pathways
print(f"{pathway.name}: {len(pathway.genes)} genes")

# Export for enrichment analysis
gene_sets = kegg.export_gene_sets()
```

### Gene Ontology (GO)

```python
from pathwaydb import GO

# Initialize GO client
go = GO(species='human', storage_path='go_human.db')

# Download GO annotations
go.download_annotations()

# Query by gene
annotations = go.query_by_gene('BRCA1')
for ann in annotations:
    print(f"{ann.gene_symbol} -> {ann.term_name} ({ann.evidence_code})")

# Filter by namespace
bp_terms = go.filter(namespace='biological_process')
print(f"Biological Process terms: {len(bp_terms)}")
```

### MSigDB Gene Sets

```python
from pathwaydb import MSigDB

# Initialize MSigDB client
msigdb = MSigDB(species='human', storage_path='msigdb.db')

# Download specific collections
msigdb.download_collection('H')  # Hallmark gene sets
msigdb.download_collection('C2')  # Curated gene sets (KEGG, Reactome, etc.)

# Search gene sets
results = msigdb.search_gene_sets('interferon')
for gs in results:
    print(f"{gs.name}: {len(gs.genes)} genes")

# Query by gene
gene_sets = msigdb.query_by_gene('STAT1')
```

### Gene ID Conversion

```python
from pathwaydb import IDConverter

# Initialize converter
converter = IDConverter(species='human')

# Convert single ID
symbol = converter.entrez_to_symbol('7157')  # Returns 'TP53'

# Batch conversion
entrez_ids = ['7157', '675', '4609']
symbols = converter.batch_convert(entrez_ids, from_type='entrez', to_type='symbol')

# Multiple ID types supported
ensembl_id = converter.symbol_to_ensembl('TP53')
uniprot_id = converter.symbol_to_uniprot('TP53')
```

## Database Information

### KEGG (Kyoto Encyclopedia of Genes and Genomes)

- **Coverage**: 500+ organisms, 500+ pathways per species
- **Content**: Metabolic, signaling, disease pathways
- **Update**: Manually curated, regularly updated
- **Species codes**: 'hsa' (human), 'mmu' (mouse), 'rno' (rat), etc.

### GO (Gene Ontology)

- **Coverage**: Thousands of species
- **Content**: Biological processes, molecular functions, cellular components
- **Update**: Continuously updated by consortium
- **Hierarchy**: DAG structure with parent-child relationships

### MSigDB (Molecular Signatures Database)

- **Collections**:
  - `H`: Hallmark gene sets (50 sets)
  - `C1`: Positional gene sets
  - `C2`: Curated gene sets (KEGG, Reactome, BioCarta, etc.)
  - `C3`: Regulatory target gene sets
  - `C4`: Computational gene sets
  - `C5`: Gene Ontology gene sets
  - `C6`: Oncogenic signatures
  - `C7`: Immunologic signatures
  - `C8`: Cell type signatures

## Advanced Usage

### Working with Local Databases

```python
from pathwaydb.storage import KEGGAnnotationDB

# Load existing database
db = KEGGAnnotationDB('kegg_human.db')

# Query with filters
results = db.filter(pathway_name='cancer')

# Export to different formats
records = db.to_records()  # List of dicts
gene_sets = db.to_gene_sets()  # For enrichment tools

# Database statistics
stats = db.stats()
print(f"Total pathways: {stats['total_pathways']}")
print(f"Total genes: {stats['total_genes']}")
```

### Custom Caching

```python
from pathwaydb import KEGG

# Use custom cache directory
kegg = KEGG(
    species='hsa',
    cache_dir='/path/to/custom/cache',
    storage_path='kegg.db'
)
```

### Batch Operations

```python
from pathwaydb import KEGG

kegg = KEGG(species='hsa', storage_path='kegg.db')

# Download and convert IDs in one step
kegg.download_annotations()
kegg.convert_ids_to_symbols()  # Convert Entrez IDs to gene symbols

# Query multiple genes
genes = ['TP53', 'BRCA1', 'EGFR']
for gene in genes:
    pathways = kegg.query_by_gene(gene)
    print(f"{gene}: {len(pathways)} pathways")
```

## Architecture

PathwayDB follows a clean 3-layer architecture:

1. **Connectors Layer** (`pathwaydb/connectors/`): API clients for external databases
2. **Storage Layer** (`pathwaydb/storage/`): SQLite-backed local storage with query interfaces
3. **HTTP Layer** (`pathwaydb/http/`): Centralized HTTP client with caching and rate limiting

### Key Design Principles

- **No external dependencies**: Easier deployment, fewer conflicts
- **Caching by default**: Respectful of API servers, faster repeat queries
- **Separation of concerns**: Connectors and storage are independent
- **Extensible**: Easy to add new databases following existing patterns

## Performance

- **Initial download**: 1-5 minutes depending on database size
- **Subsequent queries**: Milliseconds (SQLite local queries)
- **Memory footprint**: Low (streaming downloads, efficient storage)
- **Storage size**:
  - KEGG (human): ~8 MB
  - MSigDB (all collections): ~77 MB
  - GO (human): ~50 MB

## Species Support

### KEGG
Use organism codes: `hsa` (human), `mmu` (mouse), `rno` (rat), `dme` (fly), `cel` (worm), `sce` (yeast), etc.

### GO and MSigDB
Use common names: `human`, `mouse`, `rat`, etc.

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# With coverage
pytest --cov=pathwaydb tests/
```

### Code Formatting

```bash
# Format with black
black pathwaydb/

# Lint with flake8
flake8 pathwaydb/

# Type checking
mypy pathwaydb/
```

## Contributing

Contributions are welcome! Here are some ways to contribute:

1. **Add new database connectors** (WikiPathways, STRING, DisGeNET, etc.)
2. **Improve documentation**
3. **Add tests**
4. **Report bugs**
5. **Suggest features**

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## License

MIT License - see LICENSE file for details

## Citation

If you use PathwayDB in your research, please cite:

```
@software{pathwaydb,
  title = {PathwayDB: A Lightweight Pathway Annotation Toolkit},
  author = {Guo, Kai},
  year = {2026},
  url = {https://github.com/guokai8/pathwaydb}
}
```

## Acknowledgments

- **KEGG**: Kanehisa, M. et al. (2023) KEGG for taxonomy-based analysis
- **GO**: Gene Ontology Consortium (2023) The Gene Ontology knowledgebase
- **MSigDB**: Liberzon, A. et al. (2015) The Molecular Signatures Database
- **MyGene.info**: Used for gene ID conversion

## Support

- **Issues**: [GitHub Issues](https://github.com/guokai8/pathwaydb/issues)
- **Documentation**: [CLAUDE.md](CLAUDE.md)
- **Email**: guokai8@gmail.com

## Roadmap

- [ ] Add WikiPathways support
- [ ] Add STRING protein interactions
- [ ] Add DisGeNET disease associations
- [ ] Batch download utilities
- [ ] Web interface for queries
- [ ] Integration with popular enrichment tools (GSEA, enrichR)
- [ ] REST API server mode

## Related Projects

- [mygene](https://github.com/biothings/mygene.py) - Gene annotation queries
- [bioservices](https://github.com/cokelaer/bioservices) - Comprehensive bio web services
- [gprofiler](https://github.com/gprofiler/gprofiler) - Functional enrichment analysis
- [gseapy](https://github.com/zqfang/GSEApy) - GSEA in Python

---

**Made with** ❤️ **for the bioinformatics community**
