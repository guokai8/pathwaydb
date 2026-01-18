"""Quick start examples for PathwayDB."""

# Example 1: KEGG Pathways
print("=" * 60)
print("Example 1: KEGG Pathways")
print("=" * 60)

from pathwaydb import KEGG

# Initialize KEGG for human
kegg = KEGG(species='hsa', storage_path='kegg_human.db')

# Download annotations (first time only - takes a few minutes)
print("Downloading KEGG annotations...")
kegg.download_annotations()

# Convert Entrez IDs to gene symbols
print("Converting IDs to gene symbols...")
kegg.convert_ids_to_symbols()

# Query by gene
print("\nQuerying pathways for TP53...")
results = kegg.query_by_gene('TP53')
print(f"TP53 is involved in {len(results)} pathways:")
for pathway in results[:5]:  # Show first 5
    print(f"  - {pathway['pathway_id']}: {pathway['pathway_name']}")

# Get pathway details
print("\nGetting pathway details...")
pathway = kegg.get_pathway('hsa05200')
print(f"{pathway.name}")
print(f"  Genes: {len(pathway.genes)}")
print(f"  Description: {pathway.description[:100]}...")

print("\n" + "=" * 60)
print("Example 2: Gene Ontology")
print("=" * 60)

from pathwaydb import GO

# Initialize GO for human
go = GO(species='human', storage_path='go_human.db')

# Download annotations
print("Downloading GO annotations...")
go.download_annotations()

# Query by gene
print("\nQuerying GO terms for BRCA1...")
annotations = go.query_by_gene('BRCA1')
print(f"BRCA1 has {len(annotations)} GO annotations:")
for ann in annotations[:5]:
    print(f"  - {ann['term_name']} ({ann['namespace']}) [{ann['evidence_code']}]")

# Filter by namespace
print("\nFiltering biological processes...")
bp_count = len(go.filter(namespace='biological_process'))
mf_count = len(go.filter(namespace='molecular_function'))
cc_count = len(go.filter(namespace='cellular_component'))
print(f"  Biological Process: {bp_count}")
print(f"  Molecular Function: {mf_count}")
print(f"  Cellular Component: {cc_count}")

print("\n" + "=" * 60)
print("Example 3: MSigDB Gene Sets")
print("=" * 60)

from pathwaydb import MSigDB

# Initialize MSigDB
msigdb = MSigDB(species='human', storage_path='msigdb.db')

# Download Hallmark collection
print("Downloading Hallmark gene sets...")
msigdb.download_collection('H')

# Search gene sets
print("\nSearching for 'interferon' gene sets...")
results = msigdb.search_gene_sets('interferon')
print(f"Found {len(results)} gene sets:")
for gs in results[:3]:
    print(f"  - {gs.name}: {len(gs.genes)} genes")

# Query by gene
print("\nQuerying gene sets containing STAT1...")
gene_sets = msigdb.query_by_gene('STAT1')
print(f"STAT1 appears in {len(gene_sets)} gene sets:")
for gs in gene_sets[:5]:
    print(f"  - {gs.name}")

print("\n" + "=" * 60)
print("Example 4: Gene ID Conversion")
print("=" * 60)

from pathwaydb import IDConverter

# Initialize converter
converter = IDConverter(species='human')

# Single conversion
print("Converting single Entrez ID to symbol...")
symbol = converter.entrez_to_symbol('7157')
print(f"  Entrez 7157 -> {symbol}")

# Batch conversion
print("\nBatch converting Entrez IDs to symbols...")
entrez_ids = ['7157', '675', '4609', '1956']
results = converter.batch_convert(entrez_ids, from_type='entrez', to_type='symbol')
for eid, symbol in zip(entrez_ids, results):
    print(f"  {eid} -> {symbol}")

# Convert to other ID types
print(f"\nConverting TP53 to other ID types...")
ensembl = converter.symbol_to_ensembl('TP53')
uniprot = converter.symbol_to_uniprot('TP53')
print(f"  Ensembl: {ensembl}")
print(f"  UniProt: {uniprot}")

print("\n" + "=" * 60)
print("Example 5: Database Statistics")
print("=" * 60)

# KEGG stats
print("\nKEGG Database Statistics:")
kegg_stats = kegg.stats()
for key, value in kegg_stats.items():
    print(f"  {key}: {value}")

# GO stats
print("\nGO Database Statistics:")
go_stats = go.stats()
for key, value in go_stats.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 60)
print("All examples completed successfully!")
print("=" * 60)
