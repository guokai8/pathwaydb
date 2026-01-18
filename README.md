# PathwayDB

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/github-guokai8%2Fpathwaydb-blue.svg)](https://github.com/guokai8/pathwaydb)

A lightweight Python library for querying and storing biological pathway and gene set annotations from major databases.

**Perfect for:**
- 🧬 Gene set enrichment analysis (GSEA)
- 🔬 Pathway annotation and analysis
- 📊 Functional genomics workflows
- 🧪 Bioinformatics pipelines
- 📈 Integration with pandas/R for downstream analysis

## Why PathwayDB?

- **No Dependencies Hassle**: Pure Python stdlib - no compilation, no conflicts, works everywhere
- **Offline-First**: Download once, query forever - perfect for HPC clusters without internet
- **Fast**: Millisecond queries on local SQLite databases
- **DataFrame-Friendly**: Export directly to pandas format for analysis (like clusterProfiler in R)
- **Simple API**: Intuitive methods that feel natural for bioinformaticians
- **Well-Documented**: Clear examples and comprehensive documentation

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [DataFrame Export](#dataframe-export-for-enrichment-analysis)
- [Database Information](#database-information)
- [Advanced Usage](#advanced-usage)
- [Documentation](#documentation)

## Features

- ✅ **Multiple Database Support**: KEGG, Gene Ontology (GO), and MSigDB
- ✅ **Zero External Dependencies**: Uses only Python standard library
- ✅ **Local SQLite Storage**: Download once, query offline forever
- ✅ **DataFrame Export**: Export to pandas-compatible format (like clusterProfiler)
- ✅ **Smart Caching**: HTTP response caching and gene ID mapping cache
- ✅ **Rate Limiting**: Built-in rate limiting for respectful API usage
- ✅ **Gene ID Conversion**: Convert between Entrez, Symbol, Ensembl, and UniProt IDs
- ✅ **Fast Queries**: Millisecond-level queries on local databases

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

# Download all pathway annotations (first time only - takes ~2 minutes)
kegg.download_annotations()
# Output: Downloaded 8,000+ pathway-gene annotations
kegg.convert_ids_to_symbols()
# Query pathways for a specific gene
results = kegg.query_by_gene('TP53')
print(f"TP53 is in {len(results)} pathways")
# Output: TP53 is in 73 pathways

for pathway in results[:3]:
    print(f"  {pathway.pathway_id}: {pathway.pathway_name}")
# Output:
#   hsa05200: Pathways in cancer
#   hsa04115: p53 signaling pathway
#   hsa04110: Cell cycle

# Get database statistics
stats = kegg.stats()
print(stats)
# Output: {'total_annotations': 8234, 'unique_genes': 7894, 'unique_pathways': 354}

# Export to DataFrame format (NEW!)
df_data = kegg.to_dataframe()
# Returns: [{'GeneID': 'TP53', 'PATH': 'hsa05200', 'Annot': 'Pathways in cancer'}, ...]
```

### Gene Ontology (GO)

```python
from pathwaydb import GO

# Initialize GO client
go = GO(storage_path='go_human.db')

# Download GO annotations (first time only)
go.download_annotations(species='human')
# Output: Downloaded 500,000+ gene-term annotations
go.populate_term_names()
# Query GO terms for a specific gene
annotations = go.query_by_gene('BRCA1')
print(f"BRCA1 has {len(annotations)} GO annotations")
# Output: BRCA1 has 156 GO annotations

for ann in annotations[:3]:
    print(f"  {ann.go_id}: {ann.aspect} [{ann.evidence_code}]")
# Output:
#   GO:0006281: P [IBA]  (DNA repair)
#   GO:0006355: P [TAS]  (regulation of transcription)
#   GO:0005515: F [IPI]  (protein binding)

# Filter by namespace (biological_process, molecular_function, cellular_component)
bp_terms = go.filter(namespace='biological_process')
print(f"Biological Process annotations: {len(bp_terms)}")

# Filter by evidence codes (experimental evidence only)
exp_annotations = go.filter(evidence_codes=['EXP', 'IDA', 'IPI', 'IMP'])
print(f"Experimental evidence: {len(exp_annotations)}")

# Combine filters: TP53 + biological_process + experimental evidence
tp53_bp_exp = go.filter(
    gene_symbols=['TP53'],
    namespace='biological_process',
    evidence_codes=['EXP', 'IDA', 'IPI']
)
print(f"TP53 biological processes (experimental): {len(tp53_bp_exp)}")

# NEW FEATURE: Filter by term name/description (like KEGG pathway names!)
# First, populate term names from QuickGO API (one-time setup)
go.populate_term_names()  # Fetches GO term descriptions

# Now you can search by term description (case-insensitive substring match)
dna_repair = go.filter(term_name='DNA repair')
apoptosis = go.filter(term_name='apoptosis')
transcription = go.filter(term_name='transcription')

# Combine term name with other filters
tp53_dna = go.filter(gene_symbols=['TP53'], term_name='DNA')
print(f"TP53 DNA-related terms: {len(tp53_dna)}")

# Export to DataFrame format
df_data = go.to_dataframe()
# Returns: [{'GeneID': 'BRCA1', 'TERM': 'GO:0006281', 'Aspect': 'P', 'Evidence': 'IBA'}, ...]
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

# Query with filters - search by pathway name (case-insensitive substring match)
results = db.filter(pathway_name='cancer')
print(f"Found {len(results)} annotations in cancer-related pathways")
# Output: Found 2389 annotations in cancer-related pathways

# Combine multiple filters
cancer_tp53 = db.filter(pathway_name='cancer', gene_symbols=['TP53'])
print(f"TP53 in {len(cancer_tp53)} cancer pathways")
# Output: TP53 in 15 cancer pathways

# Other filter options
metabolism = db.filter(pathway_name='metabolism')
specific_genes = db.filter(gene_symbols=['TP53', 'BRCA1', 'EGFR'])
specific_pathways = db.filter(pathway_ids=['hsa04110', 'hsa04115'])

# Export to different formats
records = db.to_records()  # List of dicts
gene_sets = db.to_gene_sets()  # For enrichment tools

# Database statistics
stats = db.stats()
print(f"Total annotations: {stats['total_annotations']}")
print(f"Unique pathways: {stats['unique_pathways']}")
print(f"Unique genes: {stats['unique_genes']}")
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

### DataFrame Export for Enrichment Analysis

**NEW FEATURE**: Export annotations in tabular format compatible with pandas DataFrame and enrichment tools (similar to clusterProfiler in R).

#### Direct Export from Connectors

```python
from pathwaydb import KEGG, GO
import pandas as pd

# KEGG - Export to DataFrame format
kegg = KEGG(species='hsa', storage_path='kegg_human.db')
df_data = kegg.to_dataframe()  # Get all annotations

# Convert to pandas DataFrame
df = pd.DataFrame(df_data)
print(df.head())
```

**Output:**
```
     GeneID      PATH                                  Annot
0       A2M  hsa04610  Complement and coagulation cascades
1      NAT1  hsa00232                    Caffeine metabolism
2      NAT1  hsa00983        Drug metabolism - other enzymes
3      NAT1  hsa01100                     Metabolic pathways
4      NAT2  hsa00232                    Caffeine metabolism
```

#### DataFrame Format Specifications

**KEGG DataFrame columns:**
- `GeneID`: Gene symbol (e.g., 'TP53')
- `PATH`: Pathway ID (e.g., 'hsa04110')
- `Annot`: Pathway name/description

**GO DataFrame columns:**
- `GeneID`: Gene symbol (e.g., 'BRCA1')
- `TERM`: GO term ID (e.g., 'GO:0006281')
- `Aspect`: P (biological_process), F (molecular_function), C (cellular_component)
- `Evidence`: Evidence code (e.g., 'EXP', 'IDA', 'IEA')

#### Analysis Examples with pandas

```python
# Get KEGG annotations
kegg = KEGG(species='hsa', storage_path='kegg_human.db')
df = pd.DataFrame(kegg.to_dataframe())

# Save to CSV
df.to_csv('kegg_annotations.csv', index=False)

# Filter for specific gene
tp53_pathways = df[df['GeneID'] == 'TP53']
print(f"TP53 pathways: {len(tp53_pathways)}")

# Find all genes in cancer-related pathways
cancer_df = df[df['Annot'].str.contains('cancer', case=False)]
cancer_genes = cancer_df['GeneID'].unique()
print(f"Genes in cancer pathways: {len(cancer_genes)}")

# Get pathway sizes
pathway_sizes = df.groupby('PATH')['GeneID'].count()
print(pathway_sizes.head())

# GO annotations
go = GO(storage_path='go_human.db')
df_go = pd.DataFrame(go.to_dataframe())

# Filter biological processes only
bp_df = df_go[df_go['Aspect'] == 'P']

# Get genes with experimental evidence
exp_df = df_go[df_go['Evidence'].isin(['EXP', 'IDA', 'IPI', 'IMP'])]
print(f"Annotations with experimental evidence: {len(exp_df)}")

# Create gene-to-term mapping
gene_to_terms = df_go.groupby('GeneID')['TERM'].apply(list).to_dict()
```

#### Use with Enrichment Analysis Tools

```python
# Prepare background gene set
all_genes = df['GeneID'].unique()

# Prepare pathway gene sets for enrichment
pathway_dict = df.groupby('PATH').apply(
    lambda x: {
        'genes': x['GeneID'].tolist(),
        'name': x['Annot'].iloc[0]
    }
).to_dict()

# Your gene list of interest
my_genes = ['TP53', 'BRCA1', 'EGFR', 'MYC', 'KRAS']

# Find enriched pathways (simple overlap example)
for pathway_id, info in pathway_dict.items():
    overlap = set(my_genes) & set(info['genes'])
    if overlap:
        print(f"{pathway_id}: {info['name']} - {len(overlap)} genes")
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

## Documentation

### API Reference

**Main Classes:**
- `KEGG(species, storage_path, cache_dir)` - KEGG pathway database client
- `GO(storage_path, cache_dir)` - Gene Ontology client
- `MSigDB(species, storage_path, cache_dir)` - MSigDB gene sets client
- `IDConverter(species, cache_path)` - Gene ID converter

**Key Methods:**
- `download_annotations()` - Download and store annotations
- `query_by_gene(gene)` - Query annotations for a specific gene
- `to_dataframe(limit)` - Export to pandas-compatible format
- `filter(**criteria)` - Filter annotations by various criteria
- `stats()` - Get database statistics
- `export_gene_sets()` - Export as gene sets dictionary

**Storage Classes:**
- `KEGGAnnotationDB(db_path)` - Direct access to KEGG storage
- `GOAnnotationDB(db_path)` - Direct access to GO storage

For detailed architecture and development guidelines, see [CLAUDE.md](CLAUDE.md).

### Examples

See the `examples/` directory for comprehensive usage examples:
- `examples/quickstart.py` - Basic usage for all databases
- `examples/dataframe_export.py` - DataFrame export and analysis

## Contributing

Contributions are welcome! Here are some ways to contribute:

1. **Add new database connectors** (WikiPathways, STRING, DisGeNET, etc.)
2. **Improve documentation**
3. **Add tests**
4. **Report bugs**
5. **Suggest features**

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines and [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

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

**Version 0.2.0** (Planned):
- [ ] WikiPathways connector
- [ ] Enhanced DataFrame export with metadata
- [ ] Batch download utilities
- [ ] Comprehensive test suite

**Future Considerations** (based on user feedback):
- [ ] STRING protein-protein interactions
- [ ] DisGeNET disease-gene associations
- [ ] Human Phenotype Ontology (HPO)
- [ ] Integration helpers for GSEA/enrichR
- [ ] REST API server mode
- [ ] Command-line interface (CLI)

**Want to contribute?** See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add new database connectors!

## Related Projects

- [mygene](https://github.com/biothings/mygene.py) - Gene annotation queries
- [bioservices](https://github.com/cokelaer/bioservices) - Comprehensive bio web services
- [gprofiler](https://github.com/gprofiler/gprofiler) - Functional enrichment analysis
- [gseapy](https://github.com/zqfang/GSEApy) - GSEA in Python

---

**Made with** ❤️ **for the bioinformatics community**
