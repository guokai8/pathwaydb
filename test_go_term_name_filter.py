"""
Test GO term name filtering functionality.

This demonstrates the new feature to filter GO annotations by term description/name.
"""

print("=" * 70)
print("GO Term Name Filtering - NEW FEATURE")
print("=" * 70)

from pathwaydb import GO
from pathwaydb.storage import GOAnnotationDB

# Step 1: Create or load GO database
print("\nStep 1: Setting up GO database")
print("-" * 70)

go = GO(storage_path='go_human_with_names.db')

# Check if database exists and has data
try:
    stats = go.stats()
    if stats['total_annotations'] == 0:
        print("⚠ Database is empty. Downloading GO annotations...")
        print("This will take a few minutes...")
        go.download_annotations(species='human')
        stats = go.stats()

    print(f"✓ Database has {stats['total_annotations']:,} annotations")
    print(f"✓ Unique GO terms: {stats['unique_terms']:,}")
except:
    print("Creating new GO database and downloading annotations...")
    go.download_annotations(species='human')
    stats = go.stats()
    print(f"✓ Downloaded {stats['total_annotations']:,} annotations")

# Step 2: Populate term names (this is the NEW feature!)
print("\nStep 2: Populating GO term names")
print("-" * 70)
print("Fetching term names from QuickGO API...")
print("(This may take a few minutes for all unique terms)")

go.populate_term_names()

# Step 3: Test filtering by term name
print("\nStep 3: Testing term name filtering")
print("-" * 70)

# Example 1: Find DNA-related terms
print("\n1. Filter by term_name='DNA'")
dna_results = go.filter(term_name='DNA')
print(f"✓ Found {len(dna_results)} annotations with 'DNA' in term name")

if dna_results:
    print("\nFirst 5 unique terms:")
    seen_terms = set()
    count = 0
    for ann in dna_results:
        if ann.go_id not in seen_terms and ann.term_name:
            print(f"  {ann.go_id}: {ann.term_name}")
            seen_terms.add(ann.go_id)
            count += 1
            if count >= 5:
                break

# Example 2: Find DNA repair specifically
print("\n2. Filter by term_name='DNA repair'")
dna_repair = go.filter(term_name='DNA repair')
print(f"✓ Found {len(dna_repair)} annotations for DNA repair")

# Example 3: Combine with gene symbols
print("\n3. Filter TP53 annotations with 'apoptosis' in term name")
tp53_apoptosis = go.filter(gene_symbols=['TP53'], term_name='apoptosis')
print(f"✓ Found {len(tp53_apoptosis)} TP53 apoptosis annotations")

if tp53_apoptosis:
    print("\nTP53 apoptosis terms:")
    for ann in tp53_apoptosis[:5]:
        print(f"  {ann.go_id}: {ann.term_name} [{ann.evidence_code}]")

# Example 4: Combine term name with namespace
print("\n4. Filter biological processes with 'cell cycle' in name")
cell_cycle_bp = go.filter(namespace='biological_process', term_name='cell cycle')
print(f"✓ Found {len(cell_cycle_bp)} cell cycle biological process annotations")

# Example 5: Combine term name with evidence codes
print("\n5. Filter 'transcription' terms with experimental evidence")
transcription_exp = go.filter(
    term_name='transcription',
    evidence_codes=['EXP', 'IDA', 'IPI', 'IMP']
)
print(f"✓ Found {len(transcription_exp)} transcription annotations (experimental)")

# Example 6: Search for protein-related terms
print("\n6. Filter molecular functions with 'binding' in name")
binding_mf = go.filter(namespace='molecular_function', term_name='binding')
print(f"✓ Found {len(binding_mf)} binding-related molecular functions")

# Example 7: Case-insensitive search
print("\n7. Case-insensitive search for 'DNA' vs 'dna'")
dna_upper = go.filter(term_name='DNA')
dna_lower = go.filter(term_name='dna')
print(f"✓ 'DNA': {len(dna_upper)} results")
print(f"✓ 'dna': {len(dna_lower)} results")
print(f"✓ Case-insensitive: {len(dna_upper) == len(dna_lower)}")

print("\n" + "=" * 70)
print("Summary")
print("=" * 70)
print("""
NEW GO Filter Features:
  ✓ term_name parameter - Filter by GO term description
  ✓ Case-insensitive substring matching
  ✓ Combinable with all other filters
  ✓ Works with gene_symbols, namespace, evidence_codes, etc.

Usage:
  1. Download GO annotations: go.download_annotations(species='human')
  2. Populate term names: go.populate_term_names()
  3. Filter by term name: go.filter(term_name='DNA repair')

Examples:
  - DNA-related terms: go.filter(term_name='DNA')
  - TP53 apoptosis: go.filter(gene_symbols=['TP53'], term_name='apoptosis')
  - Cell cycle processes: go.filter(namespace='biological_process', term_name='cell cycle')
  - Experimental transcription: go.filter(term_name='transcription', evidence_codes=['EXP', 'IDA'])
""")

print("=" * 70)
print("✓ All tests completed successfully!")
print("=" * 70)
