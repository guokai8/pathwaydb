# GO Term Name Filtering Guide

## Overview

PathwayDB now supports filtering GO annotations by term name/description, just like KEGG pathway name filtering!

## Quick Start

```python
from pathwaydb import GO

# Initialize GO with storage
go = GO(storage_path='go_human.db')

<<<<<<< HEAD
# Step 1: Download annotations (if not already done)
go.download_annotations(species='human')

# Step 2: Populate term names from QuickGO API
go.populate_term_names()  # This is the KEY step!

# Step 3: Filter by term name
=======
# Download annotations (term names are fetched automatically!)
go.download_annotations(species='human')

# Filter by term name - it just works!
>>>>>>> 0ad8423 (revise function)
dna_repair = go.filter(term_name='DNA repair')
apoptosis = go.filter(term_name='apoptosis')
transcription = go.filter(term_name='transcription')
```

<<<<<<< HEAD
=======
**Note:** Term names are now **automatically fetched** during `download_annotations()` by default! No separate step needed.

>>>>>>> 0ad8423 (revise function)
## Why This Feature?

**Before:** You had to know GO IDs to filter
```python
# Hard to remember IDs
dna_repair = go.filter(go_ids=['GO:0006281'])
```

**Now:** You can search by description
```python
# Much more intuitive!
dna_repair = go.filter(term_name='DNA repair')
```

## How It Works

<<<<<<< HEAD
1. **Download Annotations**: Gets gene-to-GO mappings (GO IDs only)
2. **Populate Term Names**: Fetches GO term descriptions from QuickGO API
3. **Filter**: Search by substring match in term names

=======
1. **Download Annotations**: Gets gene-to-GO mappings from GAF files (GO IDs only)
2. **Fetch Term Names** (Automatic): Fetches GO term descriptions from QuickGO API
3. **Filter**: Search by substring match in term names

**New in v0.2.0:** Term names are automatically fetched during download by default! The `populate_term_names()` method is now called automatically unless you set `fetch_term_names=False`.

>>>>>>> 0ad8423 (revise function)
## Usage Examples

### Basic Filtering

```python
from pathwaydb import GO

go = GO(storage_path='go_human.db')

# Find all DNA-related terms
dna_terms = go.filter(term_name='DNA')

# Find cell cycle terms
cell_cycle = go.filter(term_name='cell cycle')

# Find binding-related terms
binding = go.filter(term_name='binding')
```

### Combine with Other Filters

```python
# TP53 + apoptosis terms
tp53_apoptosis = go.filter(
    gene_symbols=['TP53'],
    term_name='apoptosis'
)

# Biological processes + DNA
dna_processes = go.filter(
    namespace='biological_process',
    term_name='DNA'
)

# Experimental evidence + transcription
transcription_exp = go.filter(
    term_name='transcription',
    evidence_codes=['EXP', 'IDA', 'IPI']
)

# Multiple criteria
specific = go.filter(
    gene_symbols=['BRCA1'],
    namespace='biological_process',
    term_name='DNA repair',
    evidence_codes=['EXP', 'TAS']
)
```

### Common Searches

```python
# DNA-related
dna = go.filter(term_name='DNA')
dna_repair = go.filter(term_name='DNA repair')
dna_replication = go.filter(term_name='DNA replication')

# Cell processes
apoptosis = go.filter(term_name='apoptosis')
cell_cycle = go.filter(term_name='cell cycle')
cell_death = go.filter(term_name='cell death')

# Transcription and translation
transcription = go.filter(term_name='transcription')
translation = go.filter(term_name='translation')
gene_expression = go.filter(term_name='gene expression')

# Signaling
signaling = go.filter(term_name='signaling')
signal_transduction = go.filter(term_name='signal transduction')

# Metabolism
metabolism = go.filter(term_name='metabolism')
metabolic_process = go.filter(term_name='metabolic process')

# Immune
immune = go.filter(term_name='immune')
immune_response = go.filter(term_name='immune response')
```

## Features

✅ **Case-Insensitive**: 'DNA', 'dna', 'Dna' all work
✅ **Substring Matching**: 'repair' matches 'DNA repair', 'mismatch repair', etc.
✅ **Combinable**: Works with all other filter parameters
✅ **Fast**: Uses indexed database queries

## Comparison: KEGG vs GO Filtering

| Feature | KEGG | GO |
|---------|------|-----|
| Filter by name/description | ✅ `pathway_name='cancer'` | ✅ `term_name='DNA repair'` |
| Case-insensitive | ✅ | ✅ |
| Substring matching | ✅ | ✅ |
| Filter by category | ❌ | ✅ `namespace='biological_process'` |
| Quality filtering | ❌ | ✅ `evidence_codes=['EXP']` |

## Technical Details

### Database Schema

The GO database now includes a `term_name` column:

```sql
CREATE TABLE go_annotations (
    gene_id TEXT,
    gene_symbol TEXT,
    go_id TEXT,
    evidence_code TEXT,
    aspect TEXT,
    term_name TEXT,  -- NEW!
    PRIMARY KEY (gene_id, go_id)
);

CREATE INDEX idx_term_name ON go_annotations(term_name);
```

### populate_term_names() Method

This method:
1. Queries all unique GO IDs from the database
2. Fetches term names from QuickGO API in batches
3. Updates the `term_name` column for each annotation
4. Uses rate limiting to be respectful to the API

```python
# Under the hood
go.populate_term_names()
# Fetches from: https://www.ebi.ac.uk/QuickGO/services/ontology/go/terms/{GO_IDs}
```

### Performance

- **First time**: Downloads term names (~2-5 minutes for all unique terms)
- **Subsequent uses**: Instant (data is cached in database)
- **Filtering**: Fast indexed search

## Best Practices

<<<<<<< HEAD
### 1. Populate Term Names Once

```python
# Do this once when setting up
go = GO(storage_path='go_human.db')
go.download_annotations(species='human')
go.populate_term_names()  # Takes a few minutes
=======
### 1. Download Once, Query Forever

```python
# Do this once when setting up (term names fetched automatically)
go = GO(storage_path='go_human.db')
go.download_annotations(species='human')  # Fetches term names automatically
>>>>>>> 0ad8423 (revise function)

# Then use the database forever
go2 = GO(storage_path='go_human.db')
results = go2.filter(term_name='DNA repair')  # Instant!
```

<<<<<<< HEAD
=======
### 1b. Skip Automatic Term Name Fetching (Advanced)

If you want to skip term name fetching and do it later:

```python
# Skip automatic term name fetching
go = GO(storage_path='go_human.db')
go.download_annotations(species='human', fetch_term_names=False)

# Fetch term names later (optional)
go.populate_term_names()
```

>>>>>>> 0ad8423 (revise function)
### 2. Use Specific Terms

```python
# Too broad (millions of results)
results = go.filter(term_name='regulation')

# More specific (better results)
results = go.filter(term_name='regulation of transcription')
results = go.filter(term_name='positive regulation of apoptosis')
```

### 3. Combine with Other Filters

```python
# Narrow down results
results = go.filter(
    term_name='DNA',
    namespace='biological_process',  # Only processes
    evidence_codes=['EXP', 'IDA']     # High quality only
)
```

## Troubleshooting

### "term_name is NULL"

<<<<<<< HEAD
You forgot to run `populate_term_names()`:

```python
go = GO(storage_path='go_human.db')
go.download_annotations(species='human')
go.populate_term_names()  # Don't forget this!
```

=======
This happens if you either:
1. Downloaded annotations before v0.2.0 (when term names weren't automatic)
2. Explicitly disabled term name fetching with `fetch_term_names=False`

**Solution:** Manually populate term names:

```python
go = GO(storage_path='go_human.db')
go.populate_term_names()  # Fetches and saves term names
```

This updates your existing database with term names without re-downloading all annotations.

>>>>>>> 0ad8423 (revise function)
### No Results Found

Try broader search terms:

```python
# Too specific - might not match
results = go.filter(term_name='DNA double-strand break repair via homologous recombination')

# Better - use substring
results = go.filter(term_name='DNA repair')
results = go.filter(term_name='homologous recombination')
```

### Slow populate_term_names()

This is normal for the first run. It's fetching data for thousands of unique GO terms. The data is cached, so subsequent uses are instant.

## Summary

GO term name filtering makes PathwayDB much more user-friendly:

**Before:**
```python
# Hard to use - need to know GO IDs
dna_repair = go.filter(go_ids=['GO:0006281'])
```

<<<<<<< HEAD
**After:**
```python
# Easy and intuitive!
=======
**After (v0.2.0+):**
```python
# Easy and intuitive - term names are automatic!
go = GO(storage_path='go_human.db')
go.download_annotations(species='human')  # Term names included automatically

>>>>>>> 0ad8423 (revise function)
dna_repair = go.filter(term_name='DNA repair')
apoptosis = go.filter(term_name='apoptosis')
tp53_dna = go.filter(gene_symbols=['TP53'], term_name='DNA')
```

<<<<<<< HEAD
=======
**Key Points:**
- ✅ Term names are **automatically fetched** during download (no separate step needed!)
- ✅ Just like KEGG pathway name filtering - consistent API across all databases
- ✅ Can still use `populate_term_names()` manually if needed (e.g., updating old databases)

>>>>>>> 0ad8423 (revise function)
Now GO filtering is as easy as KEGG pathway name filtering! 🎉
