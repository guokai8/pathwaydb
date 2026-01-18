# GO Term Names Packaging Guide

## Overview

PathwayDB bundles a lightweight **GO ID → term name mapping** (~1-2 MB) with the package, providing users instant term name access without:

- ❌ Downloading full GO databases (~50 MB per species)
- ❌ Calling QuickGO API (slow, requires internet)
- ❌ Large package sizes

## How It Works

### 1. Prepare GO Term Name Mapping (Before Release)

Run this script to fetch all GO term names and create the mapping file:

```bash
python scripts/prepare_go_term_names.py
```

This creates `pathwaydb/data/go_term_names.json` (~1-2 MB):

```json
{
  "GO:0006281": "DNA repair",
  "GO:0006915": "apoptotic process",
  "GO:0008150": "biological_process",
  ...
}
```

### 2. Commit and Build Package

```bash
# Commit the mapping file
git add pathwaydb/data/go_term_names.json
git commit -m "Update GO term names for v0.2.0"

# Build package (includes the JSON file)
python setup.py sdist bdist_wheel
```

### 3. User Experience (Automatic!)

When users install pathwaydb, they get:

```python
from pathwaydb import GO

# Download GO annotations (species-specific gene-GO mappings)
go = GO(storage_path='go_human.db')
go.download_annotations(species='human')

# Term names are automatically populated from bundled data!
# No QuickGO API calls needed!

# Query with term names immediately
dna_repair = go.filter(term_name='DNA repair')  # ⚡ Instant!
apoptosis = go.filter(term_name='apoptosis')

# View term names in results
for ann in dna_repair[:3]:
    print(f"{ann.go_id}: {ann.term_name}")
    # GO:0006281: DNA repair
    # GO:0006974: cellular response to DNA damage stimulus
    # ...
```

## Package Size Comparison

| Approach | Package Size | User Download | Term Names |
|----------|--------------|---------------|------------|
| **No bundled data** | ~50 KB | ~50 MB per species | QuickGO API (~5 min) |
| **Bundle full DB** | ~50 MB | None | Instant |
| **Bundle mapping (recommended)** | ~1-2 MB | ~50 MB per species | Instant (from mapping) |

**Recommended:** Bundle only the GO term name mapping - best balance of package size and user experience.

## Technical Details

### populate_term_names() Method

The method now tries bundled data first, then falls back to QuickGO API:

```python
def populate_term_names(self, use_bundled_data=True):
    # 1. Try bundled mapping (instant)
    if use_bundled_data and has_go_term_names():
        term_names = load_go_term_names()
        # Update all GO terms from mapping
        # ⚡ Instant for ~40,000 GO terms!

    # 2. Fall back to QuickGO API if needed
    # (for new GO terms not in bundled mapping)
```

### Data Freshness

GO consortium releases new GO terms periodically. To keep the mapping current:

```bash
# Before major releases, update the mapping
python scripts/prepare_go_term_names.py

# Check what changed
git diff pathwaydb/data/go_term_names.json

# Commit and release
git add pathwaydb/data/go_term_names.json
git commit -m "Update GO term names to 2026-01 release"
```

### File Size

The JSON mapping contains ~40,000-50,000 GO terms:

```bash
# Check file size
ls -lh pathwaydb/data/go_term_names.json
# ~1.5 MB

# Check term count
python -c "
import json
with open('pathwaydb/data/go_term_names.json') as f:
    terms = json.load(f)
print(f'Terms: {len(terms):,}')
"
# Terms: ~45,000
```

## Workflow

### For Package Maintainers

**Before each release:**

1. Update GO term names:
   ```bash
   python scripts/prepare_go_term_names.py
   ```

2. Verify the update:
   ```bash
   python -c "
   from pathwaydb.data import load_go_term_names
   terms = load_go_term_names()
   print(f'Loaded {len(terms):,} GO term names')
   print(f'Sample: {list(terms.items())[:3]}')
   "
   ```

3. Commit and build:
   ```bash
   git add pathwaydb/data/go_term_names.json
   git commit -m "Update GO term names"
   python setup.py bdist_wheel
   ```

4. Verify in built package:
   ```bash
   unzip -l dist/pathwaydb-0.2.0-py3-none-any.whl | grep go_term_names
   ```

### For Users

**Just install and use** - everything is automatic:

```python
from pathwaydb import GO

# Install package (includes term name mapping)
# pip install pathwaydb

# Download GO annotations
go = GO(storage_path='go_human.db')
go.download_annotations(species='human')

# Term names already populated!
annotations = go.filter(gene_symbols=['TP53'])
for ann in annotations[:5]:
    print(f"{ann.go_id}: {ann.term_name}")
```

## Benefits

### ✅ Small Package Size

- Only ~1-2 MB added to package
- Much smaller than full databases (~150 MB for all species)

### ✅ Fast Term Name Population

- Instant lookup from bundled JSON
- No QuickGO API calls (saves ~5 minutes)
- No internet required for term names

### ✅ Always Available

- Works offline
- No API rate limits
- No network errors

### ✅ Up-to-date

- Can update mapping with each release
- Users get current GO terms

### ✅ Flexible

- Users still download species-specific annotations (updated regularly)
- Term names from stable bundled mapping
- Best of both worlds!

## Summary

**What's bundled:** GO ID → term name mapping (~1-2 MB)

**What users download:** Species-specific gene-GO annotations (~50 MB)

**Result:**
- Small package size ✅
- Instant term name access ✅
- No QuickGO API calls ✅
- Always works offline ✅

**Workflow:**
```bash
# Maintainer (before release)
python scripts/prepare_go_term_names.py
git add pathwaydb/data/go_term_names.json
python setup.py bdist_wheel

# User (after install)
pip install pathwaydb
python -c "
from pathwaydb import GO
go = GO(storage_path='go.db')
go.download_annotations(species='human')  # Term names included!
"
```

🎉 **Lightweight, fast, and works offline!**
