# PathwayDB Packaging Guide

## Overview

PathwayDB can be packaged with **pre-downloaded GO annotation data**, providing users instant access without any downloads!

## Packaging Options

### Option 1: Package WITHOUT Bundled Data (Lightweight)

**Package size:** ~50 KB (code only)
**User experience:** Downloads GO data on first use (~5 minutes)

This is the default. Just build the package:

```bash
python setup.py sdist bdist_wheel
```

Users will download data when needed:
```python
from pathwaydb import GO

# Downloads on first use
go = GO.from_cache(species='human')
```

### Option 2: Package WITH Bundled Data (Recommended)

**Package size:** ~50-150 MB (depending on species included)
**User experience:** Instant, zero downloads required!

#### Step 1: Prepare GO Annotation Data

Run the preparation script to download and prepare GO data:

```bash
# Prepare human GO annotations only
python scripts/prepare_package_data.py --species human

# Prepare multiple species
python scripts/prepare_package_data.py --species human mouse

# Prepare all supported species
python scripts/prepare_package_data.py --all
```

This downloads GO annotations with term names to `pathwaydb/data/go_annotations/`:

```
pathwaydb/data/go_annotations/
├── go_human.db    (~50 MB)
├── go_mouse.db    (~40 MB)
└── go_rat.db      (~30 MB)
```

#### Step 2: Build Package with Data

```bash
# Build source and wheel distributions
python setup.py sdist bdist_wheel

# The .whl and .tar.gz files will include the data
```

#### Step 3: Install and Use

Users install the package normally:

```bash
pip install pathwaydb-0.2.0-py3-none-any.whl
```

And get instant access to bundled data:

```python
from pathwaydb import GO

# Uses bundled data - instant, no download!
go = GO.load(species='human')

# Or explicitly use package data
go = GO.from_package_data(species='human')

# Query immediately
annotations = go.filter(gene_symbols=['TP53'])
```

## Package Size Considerations

| Species Included | Package Size | Download Time | Use Case |
|-----------------|--------------|---------------|----------|
| None (code only) | ~50 KB | N/A | Users download as needed |
| Human only | ~50 MB | ~10 sec on fast connection | Most common use case |
| Human + Mouse | ~90 MB | ~20 sec | Multi-species research |
| All (Human + Mouse + Rat) | ~120 MB | ~30 sec | Comprehensive package |

**Recommendation:** Include human GO annotations by default (most commonly used).

## User Experience Comparison

### WITHOUT Bundled Data

```python
from pathwaydb import GO

# First time - downloads data (~5 min)
go = GO.load(species='human')
print("Downloading GO annotations...")
# ... downloads from Gene Ontology ...

# Second time - uses cache (instant)
go = GO.load(species='human')  # ⚡ Instant
```

### WITH Bundled Data

```python
from pathwaydb import GO

# First time - uses bundled data (instant)
go = GO.load(species='human')  # ⚡ Instant

# Always instant!
go = GO.load(species='human')  # ⚡ Instant
```

## Data Freshness

GO annotations are updated regularly by the Gene Ontology Consortium. Consider:

1. **Bundle recent data** - Download fresh data before packaging
2. **Document version** - Note the GO release date in CHANGELOG
3. **Allow updates** - Users can still update via cache if needed

```python
from pathwaydb import download_to_cache

# Users can update cached data
download_to_cache(species='human', force_refresh=True)

# Then use updated cache instead of package data
go = GO.load(species='human', use_package_data=False)
```

## Packaging Workflow (Recommended)

For **release builds** (uploaded to PyPI):

```bash
# 1. Prepare fresh GO data
python scripts/prepare_package_data.py --species human

# 2. Update CHANGELOG with GO data version
echo "GO annotations: $(date +%Y-%m-%d)" >> CHANGELOG.md

# 3. Build package with data
python setup.py sdist bdist_wheel

# 4. Upload to PyPI
twine upload dist/*
```

For **development builds** (testing, local use):

```bash
# Build without data (faster)
python setup.py sdist bdist_wheel
```

## Checking What's Bundled

After building, check what's included:

```bash
# Extract wheel to inspect
unzip -l dist/pathwaydb-0.2.0-py3-none-any.whl | grep "data/go"

# Should show:
# pathwaydb/data/go_annotations/go_human.db
# pathwaydb/data/go_annotations/go_mouse.db
# etc.
```

In Python, check available species:

```python
from pathwaydb.data import list_bundled_species, has_go_data

# List all bundled species
print("Bundled species:", list_bundled_species())
# ['human', 'mouse']

# Check if specific species is bundled
print("Has human data:", has_go_data('human'))  # True
print("Has rat data:", has_go_data('rat'))      # False
```

## .gitignore Configuration

**Important:** The data files are large and should NOT be committed to git!

Update `.gitignore`:

```gitignore
# Data files (too large for git)
pathwaydb/data/go_annotations/*.db

# But keep the directory
!pathwaydb/data/go_annotations/.gitkeep
```

Create a `.gitkeep` file:

```bash
touch pathwaydb/data/go_annotations/.gitkeep
git add pathwaydb/data/go_annotations/.gitkeep
```

## Distribution Strategy

### GitHub Releases

Upload the wheel with bundled data as a GitHub release asset:

```bash
# Build with data
python scripts/prepare_package_data.py --species human
python setup.py bdist_wheel

# Upload to GitHub release
# Users download: pathwaydb-0.2.0-py3-none-any.whl
```

### PyPI

**Consider package size limits:**
- PyPI has a 100 MB file size limit (soft limit, can request increase)
- If bundling all species exceeds limit, bundle human only

```bash
# Human only (~50 MB - fits PyPI)
python scripts/prepare_package_data.py --species human
python setup.py sdist bdist_wheel
twine upload dist/*
```

### Separate Data Package (Advanced)

For very large data, create a separate data package:

```bash
# Main package (code only)
pip install pathwaydb

# Optional data package
pip install pathwaydb-data
```

## Testing Bundled Package

After building, test in a clean environment:

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate

# Install built package
pip install dist/pathwaydb-0.2.0-py3-none-any.whl

# Test bundled data
python -c "
from pathwaydb import GO
from pathwaydb.data import list_bundled_species

print('Bundled species:', list_bundled_species())

go = GO.from_package_data(species='human')
print('Loaded GO data successfully!')

stats = go.stats()
print(f'Total annotations: {stats[\"total_annotations\"]:,}')
"
```

## Best Practices

1. **Bundle human by default** - Most users work with human data
2. **Document what's bundled** - List bundled species in README
3. **Version the data** - Note GO release date in CHANGELOG
4. **Keep separate builds** - Development (no data) vs Release (with data)
5. **Test before release** - Verify bundled data loads correctly
6. **Provide both options** - Users can download other species via cache

## Summary

**For PyPI releases:**
```bash
# Prepare human GO annotations
python scripts/prepare_package_data.py --species human

# Build and upload
python setup.py sdist bdist_wheel
twine upload dist/*
```

**For GitHub releases:**
```bash
# Prepare multiple species
python scripts/prepare_package_data.py --species human mouse

# Build
python setup.py bdist_wheel

# Upload .whl to GitHub release
```

**Users get:**
- Instant access to bundled data (no downloads!)
- Option to download other species via cache
- Option to update data via cache

🎉 **Bundle data = Happy users with zero-setup experience!**
