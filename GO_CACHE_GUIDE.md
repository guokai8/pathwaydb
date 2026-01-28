# GO Annotation Caching Guide

## Overview

PathwayDB now supports **centralized GO annotation caching**! Download GO annotations once and reuse them across all your projects.

**Benefits:**
- ✅ Download once, use everywhere
- ✅ Saves disk space (no duplicate databases)
- ✅ Faster project setup (instant loading from cache)
- ✅ Automatic term name fetching included
- ✅ Perfect for HPC clusters and offline work

## Cache Location

GO annotations are cached at:
```
~/.pathwaydb_cache/go_annotations/go_{species}_cached.db
```

For example:
- Human: `~/.pathwaydb_cache/go_annotations/go_human_cached.db`
- Mouse: `~/.pathwaydb_cache/go_annotations/go_mouse_cached.db`
- Rat: `~/.pathwaydb_cache/go_annotations/go_rat_cached.db`

## Quick Start

### Method 1: Using GO.from_cache() (Recommended)

The easiest way to use cached annotations:

```python
from pathwaydb import GO

# Load from cache (auto-downloads if not cached)
go = GO.from_cache(species='human')

# Query immediately
annotations = go.filter(gene_symbols=['TP53'])
print(f"Found {len(annotations)} TP53 annotations")

# Filter by term name (term names included in cache)
dna_repair = go.filter(term_name='DNA repair')
```

### Method 2: Using storage functions directly

For more control over caching:

```python
from pathwaydb import download_to_cache, load_from_cache

# Download to cache once
download_to_cache(species='human', fetch_term_names=True)

# Load from cache in any project
db = load_from_cache(species='human')
annotations = db.filter(gene_symbols=['TP53'])
```

### Method 3: Copy cache to project database

Create an independent project database from cache:

```python
from pathwaydb import copy_from_cache

# Copy cache to local database
db = copy_from_cache(species='human', output_path='my_project_go.db')

# Now you have a local copy
annotations = db.filter(gene_symbols=['TP53'])
```

## Usage Patterns

### Pattern 1: Direct cache queries (Fastest)

Best for: Quick queries, scripts, exploratory analysis

```python
from pathwaydb import GO

# Always use the same cache
go = GO.from_cache(species='human')

# Query
tp53_annotations = go.filter(gene_symbols=['TP53'])
brca1_dna = go.filter(gene_symbols=['BRCA1'], term_name='DNA')
dna_repair = go.filter(term_name='DNA repair')
```

**Pros:**
- Fastest (no copying)
- Uses shared cache (saves disk space)
- Always up-to-date

**Cons:**
- Shared cache might be updated by other processes

### Pattern 2: Copy to project database (Isolated)

Best for: Long-term projects, when you need a stable snapshot

```python
from pathwaydb import copy_from_cache

# Create independent project database
db = copy_from_cache(species='human', output_path='my_analysis.db')

# Query from project database
annotations = db.filter(gene_symbols=['TP53'])
```

**Pros:**
- Independent database (won't change)
- Can modify without affecting cache
- Portable (can share the .db file)

**Cons:**
- Uses more disk space
- Won't get cache updates automatically

### Pattern 3: Pre-download for offline work

Best for: HPC clusters, air-gapped systems, batch processing

```python
from pathwaydb import download_to_cache

# Pre-download all species you need
download_to_cache(species='human')
download_to_cache(species='mouse')
download_to_cache(species='rat')

# Now available offline!
# Later, in scripts:
from pathwaydb import GO
go_human = GO.from_cache(species='human')
go_mouse = GO.from_cache(species='mouse')
```

## API Reference

### download_to_cache()

Download GO annotations to centralized cache.

```python
from pathwaydb import download_to_cache

cache_path = download_to_cache(
    species='human',              # Species: 'human', 'mouse', 'rat'
    evidence_codes=None,          # Optional: filter by evidence codes
    fetch_term_names=True,        # Include term names (default: True)
    force_refresh=False           # Re-download if True
)

print(f"Cached at: {cache_path}")
```

**Returns:** Path to the cached database file

**Example:**
```python
# Download human GO annotations with term names
download_to_cache(species='human')

# Download mouse GO annotations, experimental evidence only
download_to_cache(
    species='mouse',
    evidence_codes=['EXP', 'IDA', 'IPI', 'IMP']
)

# Re-download to update cache
download_to_cache(species='human', force_refresh=True)
```

### load_from_cache()

Load GO annotations from cache (auto-downloads if missing).

```python
from pathwaydb import load_from_cache

db = load_from_cache(species='human')

# Query
annotations = db.filter(gene_symbols=['TP53'])
```

**Returns:** GOAnnotationDB instance connected to cache

### copy_from_cache()

Copy cache to a project-specific database.

```python
from pathwaydb import copy_from_cache

db = copy_from_cache(
    species='human',
    output_path='my_project.db',
    download_if_missing=True     # Auto-download if cache missing
)

# Now you have an independent copy
annotations = db.filter(gene_symbols=['TP53'])
```

**Returns:** GOAnnotationDB instance connected to the copied database

### get_cache_path()

Get the cache file path for a species.

```python
from pathwaydb import get_cache_path

cache_path = get_cache_path(species='human')
print(f"Cache location: {cache_path}")
# ~/.pathwaydb_cache/go_annotations/go_human_cached.db
```

### GO.from_cache()

Create GO instance using cached annotations.

```python
from pathwaydb import GO

go = GO.from_cache(species='human', cache_dir=None)

# Query using GO connector methods
annotations = go.filter(gene_symbols=['TP53'])
brca1_dna = go.filter(gene_symbols=['BRCA1'], term_name='DNA')
```

**Returns:** GO instance connected to cached database

## Advanced Usage

### Checking if cache exists

```python
from pathwaydb import get_cache_path
from pathlib import Path

cache_path = get_cache_path(species='human')
if Path(cache_path).exists():
    print("Cache exists!")
else:
    print("Cache not found, will be downloaded")
```

### Getting cache statistics

```python
from pathwaydb import load_from_cache

db = load_from_cache(species='human')
stats = db.stats()

print(f"Total annotations: {stats['total_annotations']:,}")
print(f"Unique genes: {stats['unique_genes']:,}")
print(f"Unique GO terms: {stats['unique_terms']:,}")
```

### Using cache in multiple projects

Project 1:
```python
# project1/analysis.py
from pathwaydb import GO

go = GO.from_cache(species='human')
tp53 = go.filter(gene_symbols=['TP53'])
```

Project 2:
```python
# project2/script.py
from pathwaydb import GO

go = GO.from_cache(species='human')
# Uses the same cache - no re-download!
brca1 = go.filter(gene_symbols=['BRCA1'])
```

### Updating cache

```python
from pathwaydb import download_to_cache

# Update cache with latest GO annotations
download_to_cache(species='human', force_refresh=True)
```

## Migration from Project-Specific Databases

**Old approach (each project downloads separately):**
```python
# Project 1
go1 = GO(storage_path='project1_go.db')
go1.download_annotations(species='human')  # Downloads

# Project 2
go2 = GO(storage_path='project2_go.db')
go2.download_annotations(species='human')  # Downloads again!
```

**New approach (shared cache):**
```python
# One-time setup (run once on your machine)
from pathwaydb import download_to_cache
download_to_cache(species='human')  # Download once

# Project 1
from pathwaydb import GO
go1 = GO.from_cache(species='human')  # Instant!

# Project 2
go2 = GO.from_cache(species='human')  # Also instant!
```

**To migrate existing databases:**
```python
# If you have old project databases, you can delete them
# and use the cache instead

# Old way:
# go = GO(storage_path='old_project.db')

# New way:
go = GO.from_cache(species='human')

# Delete old database to save space
# rm old_project.db
```

## Best Practices

### 1. Use from_cache() for most cases

```python
from pathwaydb import GO

go = GO.from_cache(species='human')
# Simple, fast, and uses shared cache
```

### 2. Copy cache for long-term projects

```python
from pathwaydb import copy_from_cache

# Create stable snapshot for your project
db = copy_from_cache(species='human', output_path='my_study.db')
```

### 3. Pre-download for offline/HPC work

```python
# On a machine with internet:
from pathwaydb import download_to_cache

download_to_cache(species='human')
download_to_cache(species='mouse')

# Transfer ~/.pathwaydb_cache/ to HPC
# Now use offline!
```

### 4. Update cache periodically

```python
from pathwaydb import download_to_cache

# Update monthly to get latest GO annotations
download_to_cache(species='human', force_refresh=True)
```

## Cache vs. Project Database Comparison

| Feature | Shared Cache | Project Database |
|---------|--------------|------------------|
| **Setup** | Instant (after first download) | Need to download per project |
| **Disk space** | Minimal (one copy) | More (copy per project) |
| **Updates** | Update cache, all projects benefit | Update each project separately |
| **Isolation** | Shared across projects | Independent per project |
| **Portability** | Need cache on each machine | Can share .db file directly |
| **Best for** | Scripts, exploration, multiple projects | Long-term studies, snapshots |

## Troubleshooting

### Cache not found

If you get "Cache not found", it will auto-download:

```python
from pathwaydb import GO

go = GO.from_cache(species='human')
# If cache doesn't exist, will download automatically
```

### Force re-download

To update cache or fix corrupted cache:

```python
from pathwaydb import download_to_cache

download_to_cache(species='human', force_refresh=True)
```

### Check cache size

```bash
# Check cache directory size
du -sh ~/.pathwaydb_cache/go_annotations/

# List cached species
ls -lh ~/.pathwaydb_cache/go_annotations/
```

### Clear cache

To free up space:

```bash
# Remove all GO annotation caches
rm -rf ~/.pathwaydb_cache/go_annotations/

# Remove specific species
rm ~/.pathwaydb_cache/go_annotations/go_human_cached.db
```

## Summary

PathwayDB's centralized GO annotation caching provides:

- ✅ **One-time download** - Download once, use everywhere
- ✅ **Automatic term names** - Term names included in cache
- ✅ **Disk space savings** - One cache for all projects
- ✅ **Faster project setup** - Instant loading from cache
- ✅ **Offline support** - Pre-download for HPC/offline work
- ✅ **Flexible usage** - Direct cache queries or project copies

**Recommended workflow:**

```python
# 1. Download to cache (once)
from pathwaydb import download_to_cache
download_to_cache(species='human')

# 2. Use in any project (instant)
from pathwaydb import GO
go = GO.from_cache(species='human')

# 3. Query as normal
annotations = go.filter(gene_symbols=['TP53'], term_name='DNA')
```

🎉 Download once, use everywhere!
