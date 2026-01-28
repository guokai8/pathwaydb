#!/usr/bin/env python3
"""
Prepare GO term name mapping for packaging.

<<<<<<< HEAD
This script fetches all GO term names and creates a lightweight mapping file
that can be bundled with the package. Users get instant term name access
without downloading the full GO database or calling QuickGO API.
=======
This script downloads the GO OBO file and creates a lightweight JSON mapping
that can be bundled with the package. Users get instant term name access
without downloading the full GO database or calling any API.
>>>>>>> 0ad8423 (revise function)

Usage:
    python scripts/prepare_go_term_names.py
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

<<<<<<< HEAD
from urllib.request import urlopen, Request
from time import sleep


def fetch_all_go_terms(output_path: Path):
    """
    Fetch all GO terms and their names from QuickGO API.
=======

def fetch_all_go_terms_from_obo(output_path: Path):
    """
    Fetch all GO terms and their names from GO OBO file.

    This is faster and more reliable than QuickGO API.
>>>>>>> 0ad8423 (revise function)

    Args:
        output_path: Path to save the JSON mapping file
    """
<<<<<<< HEAD
    print("=" * 70)
    print("Fetching GO Term Names from QuickGO API")
    print("=" * 70)

    # QuickGO API endpoint to get all GO terms
    base_url = "https://www.ebi.ac.uk/QuickGO/services/ontology/go/terms"

    print(f"\nStep 1: Fetching GO term list...")

    # Get all GO terms (this returns a paginated list)
    # We'll fetch terms in batches
    all_terms = {}
    page = 1
    page_size = 100

    while True:
        url = f"{base_url}?page={page}&limit={page_size}"

        try:
            request = Request(url, headers={
                'Accept': 'application/json',
                'User-Agent': 'pathwaydb/0.2.0'
            })

            with urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))

            results = data.get('results', [])
            if not results:
                break

            # Extract GO ID -> name mappings
            for term in results:
                go_id = term.get('id', '')
                name = term.get('name', '')
                if go_id and name:
                    all_terms[go_id] = name

            print(f"  Page {page}: {len(results)} terms (total: {len(all_terms)})")
            page += 1

            # Rate limiting
            sleep(0.1)

        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break

    print(f"\n✓ Fetched {len(all_terms):,} GO terms")
=======
    from pathwaydb.storage.go_db import download_go_obo

    print("=" * 70)
    print("Fetching GO Term Names from OBO File")
    print("=" * 70)

    print(f"\nStep 1: Downloading and parsing GO OBO file...")
    all_terms = download_go_obo()

    print(f"\n✓ Parsed {len(all_terms):,} GO terms")
>>>>>>> 0ad8423 (revise function)

    # Save to JSON
    print(f"\nStep 2: Saving to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
<<<<<<< HEAD
        json.dump(all_terms, f, indent=2, ensure_ascii=False)
=======
        json.dump(all_terms, f, separators=(',', ':'), ensure_ascii=False)
>>>>>>> 0ad8423 (revise function)

    file_size = output_path.stat().st_size / 1024
    print(f"✓ Saved {len(all_terms):,} terms to {output_path}")
    print(f"  File size: {file_size:.1f} KB")

    # Sample terms
    print(f"\nSample terms:")
<<<<<<< HEAD
    for i, (go_id, name) in enumerate(list(all_terms.items())[:5]):
=======
    sample_ids = ['GO:0006281', 'GO:0006974', 'GO:0007049', 'GO:0008150', 'GO:0003674']
    for go_id in sample_ids:
        name = all_terms.get(go_id, 'NOT FOUND')
>>>>>>> 0ad8423 (revise function)
        print(f"  {go_id}: {name}")

    return all_terms


def main():
    # Output path
    script_dir = Path(__file__).parent
    package_dir = script_dir.parent / 'pathwaydb'
    data_dir = package_dir / 'data'
    output_path = data_dir / 'go_term_names.json'

    print(f"Output file: {output_path}\n")

    # Fetch and save
<<<<<<< HEAD
    terms = fetch_all_go_terms(output_path)
=======
    terms = fetch_all_go_terms_from_obo(output_path)
>>>>>>> 0ad8423 (revise function)

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"""
✓ GO term name mapping prepared successfully!

File: {output_path}
Size: {output_path.stat().st_size / 1024:.1f} KB
Terms: {len(terms):,}

This lightweight file will be bundled with the package.
Users will get instant term name access without:
  • Downloading full GO database
  • Calling QuickGO API

Next steps:
  1. Commit {output_path.name} to git
  2. Build package: python setup.py bdist_wheel
  3. Users get term names automatically!
""")


if __name__ == '__main__':
    main()
