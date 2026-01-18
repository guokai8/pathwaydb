# PathwayDB Package Data

This directory contains lightweight data files bundled with the PathwayDB package.

## go_term_names.json

**Size:** ~1-2 MB
**Purpose:** GO ID → term name mapping

This file provides instant term name access without:
- Downloading full GO databases
- Calling QuickGO API (slow)
- Large package sizes

When users download GO annotations, term names are automatically populated from this bundled mapping.

### How It Works

1. User installs pathwaydb package
2. GO term name mapping is already included
3. User downloads GO annotations:
   ```python
   from pathwaydb import GO
   go = GO(storage_path='go_human.db')
   go.download_annotations(species='human')
   # Term names populated automatically from bundled data!
   ```

4. Query with term names immediately:
   ```python
   dna_repair = go.filter(term_name='DNA repair')  # Works instantly!
   ```

## Updating the Mapping

To update the GO term name mapping before releasing a new version:

```bash
# Run the preparation script
python scripts/prepare_go_term_names.py

# This fetches all current GO terms from QuickGO API
# and updates pathwaydb/data/go_term_names.json

# Commit the updated file
git add pathwaydb/data/go_term_names.json
git commit -m "Update GO term names"
```

## go_annotations/ (Optional)

This directory can optionally contain full GO annotation databases if you want to bundle them:

- `go_human.db` (~50 MB) - Human GO annotations with term names
- `go_mouse.db` (~40 MB) - Mouse GO annotations with term names
- `go_rat.db` (~30 MB) - Rat GO annotations with term names

**Note:** These large files are NOT included by default to keep package size small.
Only `go_term_names.json` is bundled.

To prepare full databases (optional):
```bash
python scripts/prepare_package_data.py --species human
```
