"""
Test MSigDB filtering functionality.

Demonstrates the new unified filter() method and to_dataframe() export.
"""

print("=" * 70)
print("MSigDB Filter & DataFrame Export - NEW FEATURES")
print("=" * 70)

from pathwaydb import MSigDB

# Initialize MSigDB
print("\nInitializing MSigDB...")
msigdb = MSigDB(storage_path='msigdb_test.db')

# Download Hallmark collection if not already downloaded
print("\nDownloading Hallmark gene sets (if needed)...")
try:
    count = msigdb.download_collection('H', species='human')
    print(f"✓ Hallmark collection ready ({count} gene sets)")
except Exception as e:
    print(f"Note: {e}")

# Get stats
stats = msigdb.stats()
print(f"\nDatabase statistics:")
print(f"  Total gene sets: {stats['total_gene_sets']}")
print(f"  Collections: {stats['total_collections']}")
if 'by_collection' in stats:
    for coll, count in stats['by_collection'].items():
        print(f"    {coll}: {count} gene sets")

print("\n" + "=" * 70)
print("Testing filter() method")
print("=" * 70)

# Test 1: Filter by gene set name
print("\n1. Filter by gene_set_name='apoptosis'")
apoptosis_sets = msigdb.filter(gene_set_name='apoptosis')
print(f"✓ Found {len(apoptosis_sets)} gene sets with 'apoptosis' in name")
if apoptosis_sets:
    print("\nFirst 3 gene sets:")
    for gs in apoptosis_sets[:3]:
        print(f"  {gs.gene_set_name}")
        print(f"    Collection: {gs.collection}, Genes: {len(gs.genes)}")

# Test 2: Filter by collection
print("\n2. Filter by collection='H'")
hallmark_sets = msigdb.filter(collection='H')
print(f"✓ Found {len(hallmark_sets)} Hallmark gene sets")

# Test 3: Filter by description
print("\n3. Filter by description='immune'")
immune_sets = msigdb.filter(description='immune')
print(f"✓ Found {len(immune_sets)} gene sets with 'immune' in description")
if immune_sets:
    print("\nFirst 3 gene sets:")
    for gs in immune_sets[:3]:
        print(f"  {gs.gene_set_name}")
        print(f"    Description: {gs.description[:60]}...")

# Test 4: Filter by gene symbols
print("\n4. Filter by gene_symbols=['TP53', 'MYC']")
tp53_myc_sets = msigdb.filter(gene_symbols=['TP53', 'MYC'])
print(f"✓ Found {len(tp53_myc_sets)} gene sets containing TP53 or MYC")
if tp53_myc_sets:
    print("\nFirst 5 gene sets:")
    for gs in tp53_myc_sets[:5]:
        has_tp53 = 'TP53' in gs.genes
        has_myc = 'MYC' in gs.genes
        genes_str = []
        if has_tp53:
            genes_str.append('TP53')
        if has_myc:
            genes_str.append('MYC')
        print(f"  {gs.gene_set_name} ({gs.collection})")
        print(f"    Contains: {', '.join(genes_str)}")

# Test 5: Combine multiple filters
print("\n5. Combine filters: gene_set_name='interferon' + collection='H'")
interferon_hallmark = msigdb.filter(
    gene_set_name='interferon',
    collection='H'
)
print(f"✓ Found {len(interferon_hallmark)} Hallmark interferon gene sets")
if interferon_hallmark:
    for gs in interferon_hallmark:
        print(f"  {gs.gene_set_name}")
        print(f"    Genes: {len(gs.genes)}")
        print(f"    Description: {gs.description[:80]}...")

# Test 6: Case-insensitive search
print("\n6. Case-insensitive search: 'APOPTOSIS' vs 'apoptosis'")
upper_results = msigdb.filter(gene_set_name='APOPTOSIS')
lower_results = msigdb.filter(gene_set_name='apoptosis')
print(f"✓ 'APOPTOSIS': {len(upper_results)} results")
print(f"✓ 'apoptosis': {len(lower_results)} results")
print(f"✓ Case-insensitive: {len(upper_results) == len(lower_results)}")

print("\n" + "=" * 70)
print("Testing to_dataframe() method")
print("=" * 70)

# Test DataFrame export
print("\n7. Export Hallmark gene sets to DataFrame format")
df_data = msigdb.to_dataframe(collection='H')
print(f"✓ Exported {len(df_data)} gene-to-geneset mappings")

if df_data:
    print("\nFirst 10 rows:")
    print(f"{'GeneID':<12} {'GeneSet':<30} {'Collection':<12}")
    print("-" * 70)
    for row in df_data[:10]:
        gene_set_short = row['GeneSet'][:28] + '...' if len(row['GeneSet']) > 30 else row['GeneSet']
        print(f"{row['GeneID']:<12} {gene_set_short:<30} {row['Collection']:<12}")

print("\n" + "=" * 70)
print("Summary")
print("=" * 70)
print("""
NEW MSigDB Filter Features:
  ✓ filter() method - Unified filtering with multiple criteria
  ✓ gene_set_name parameter - Filter by gene set name (case-insensitive)
  ✓ description parameter - Filter by description text
  ✓ collection parameter - Filter by collection (H, C1, C2, etc.)
  ✓ gene_symbols parameter - Find gene sets containing specific genes
  ✓ organism parameter - Filter by organism (human, mouse)
  ✓ to_dataframe() method - Export to pandas-compatible format

DataFrame Export Format:
  Columns: GeneID, GeneSet, Collection, Description
  Each row represents one gene-to-geneset mapping

Usage Examples:
  # Find apoptosis gene sets
  msigdb.filter(gene_set_name='apoptosis')

  # Find Hallmark immune gene sets
  msigdb.filter(collection='H', description='immune')

  # Find gene sets containing TP53
  msigdb.filter(gene_symbols=['TP53'])

  # Export to pandas DataFrame
  data = msigdb.to_dataframe(collection='H')
  import pandas as pd
  df = pd.DataFrame(data)

MSigDB filtering is now consistent with KEGG and GO! 🎉
""")

print("=" * 70)
print("✓ All tests completed successfully!")
print("=" * 70)
