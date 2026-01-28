# Filter Guide: KEGG vs GO

This guide explains the filter capabilities for KEGG and GO databases in PathwayDB.

## KEGG Filter

### Available Parameters

```python
from pathwaydb.storage import KEGGAnnotationDB

db = KEGGAnnotationDB('kegg_human.db')

results = db.filter(
    gene_ids=None,           # List[str] - Exact match on gene IDs
    gene_symbols=None,       # List[str] - Exact match on gene symbols
    pathway_ids=None,        # List[str] - Exact match on pathway IDs
    pathway_name=None,       # str - Case-insensitive substring match
    organism=None            # str - Exact match on organism code
)
```

### Examples

```python
# Search by pathway name (case-insensitive substring)
cancer = db.filter(pathway_name='cancer')
# Matches: "Pathways in cancer", "Colorectal cancer", etc.

metabolism = db.filter(pathway_name='metabolism')
signaling = db.filter(pathway_name='signaling')

# Search by specific genes
tp53_pathways = db.filter(gene_symbols=['TP53'])
cancer_genes = db.filter(gene_symbols=['TP53', 'BRCA1', 'EGFR'])

# Search by pathway IDs
cell_cycle = db.filter(pathway_ids=['hsa04110', 'hsa04115'])

# Combine filters
tp53_cancer = db.filter(
    pathway_name='cancer',
    gene_symbols=['TP53']
)
```

### Key Features

✅ **Pathway name search** - Substring matching, case-insensitive
✅ **Gene symbol filtering** - Exact match (multiple allowed)
✅ **Pathway ID filtering** - Exact match (multiple allowed)
✅ **Organism filtering** - For multi-organism databases
✅ **Combinable** - All filters can be combined with AND logic

## GO Filter

### Available Parameters

#### Using GO Connector (Recommended)

```python
from pathwaydb import GO

go = GO(storage_path='go_human.db')

results = go.filter(
    gene_symbols=None,       # List[str] - Exact match on gene symbols
    go_ids=None,             # List[str] - Exact match on GO term IDs
    evidence_codes=None,     # List[str] - Exact match on evidence codes
    aspect=None,             # str - P/F/C (aspect code)
    namespace=None           # str - 'biological_process', 'molecular_function', 'cellular_component'
)
```

#### Using Storage Directly

```python
from pathwaydb.storage import GOAnnotationDB

db = GOAnnotationDB('go_human.db')

results = db.filter(
    gene_ids=None,           # List[str] - Exact match on gene IDs
    gene_symbols=None,       # List[str] - Exact match on gene symbols
    go_ids=None,             # List[str] - Exact match on GO term IDs
    evidence_codes=None,     # List[str] - Exact match on evidence codes
    aspect=None              # str - P/F/C (aspect code)
)
```

### Examples

```python
# Filter by gene symbols
brca1 = db.filter(gene_symbols=['BRCA1'])
cancer_genes = db.filter(gene_symbols=['TP53', 'BRCA1', 'EGFR'])

# Filter by namespace (using connector)
bp = go.filter(namespace='biological_process')
mf = go.filter(namespace='molecular_function')
cc = go.filter(namespace='cellular_component')

# Filter by aspect (using storage)
bp = db.filter(aspect='P')  # biological_process
mf = db.filter(aspect='F')  # molecular_function
cc = db.filter(aspect='C')  # cellular_component

# Filter by evidence codes
experimental = db.filter(evidence_codes=['EXP', 'IDA', 'IPI', 'IMP'])
computational = db.filter(evidence_codes=['IEA'])
curated = db.filter(evidence_codes=['TAS', 'IC'])

# Filter by specific GO terms
dna_repair = db.filter(go_ids=['GO:0006281'])
apoptosis = db.filter(go_ids=['GO:0006915'])

# Combine filters
tp53_bp_exp = db.filter(
    gene_symbols=['TP53'],
    aspect='P',
    evidence_codes=['EXP', 'IDA', 'IPI']
)
```

### Key Features

✅ **Gene symbol filtering** - Exact match (multiple allowed)
✅ **GO term ID filtering** - Exact match (multiple allowed)
✅ **Evidence code filtering** - Filter by quality/source
✅ **Namespace/Aspect filtering** - User-friendly or code-based
✅ **Combinable** - All filters can be combined with AND logic
❌ **NO term name search** - Must use GO IDs, not names

## Evidence Codes (GO Only)

### Experimental Evidence (High Confidence)
- **EXP**: Inferred from Experiment
- **IDA**: Inferred from Direct Assay
- **IPI**: Inferred from Physical Interaction
- **IMP**: Inferred from Mutant Phenotype
- **IGI**: Inferred from Genetic Interaction
- **IEP**: Inferred from Expression Pattern

### Computational Analysis
- **IEA**: Inferred from Electronic Annotation (automated)
- **ISS**: Inferred from Sequence/Structural Similarity
- **ISO**: Inferred from Sequence Orthology
- **ISA**: Inferred from Sequence Alignment

### Author/Curator Statements
- **TAS**: Traceable Author Statement
- **NAS**: Non-traceable Author Statement
- **IC**: Inferred by Curator
- **ND**: No biological Data available

## Comparison Table

| Feature | KEGG | GO |
|---------|------|-----|
| Filter by gene symbol | ✅ Exact match | ✅ Exact match |
| Filter by ID | ✅ Pathway ID | ✅ GO term ID |
| Filter by name/description | ✅ Substring match | ❌ Not supported |
| Filter by category | ❌ | ✅ Namespace/Aspect |
| Filter by evidence/quality | ❌ | ✅ Evidence codes |
| Case-insensitive search | ✅ (pathway_name) | ❌ |
| Substring matching | ✅ (pathway_name) | ❌ |

## Tips and Best Practices

### KEGG

```python
# Find all signaling pathways
signaling = db.filter(pathway_name='signaling')

# Case doesn't matter
cancer1 = db.filter(pathway_name='cancer')
cancer2 = db.filter(pathway_name='Cancer')
cancer3 = db.filter(pathway_name='CANCER')
# All return the same results

# Combine for specific queries
jak_stat = db.filter(
    pathway_name='JAK-STAT',
    gene_symbols=['STAT1', 'STAT3']
)
```

### GO

```python
# Get high-quality annotations only
high_quality = db.filter(
    evidence_codes=['EXP', 'IDA', 'IPI', 'IMP', 'TAS', 'IC']
)

# Exclude computational predictions
non_iea = db.filter(
    evidence_codes=['EXP', 'IDA', 'IPI', 'IMP', 'IGI', 'IEP', 'TAS', 'IC', 'NAS']
)

# Get specific functional categories
dna_processes = db.filter(
    go_ids=['GO:0006281', 'GO:0006260', 'GO:0006302'],  # DNA repair, replication, processing
    evidence_codes=['EXP', 'IDA']
)
```

## Workarounds for Missing Features

### GO: Search by Term Name

Since GO doesn't store term names locally, use the GO connector to look up terms first:

```python
from pathwaydb import GO

go = GO(storage_path='go_human.db')

# Look up a term by ID to see its name
term = go.get_term('GO:0006281')
print(f"{term.id}: {term.name}")  # GO:0006281: DNA repair

# Then filter by that term
dna_repair_genes = db.filter(go_ids=['GO:0006281'])
```

Or use external GO browsers like:
- [QuickGO](https://www.ebi.ac.uk/QuickGO/)
- [AmiGO](http://amigo.geneontology.org/)

## Summary

- **KEGG**: Best for pathway name-based searches and organism-specific queries
- **GO**: Best for evidence-based filtering and hierarchical category analysis
- Both support combining multiple filters with AND logic
- Both can be exported to DataFrame format for pandas analysis
