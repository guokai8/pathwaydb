# PathwayDB Filtering Guide: KEGG, GO, and MSigDB

## Overview

PathwayDB provides **unified filtering** across all three databases with consistent API design!

All databases support:
- ✅ **Description-based filtering** - Search by name/description, not just IDs
- ✅ **Case-insensitive matching** - 'cancer', 'Cancer', 'CANCER' all work
- ✅ **Substring search** - Partial matches automatically
- ✅ **Combined filters** - Mix multiple criteria for complex queries
- ✅ **DataFrame export** - Pandas-compatible format for analysis

## Quick Comparison

| Database | Filter by Description | DataFrame Columns |
|----------|----------------------|-------------------|
| **KEGG** | `pathway_name='cancer'` | GeneID, PATH, Annot |
| **GO** | `term_name='DNA repair'` | GeneID, TERM, Aspect, Evidence |
| **MSigDB** | `gene_set_name='apoptosis'` | GeneID, GeneSet, Collection, Description |

## KEGG Filtering

### Available Parameters

```python
from pathwaydb import KEGG

kegg = KEGG(species='hsa', storage_path='kegg_human.db')
kegg.download_annotations()

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

# Combine filters
tp53_cancer = kegg.filter(
    gene_symbols=['TP53'],
    pathway_name='cancer'
)

# Export to DataFrame
data = kegg.to_dataframe()
# Returns: [{'GeneID': 'TP53', 'PATH': 'hsa05200', 'Annot': 'Pathways in cancer'}, ...]
```

## GO Filtering

### Available Parameters

```python
from pathwaydb import GO

go = GO(storage_path='go_human.db')
<<<<<<< HEAD
go.download_annotations(species='human')
go.populate_term_names()  # ONE-TIME SETUP for term name filtering
=======
go.download_annotations(species='human')  # Term names fetched automatically (v0.2.0+)
>>>>>>> 0ad8423 (revise function)

results = go.filter(
    gene_symbols=['TP53', 'BRCA1'],      # Exact match
    term_name='DNA repair',               # Case-insensitive substring
    namespace='biological_process',       # User-friendly names
    evidence_codes=['EXP', 'IDA'],       # Quality filtering
    go_ids=['GO:0006281']                # Exact match
)
```

### Examples

```python
# Search by term name (after populate_term_names)
dna_repair = go.filter(term_name='DNA repair')
apoptosis = go.filter(term_name='apoptosis')

# Combine filters
tp53_dna = go.filter(
    gene_symbols=['TP53'],
    term_name='DNA',
    evidence_codes=['EXP', 'IDA']  # Experimental evidence only
)

# Filter by namespace
cell_cycle_bp = go.filter(
    namespace='biological_process',
    term_name='cell cycle'
)

# Export to DataFrame
data = go.to_dataframe()
# Returns: [{'GeneID': 'TP53', 'TERM': 'GO:0006281', 'Aspect': 'P', 'Evidence': 'IDA'}, ...]
```

## MSigDB Filtering

### Available Parameters

```python
from pathwaydb import MSigDB

msigdb = MSigDB(storage_path='msigdb.db')
msigdb.download_collection('H')  # Hallmark gene sets

results = msigdb.filter(
    gene_symbols=['TP53', 'MYC'],         # Find sets containing these genes
    gene_set_name='apoptosis',            # Case-insensitive substring
    description='immune',                 # Search in description
    collection='H',                       # H, C1, C2, etc.
    organism='human'                      # human or mouse
)
```

### Examples

```python
# Search by gene set name
apoptosis = msigdb.filter(gene_set_name='apoptosis')
interferon = msigdb.filter(gene_set_name='interferon')

# Filter by description
immune = msigdb.filter(description='immune')

# Filter by collection
hallmark = msigdb.filter(collection='H')
kegg_reactome = msigdb.filter(collection='C2')

# Find gene sets containing specific genes
tp53_sets = msigdb.filter(gene_symbols=['TP53'])

# Combine filters
hallmark_interferon = msigdb.filter(
    collection='H',
    gene_set_name='interferon'
)

# Export to DataFrame
data = msigdb.to_dataframe(collection='H')
# Returns: [{'GeneID': 'TP53', 'GeneSet': 'HALLMARK_APOPTOSIS', 'Collection': 'H', 'Description': '...'}, ...]
```

## Feature Comparison Matrix

| Feature | KEGG | GO | MSigDB |
|---------|------|-----|--------|
| **Filter by description** | ✅ `pathway_name` | ✅ `term_name` | ✅ `gene_set_name`, `description` |
| **Case-insensitive** | ✅ | ✅ | ✅ |
| **Substring matching** | ✅ | ✅ | ✅ |
| **Filter by gene symbol** | ✅ | ✅ | ✅ |
| **Filter by ID** | ✅ `pathway_ids` | ✅ `go_ids` | ✅ `gene_set_id` (via query) |
| **Filter by category** | ❌ | ✅ `namespace`/`aspect` | ✅ `collection` |
| **Filter by quality** | ❌ | ✅ `evidence_codes` | ❌ |
| **Filter by organism** | ✅ | ❌ (set at download) | ✅ |
| **DataFrame export** | ✅ | ✅ | ✅ |
<<<<<<< HEAD
| **Setup required** | ❌ None | ⚠️ Run `populate_term_names()` once | ❌ None |
=======
| **Setup required** | ❌ None | ✅ Automatic (v0.2.0+) | ❌ None |
>>>>>>> 0ad8423 (revise function)

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

# MSigDB: By gene set name
apoptosis_genes = msigdb.filter(
    gene_set_name='apoptosis',
    collection='H'
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

# MSigDB: Gene sets containing TP53
tp53_sets = msigdb.filter(gene_symbols=['TP53'])
```

### 3. High-Quality Annotations Only

```python
# GO: Experimental evidence only
exp_annotations = go.filter(
    term_name='transcription',
    evidence_codes=['EXP', 'IDA', 'IPI', 'IMP']
)

# MSigDB: Hallmark gene sets (highly curated)
hallmark_sets = msigdb.filter(collection='H')
```

### 4. Export for Enrichment Analysis

```python
# KEGG
kegg_data = kegg.to_dataframe()
import pandas as pd
kegg_df = pd.DataFrame(kegg_data)

# GO
go_data = go.to_dataframe()
go_df = pd.DataFrame(go_data)

# MSigDB
msigdb_data = msigdb.to_dataframe(collection='H')
msigdb_df = pd.DataFrame(msigdb_data)

# Use with your enrichment tool
# enrichment_analysis(kegg_df, gene_list)
```

## DataFrame Export Formats

### KEGG DataFrame

```python
data = kegg.to_dataframe()
# [
#   {'GeneID': 'TP53', 'PATH': 'hsa05200', 'Annot': 'Pathways in cancer'},
#   {'GeneID': 'TP53', 'PATH': 'hsa04115', 'Annot': 'p53 signaling pathway'},
#   ...
# ]
```

### GO DataFrame

```python
data = go.to_dataframe()
# [
#   {'GeneID': 'TP53', 'TERM': 'GO:0006281', 'Aspect': 'P', 'Evidence': 'IDA'},
#   {'GeneID': 'TP53', 'TERM': 'GO:0006915', 'Aspect': 'P', 'Evidence': 'TAS'},
#   ...
# ]
```

### MSigDB DataFrame

```python
data = msigdb.to_dataframe(collection='H')
# [
#   {'GeneID': 'TP53', 'GeneSet': 'HALLMARK_APOPTOSIS', 'Collection': 'H', 'Description': 'Genes mediating...'},
#   {'GeneID': 'TP53', 'GeneSet': 'HALLMARK_P53_PATHWAY', 'Collection': 'H', 'Description': 'Genes involved in...'},
#   ...
# ]
```

## Side-by-Side Examples

### Finding Cancer-Related Annotations

```python
from pathwaydb import KEGG, GO, MSigDB

# KEGG: Cancer pathways
kegg = KEGG(species='hsa', storage_path='kegg_human.db')
kegg.download_annotations()
cancer_kegg = kegg.filter(pathway_name='cancer')
print(f"KEGG: {len(cancer_kegg)} cancer pathway annotations")

# GO: Cancer-related terms
go = GO(storage_path='go_human.db')
go.download_annotations(species='human')
go.populate_term_names()
cancer_go = go.filter(term_name='cancer')
print(f"GO: {len(cancer_go)} cancer term annotations")

# MSigDB: Cancer gene sets
msigdb = MSigDB(storage_path='msigdb.db')
msigdb.download_collection('H')
cancer_msigdb = msigdb.filter(gene_set_name='cancer')
print(f"MSigDB: {len(cancer_msigdb)} cancer gene sets")
```

### Finding TP53 Functions Across Databases

```python
# KEGG pathways
tp53_kegg = kegg.filter(gene_symbols=['TP53'])
print(f"TP53 in {len(tp53_kegg)} KEGG pathway annotations")

# GO terms
tp53_go = go.filter(gene_symbols=['TP53'])
print(f"TP53 in {len(tp53_go)} GO term annotations")

# MSigDB gene sets
tp53_msigdb = msigdb.filter(gene_symbols=['TP53'])
print(f"TP53 in {len(tp53_msigdb)} MSigDB gene sets")

# GO terms with high-quality evidence
tp53_go_exp = go.filter(
    gene_symbols=['TP53'],
    evidence_codes=['EXP', 'IDA']
)
print(f"TP53 in {len(tp53_go_exp)} GO terms (experimental evidence)")
```

## Tips and Best Practices

### General

1. **Use broad search terms** - 'cancer' matches many variants
2. **Case doesn't matter** - 'cancer', 'Cancer', 'CANCER' all work
3. **Combine filters** - Mix criteria for precise results
4. **Export to DataFrame** - Use for enrichment analysis and integration with pandas/R

### KEGG-Specific

- No setup required - works immediately after download
- Pathway names are descriptive (e.g., "Pathways in cancer")

### GO-Specific

<<<<<<< HEAD
- **IMPORTANT**: Run `populate_term_names()` once for term name filtering
- Use specific terms - 'DNA repair' is better than just 'repair'
- Combine with evidence codes for high-quality annotations
- Use namespace to filter by biological_process, molecular_function, cellular_component
=======
- **v0.2.0+**: Term names are automatically fetched during download (no manual step needed!)
- Use specific terms - 'DNA repair' is better than just 'repair'
- Combine with evidence codes for high-quality annotations
- Use namespace to filter by biological_process, molecular_function, cellular_component
- For old databases: Run `go.populate_term_names()` to add term names
>>>>>>> 0ad8423 (revise function)

### MSigDB-Specific

- Download collections separately (H, C1, C2, etc.)
- Hallmark (H) gene sets are highly curated and recommended
- C2 contains KEGG, Reactome, and BioCarta pathways
- Use `gene_set_name` for the set name, `description` for the description text

## Performance

| Operation | KEGG | GO | MSigDB |
|-----------|------|-----|--------|
| **Initial download** | ~2 min | ~3-5 min | ~1-2 min per collection |
| **Populate descriptions** | N/A (built-in) | ~2-5 min (one-time) | N/A (built-in) |
| **Filtering queries** | Milliseconds | Milliseconds | Milliseconds |
| **Storage size** | ~8 MB | ~50 MB | ~5-10 MB per collection |

## Summary

PathwayDB provides **consistent, intuitive filtering** across all three major annotation databases:

```python
# KEGG - No setup required
kegg.filter(pathway_name='cancer')

<<<<<<< HEAD
# GO - One-time setup
go.populate_term_names()  # Run once
go.filter(term_name='DNA repair')  # Then use forever
=======
# GO - Automatic setup (v0.2.0+)
go.download_annotations(species='human')  # Term names fetched automatically
go.filter(term_name='DNA repair')
>>>>>>> 0ad8423 (revise function)

# MSigDB - No setup required
msigdb.filter(gene_set_name='apoptosis')
```

<<<<<<< HEAD
=======
**What's New in v0.2.0:**
- ✅ GO term names are **automatically fetched** during download
- ✅ No separate `populate_term_names()` step needed
- ✅ Consistent, zero-setup experience across all databases

>>>>>>> 0ad8423 (revise function)
All databases support:
- Case-insensitive substring matching
- Filtering by gene symbols
- Combined multi-criteria queries
- DataFrame export for enrichment analysis

**No need to remember IDs - just search by description!** 🎉
