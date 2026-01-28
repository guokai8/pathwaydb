"""
GO Filter Examples - Comprehensive guide to filtering GO annotations.

The GO filter supports multiple parameters for flexible querying.
"""

from pathwaydb import GO
from pathwaydb.storage import GOAnnotationDB

print("=" * 70)
print("GO Filter Examples")
print("=" * 70)

# Example 1: Filter by gene symbols
print("\n1. Filter by Gene Symbols")
print("-" * 70)

go = GO(storage_path='go_human.db')
db = GOAnnotationDB('go_human.db')

# Single gene
tp53_annotations = db.filter(gene_symbols=['TP53'])
print(f"TP53 has {len(tp53_annotations)} GO annotations")

# Multiple genes
cancer_genes = db.filter(gene_symbols=['TP53', 'BRCA1', 'EGFR'])
print(f"TP53, BRCA1, EGFR have {len(cancer_genes)} total annotations")

# Example 2: Filter by Aspect (Namespace)
print("\n2. Filter by Aspect/Namespace")
print("-" * 70)

# Method 1: Using the GO connector with namespace parameter
biological_process = go.filter(namespace='biological_process')
molecular_function = go.filter(namespace='molecular_function')
cellular_component = go.filter(namespace='cellular_component')

print(f"Biological Process: {len(biological_process)} annotations")
print(f"Molecular Function: {len(molecular_function)} annotations")
print(f"Cellular Component: {len(cellular_component)} annotations")

# Method 2: Using storage directly with aspect codes
bp_annotations = db.filter(aspect='P')  # P = biological_process
mf_annotations = db.filter(aspect='F')  # F = molecular_function
cc_annotations = db.filter(aspect='C')  # C = cellular_component

print(f"\nUsing aspect codes:")
print(f"  Aspect P: {len(bp_annotations)} annotations")
print(f"  Aspect F: {len(mf_annotations)} annotations")
print(f"  Aspect C: {len(cc_annotations)} annotations")

# Example 3: Filter by Evidence Codes
print("\n3. Filter by Evidence Codes")
print("-" * 70)

# Get only experimental evidence (high confidence)
experimental = db.filter(evidence_codes=['EXP', 'IDA', 'IPI', 'IMP', 'IGI', 'IEP'])
print(f"Experimental evidence: {len(experimental)} annotations")

# Computational evidence
computational = db.filter(evidence_codes=['IEA', 'ISS', 'ISO', 'ISA'])
print(f"Computational evidence: {len(computational)} annotations")

# Manual curation
curated = db.filter(evidence_codes=['TAS', 'NAS', 'IC'])
print(f"Manually curated: {len(curated)} annotations")

# Example 4: Combine Multiple Filters
print("\n4. Combine Multiple Filters")
print("-" * 70)

# Get TP53 biological processes with experimental evidence
tp53_bp_exp = db.filter(
    gene_symbols=['TP53'],
    aspect='P',
    evidence_codes=['EXP', 'IDA', 'IPI', 'IMP']
)
print(f"TP53 biological processes (experimental): {len(tp53_bp_exp)} annotations")

# Get multiple genes in molecular functions
genes_mf = db.filter(
    gene_symbols=['TP53', 'BRCA1', 'MYC'],
    aspect='F'
)
print(f"TP53/BRCA1/MYC molecular functions: {len(genes_mf)} annotations")

# Example 5: Filter by Specific GO Terms
print("\n5. Filter by Specific GO Terms")
print("-" * 70)

# DNA repair terms
dna_repair_genes = db.filter(go_ids=['GO:0006281'])  # DNA repair
print(f"Genes annotated with DNA repair: {len(dna_repair_genes)}")

# Apoptosis terms
apoptosis_genes = db.filter(go_ids=['GO:0006915'])  # Apoptotic process
print(f"Genes annotated with apoptosis: {len(apoptosis_genes)}")

# Multiple specific terms
specific_terms = db.filter(go_ids=['GO:0006281', 'GO:0006915', 'GO:0008283'])
print(f"Genes in DNA repair/apoptosis/proliferation: {len(specific_terms)}")

# Example 6: Quality Filtering
print("\n6. Filter for High-Quality Annotations")
print("-" * 70)

# High-confidence annotations: experimental + manually reviewed
high_confidence = db.filter(
    evidence_codes=['EXP', 'IDA', 'IPI', 'IMP', 'IGI', 'IEP', 'TAS', 'IC'],
    aspect='P'
)
print(f"High-confidence biological processes: {len(high_confidence)} annotations")

# Exclude computational predictions
all_bp = db.filter(aspect='P')
iea_bp = db.filter(aspect='P', evidence_codes=['IEA'])
curated_bp = len(all_bp) - len(iea_bp)
print(f"Curated biological processes (excluding IEA): ~{curated_bp} annotations")

# Example 7: Export Filtered Results
print("\n7. Export Filtered Results to DataFrame")
print("-" * 70)

# Filter and export
tp53_data = db.filter(gene_symbols=['TP53'], aspect='P')
print(f"Filtered {len(tp53_data)} TP53 biological process annotations")

# Convert to DataFrame format
import pandas as pd
df_records = [ann.to_dict() for ann in tp53_data[:10]]
df = pd.DataFrame(df_records) if df_records else None

if df is not None:
    print("\nFirst 5 rows:")
    print(df.head())

# Save to CSV
# df.to_csv('tp53_biological_processes.csv', index=False)

print("\n" + "=" * 70)
print("GO Filter Summary")
print("=" * 70)
print("""
Available Filter Parameters:
  - gene_symbols: List[str] - Filter by gene symbols
  - gene_ids: List[str] - Filter by gene IDs
  - go_ids: List[str] - Filter by GO term IDs
  - evidence_codes: List[str] - Filter by evidence codes
  - aspect: str - Filter by P/F/C (biological_process/molecular_function/cellular_component)

Using GO Connector (go.filter):
  - namespace: str - User-friendly names: 'biological_process', 'molecular_function', 'cellular_component'

Evidence Code Guide:
  Experimental:
    - EXP: Inferred from Experiment
    - IDA: Inferred from Direct Assay
    - IPI: Inferred from Physical Interaction
    - IMP: Inferred from Mutant Phenotype
    - IGI: Inferred from Genetic Interaction
    - IEP: Inferred from Expression Pattern

  Computational:
    - IEA: Inferred from Electronic Annotation
    - ISS: Inferred from Sequence/Structural Similarity
    - ISO: Inferred from Sequence Orthology
    - ISA: Inferred from Sequence Alignment

  Author/Curator:
    - TAS: Traceable Author Statement
    - NAS: Non-traceable Author Statement
    - IC: Inferred by Curator
    - ND: No biological Data available

Note: GO term names are NOT stored in the local database.
      Use go_ids parameter to filter specific terms.
      For term name lookup, use the GO connector's get_term() method.
""")

db.close()
