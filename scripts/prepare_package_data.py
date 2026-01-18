#!/usr/bin/env python3
"""
Prepare GO annotation data for packaging.

This script downloads GO annotations and prepares them for inclusion
in the PathwayDB package, so users don't need to download them.

Usage:
    python scripts/prepare_package_data.py --species human mouse
    python scripts/prepare_package_data.py --all
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pathwaydb.storage.go_db import download_go_annotations_filtered
from pathwaydb.connectors.go import GO


def prepare_go_data(species: str, data_dir: Path):
    """
    Download and prepare GO annotation data for a species.

    Args:
        species: Species name ('human', 'mouse', 'rat')
        data_dir: Directory to save data files
    """
    print(f"\n{'='*70}")
    print(f"Preparing GO data for {species}")
    print(f"{'='*70}\n")

    output_path = data_dir / f"go_{species}.db"

    # Download annotations
    print(f"Step 1: Downloading GO annotations for {species}...")
    download_go_annotations_filtered(
        species=species,
        evidence_codes=None,  # Include all evidence codes
        output_path=str(output_path),
        return_db=False
    )

    # Populate term names
    print(f"\nStep 2: Fetching GO term names...")
    go = GO(storage_path=str(output_path))
    go.populate_term_names()

    # Verify
    print(f"\nStep 3: Verifying data...")
    stats = go.stats()
    print(f"  ✓ Total annotations: {stats['total_annotations']:,}")
    print(f"  ✓ Unique genes: {stats['unique_genes']:,}")
    print(f"  ✓ Unique GO terms: {stats['unique_terms']:,}")

    # Check file size
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  ✓ Database size: {file_size_mb:.1f} MB")

    print(f"\n✓ Successfully prepared GO data for {species}")
    print(f"  Location: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare GO annotation data for packaging"
    )
    parser.add_argument(
        '--species',
        nargs='+',
        choices=['human', 'mouse', 'rat'],
        help='Species to prepare data for'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Prepare data for all supported species'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory (default: pathwaydb/data/go_annotations/)'
    )

    args = parser.parse_args()

    # Determine output directory
    if args.output_dir:
        data_dir = Path(args.output_dir)
    else:
        # Use package data directory
        script_dir = Path(__file__).parent
        package_dir = script_dir.parent / 'pathwaydb'
        data_dir = package_dir / 'data' / 'go_annotations'

    # Create directory
    data_dir.mkdir(parents=True, exist_ok=True)

    # Determine species to process
    if args.all:
        species_list = ['human', 'mouse', 'rat']
    elif args.species:
        species_list = args.species
    else:
        print("Error: Must specify --species or --all")
        parser.print_help()
        sys.exit(1)

    print(f"Data will be saved to: {data_dir}")
    print(f"Species to prepare: {', '.join(species_list)}")

    # Prepare data for each species
    for species in species_list:
        try:
            prepare_go_data(species, data_dir)
        except Exception as e:
            print(f"\n✗ Failed to prepare data for {species}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\n{'='*70}")
    print("Summary")
    print(f"{'='*70}\n")

    # List prepared files
    print("Prepared data files:")
    total_size = 0
    for db_file in sorted(data_dir.glob('go_*.db')):
        size_mb = db_file.stat().st_size / (1024 * 1024)
        total_size += size_mb
        species_name = db_file.stem.replace('go_', '')
        print(f"  ✓ {species_name:10s} - {size_mb:6.1f} MB - {db_file}")

    print(f"\nTotal size: {total_size:.1f} MB")
    print(f"\nData location: {data_dir}")
    print("\nNext steps:")
    print("  1. Run 'python setup.py sdist bdist_wheel' to build package with data")
    print("  2. Data will be included in the package distribution")
    print("  3. Users can use GO.from_package_data() or GO.load() to access bundled data")


if __name__ == '__main__':
    main()
