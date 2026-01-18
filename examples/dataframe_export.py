"""
Example: Export KEGG and GO data to DataFrame-compatible format.

This example shows how to export annotation data in a tabular format
that's compatible with pandas DataFrame or can be used directly for
enrichment analysis (similar to clusterProfiler in R).
"""

print("=" * 70)
print("Example: Export Annotation Data to DataFrame Format")
print("=" * 70)

# Example 1: KEGG Pathway Annotations
print("\n1. KEGG Pathway Annotations (DataFrame format)")
print("-" * 70)

from pathwaydb.storage import KEGGAnnotationDB

# Load existing KEGG database
kegg_db = KEGGAnnotationDB('kegg_human.db')

# Export to DataFrame-compatible format
df_data = kegg_db.to_dataframe(limit=10)

print(f"\nReturned {len(df_data)} rows")
print("\nFirst 10 rows:")
print(f"{'GeneID':<10} {'PATH':<12} {'Annot':<50}")
print("-" * 72)
for row in df_data:
    annot = row['Annot'][:47] + '...' if row['Annot'] and len(row['Annot']) > 50 else (row['Annot'] or '')
    print(f"{row['GeneID']:<10} {row['PATH']:<12} {annot:<50}")

# Example 2: Convert to pandas DataFrame (if pandas is installed)
print("\n\n2. Convert to pandas DataFrame (if available)")
print("-" * 70)

try:
    import pandas as pd

    # Get all data (or use limit parameter for large datasets)
    all_data = kegg_db.to_dataframe(limit=1000)

    # Create DataFrame
    df = pd.DataFrame(all_data)

    print("\nDataFrame Info:")
    print(df.info())

    print("\nFirst 5 rows:")
    print(df.head())

    print("\nUnique genes:", df['GeneID'].nunique())
    print("Unique pathways:", df['PATH'].nunique())

    # Example: Filter for specific gene
    print("\nPathways for gene 'TP53':")
    tp53_pathways = df[df['GeneID'] == 'TP53']
    print(tp53_pathways[['PATH', 'Annot']].to_string(index=False))

except ImportError:
    print("\npandas not installed. The data is returned as a list of dicts")
    print("which can be used directly or converted to other formats.")
    print("\nTo use pandas:")
    print("  pip install pandas")

# Example 3: GO Annotations
print("\n\n3. GO Annotations (DataFrame format)")
print("-" * 70)

from pathwaydb.storage import GOAnnotationDB

# Load existing GO database
go_db = GOAnnotationDB('go_human.db')

# Export to DataFrame-compatible format
go_data = go_db.to_dataframe(limit=10)

print(f"\nReturned {len(go_data)} rows")
print("\nFirst 10 rows:")
print(f"{'GeneID':<10} {'TERM':<15} {'Aspect':<8} {'Evidence':<10}")
print("-" * 45)
for row in go_data:
    print(f"{row['GeneID']:<10} {row['TERM']:<15} {row['Aspect']:<8} {row['Evidence']:<10}")

# Example 4: Using GO data with pandas
try:
    import pandas as pd

    # Get GO data
    all_go_data = go_db.to_dataframe(limit=1000)
    df_go = pd.DataFrame(all_go_data)

    print("\n\nGO DataFrame Info:")
    print(df_go.info())

    print("\nFirst 5 rows:")
    print(df_go.head())

    # Count annotations by aspect
    print("\nAnnotations by aspect:")
    print(df_go['Aspect'].value_counts())

    # Count annotations by evidence code
    print("\nTop 10 evidence codes:")
    print(df_go['Evidence'].value_counts().head(10))

    # Example: Filter for specific gene and aspect
    print("\nBiological Process terms for gene 'BRCA1':")
    brca1_bp = df_go[(df_go['GeneID'] == 'BRCA1') & (df_go['Aspect'] == 'P')]
    print(brca1_bp[['TERM', 'Evidence']].to_string(index=False))

except ImportError:
    pass

# Example 5: Save to CSV (if pandas is installed)
print("\n\n4. Save to CSV file")
print("-" * 70)

try:
    import pandas as pd

    # Export KEGG data
    kegg_data = kegg_db.to_dataframe()
    df_kegg = pd.DataFrame(kegg_data)
    df_kegg.to_csv('kegg_annotations.csv', index=False)
    print(f"✓ Saved KEGG annotations to kegg_annotations.csv ({len(df_kegg)} rows)")

    # Export GO data
    go_data_all = go_db.to_dataframe()
    df_go_all = pd.DataFrame(go_data_all)
    df_go_all.to_csv('go_annotations.csv', index=False)
    print(f"✓ Saved GO annotations to go_annotations.csv ({len(df_go_all)} rows)")

except ImportError:
    print("pandas not installed - cannot save to CSV")
    print("\nAlternative: Save without pandas:")

    import csv

    # Export KEGG to CSV manually
    kegg_data = kegg_db.to_dataframe(limit=100)
    if kegg_data:
        with open('kegg_annotations_manual.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=kegg_data[0].keys())
            writer.writeheader()
            writer.writerows(kegg_data)
        print(f"✓ Saved KEGG annotations to kegg_annotations_manual.csv (first 100 rows)")

# Example 6: Use for enrichment analysis
print("\n\n5. Prepare for enrichment analysis")
print("-" * 70)

# Create gene-to-pathway mapping
kegg_mapping = kegg_db.to_dataframe()

# Group by gene to get all pathways per gene
from collections import defaultdict

gene_to_pathways = defaultdict(list)
for row in kegg_mapping:
    gene_to_pathways[row['GeneID']].append(row['PATH'])

print(f"\nCreated gene-to-pathway mapping for {len(gene_to_pathways)} genes")
print("\nExample - Pathways for TP53:")
print(gene_to_pathways.get('TP53', [])[:10])

# Group by pathway to get all genes per pathway
pathway_to_genes = defaultdict(list)
for row in kegg_mapping:
    pathway_to_genes[row['PATH']].append(row['GeneID'])

print(f"\nCreated pathway-to-gene mapping for {len(pathway_to_genes)} pathways")

# Close databases
kegg_db.close()
go_db.close()

print("\n" + "=" * 70)
print("Examples completed successfully!")
print("=" * 70)
