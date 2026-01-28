# PathwayDB Filtering: Complete Summary

## Overview

PathwayDB now supports filtering by **description/name** for both KEGG and GO databases!

## Quick Comparison

| Database | Filter by Description | Syntax |
|----------|----------------------|--------|
| **KEGG** | ✅ Pathway names | `kegg.filter(pathway_name='cancer')` |
| **GO** | ✅ Term names | `go.filter(term_name='DNA repair')` |

Both support:
- ✅ Case-insensitive substring matching
- ✅ Combining with other filter criteria
- ✅ Fast indexed database queries

## KEGG Filtering

### Available Parameters

```python
from pathwaydb import KEGG

kegg = KEGG(species='hsa', storage_path='kegg_human.db')

results = kegg.filter(
    gene_symbols=['TP53', 'BRCA1'],      # Exact match
    pathway_name='cancer',                # Case-insensitive substring
    pathway_ids=['hsa04110', 'hsa04115'], # Exact match
    organism='hsa'                        # Exact match
)
```

### Examples

```python
# Search by pathway name
cancer = kegg.filter(pathway_name='cancer')
metabolism = kegg.filter(pathway_name='metabolism')
signaling = kegg.filter(pathway_name='signaling')

# Combine filters
tp53_cancer = kegg.filter(
    gene_symbols=['TP53'],
    pathway_name='cancer'
)
```

### Features

✅ **Pathway name search** - No need to remember pathway IDs
✅ **Case-insensitive** - 'cancer', 'Cancer', 'CANCER' all work
✅ **Substring matching** - 'cancer' matches "Pathways in cancer", "Colorectal cancer", etc.
✅ **Ready to use** - No extra setup required

## GO Filtering

### Available Parameters

```python
from pathwaydb import GO

go = GO(storage_path='go_human.db')

results = go.filter(
    gene_symbols=['TP53', 'BRCA1'],      # Exact match
    term_name='DNA repair',               # Case-insensitive substring (NEW!)
    namespace='biological_process',       # User-friendly names
    evidence_codes=['EXP', 'IDA'],       # Quality filtering
    go_ids=['GO:0006281']                # Exact match
)
```

### Setup Required

<<<<<<< HEAD
**ONE-TIME SETUP** to enable term name filtering:
=======
**v0.2.0+:** Term names are automatically fetched during download!
>>>>>>> 0ad8423 (revise function)

```python
from pathwaydb import GO

go = GO(storage_path='go_human.db')

<<<<<<< HEAD
# Step 1: Download annotations
go.download_annotations(species='human')

# Step 2: Fetch term names from QuickGO API (takes a few minutes)
go.populate_term_names()

# Step 3: Now you can filter by term name!
dna_repair = go.filter(term_name='DNA repair')
```

=======
# Download annotations (term names fetched automatically)
go.download_annotations(species='human')

# Filter by term name - it just works!
dna_repair = go.filter(term_name='DNA repair')
```

**Optional:** Skip automatic term name fetching if needed:
```python
# Advanced: skip automatic fetching
go.download_annotations(species='human', fetch_term_names=False)

# Fetch later if needed
go.populate_term_names()
```

>>>>>>> 0ad8423 (revise function)
### Examples

```python
# Search by term name (after running populate_term_names)
dna = go.filter(term_name='DNA')
apoptosis = go.filter(term_name='apoptosis')
transcription = go.filter(term_name='transcription')

# Combine filters
tp53_dna = go.filter(
    gene_symbols=['TP53'],
    term_name='DNA',
    evidence_codes=['EXP', 'IDA']  # Experimental evidence only
)

# Combine with namespace
cell_cycle_bp = go.filter(
    namespace='biological_process',
    term_name='cell cycle'
)
```

### Features

✅ **Term name search** - No need to remember GO IDs
✅ **Case-insensitive** - 'DNA', 'dna', 'Dna' all work
✅ **Substring matching** - 'DNA' matches "DNA repair", "DNA replication", etc.
✅ **Namespace filtering** - User-friendly category names
✅ **Evidence code filtering** - Filter by quality/source
✅ **Combinable** - All filters work together

## Side-by-Side Examples

### KEGG: Find Cancer Pathways

```python
from pathwaydb import KEGG

kegg = KEGG(species='hsa', storage_path='kegg_human.db')
kegg.download_annotations()

# Find all cancer-related pathways
cancer = kegg.filter(pathway_name='cancer')
print(f"Found {len(cancer)} cancer annotations")

# Find TP53 in cancer pathways
tp53_cancer = kegg.filter(
    gene_symbols=['TP53'],
    pathway_name='cancer'
)
print(f"TP53 in {len(tp53_cancer)} cancer pathway annotations")
```

### GO: Find DNA Repair Terms

```python
from pathwaydb import GO

go = GO(storage_path='go_human.db')
go.download_annotations(species='human')
go.populate_term_names()  # ONE-TIME SETUP

# Find all DNA repair terms
dna_repair = go.filter(term_name='DNA repair')
print(f"Found {len(dna_repair)} DNA repair annotations")

# Find TP53 DNA repair annotations
tp53_dna_repair = go.filter(
    gene_symbols=['TP53'],
    term_name='DNA repair'
)
print(f"TP53 in {len(tp53_dna_repair)} DNA repair annotations")
```

## Full Feature Matrix

| Feature | KEGG | GO |
|---------|------|-----|
| **Filter by name/description** | ✅ `pathway_name` | ✅ `term_name` |
| **Case-insensitive** | ✅ | ✅ |
| **Substring matching** | ✅ | ✅ |
| **Filter by gene symbol** | ✅ | ✅ |
| **Filter by ID** | ✅ `pathway_ids` | ✅ `go_ids` |
| **Filter by category** | ❌ | ✅ `namespace`/`aspect` |
| **Filter by quality** | ❌ | ✅ `evidence_codes` |
<<<<<<< HEAD
| **Setup required** | ❌ None | ⚠️ Run `populate_term_names()` once |
=======
| **Setup required** | ❌ None | ✅ Automatic (v0.2.0+) |
>>>>>>> 0ad8423 (revise function)
| **Data source** | KEGG API | GAF files + QuickGO API |

## Common Use Cases

### 1. Find All Genes in a Biological Process

```python
# KEGG: By pathway name
cancer_genes = kegg.filter(pathway_name='cancer')

# GO: By term name
apoptosis_genes = go.filter(
    namespace='biological_process',
    term_name='apoptosis'
)
```

### 2. Find Specific Gene's Functions

```python
# KEGG: TP53 pathways
tp53_pathways = kegg.filter(gene_symbols=['TP53'])

# GO: TP53 functions
tp53_functions = go.filter(gene_symbols=['TP53'])

# GO: TP53 DNA-related functions
tp53_dna = go.filter(
    gene_symbols=['TP53'],
    term_name='DNA'
)
```

### 3. High-Quality Annotations Only

```python
# GO: Experimental evidence only
exp_annotations = go.filter(
    term_name='transcription',
    evidence_codes=['EXP', 'IDA', 'IPI', 'IMP']
)

# GO: Exclude computational predictions
curated = go.filter(
    term_name='DNA repair',
    evidence_codes=['EXP', 'IDA', 'TAS', 'IC']
)
```

### 4. Combine Multiple Criteria

```python
# KEGG: Multiple genes in specific pathways
results = kegg.filter(
    gene_symbols=['TP53', 'BRCA1', 'EGFR'],
    pathway_name='signaling'
)

# GO: Complex query
results = go.filter(
    gene_symbols=['TP53'],
    namespace='biological_process',
    term_name='cell cycle',
    evidence_codes=['EXP', 'IDA']
)
```

## Tips and Best Practices

### KEGG

1. **Use broad search terms** - 'cancer' matches many pathway variants
2. **Case doesn't matter** - 'cancer', 'Cancer', 'CANCER' all work
3. **No setup required** - Works immediately after download

### GO

1. **Run `populate_term_names()` once** - Then term name filtering works forever
2. **Use specific terms** - 'DNA repair' is better than just 'repair'
3. **Combine with evidence codes** - Get high-quality annotations
4. **Use namespace** - Filter by biological_process, molecular_function, cellular_component

## Performance

| Operation | KEGG | GO |
|-----------|------|-----|
| **Initial download** | ~2 min | ~3-5 min |
| **Populate term names** | N/A | ~2-5 min (one-time) |
| **Filtering queries** | Milliseconds | Milliseconds |
| **Storage size** | ~8 MB | ~50 MB |

## Documentation

- **[FILTER_GUIDE.md](FILTER_GUIDE.md)** - Detailed filter comparison
- **[GO_TERM_NAME_GUIDE.md](GO_TERM_NAME_GUIDE.md)** - GO term name filtering guide
- **[README.md](README.md)** - Main documentation
- **[examples/go_filter_examples.py](examples/go_filter_examples.py)** - Comprehensive examples

## Summary

Both KEGG and GO now support **intuitive description-based filtering**:

```python
# KEGG - No setup required
kegg.filter(pathway_name='cancer')

<<<<<<< HEAD
# GO - One-time setup
go.populate_term_names()  # Run once
go.filter(term_name='DNA repair')  # Then use forever
```

=======
# GO - Automatic setup (v0.2.0+)
go.download_annotations(species='human')  # Term names fetched automatically
go.filter(term_name='DNA repair')
```

**What's New in v0.2.0:**
- ✅ GO term names are **automatically fetched** during download
- ✅ No separate `populate_term_names()` step needed (runs automatically)
- ✅ Consistent, user-friendly API across both databases

>>>>>>> 0ad8423 (revise function)
This makes PathwayDB much more user-friendly - no need to remember IDs, just search by description! 🎉
