"""GO annotation storage with DataFrame-like interface."""
import gzip
import sqlite3
from typing import List, Optional, Dict, Union
from urllib.request import urlopen
from dataclasses import dataclass, asdict


@dataclass
class GOAnnotationRecord:
    """Single GO annotation record."""
    gene_id: str
    gene_symbol: str
    go_id: str
    evidence_code: str
    aspect: str  # P=biological_process, F=molecular_function, C=cellular_component
    term_name: Optional[str] = None  # GO term name/description

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return asdict(self)


class GOAnnotationDB:
    """
    SQLite-backed GO annotation database with DataFrame-like query interface.
    
    Usage:
        db = GOAnnotationDB('go_annotations.db')
        
        # Query methods
        annotations = db.query_by_gene(['TP53', 'BRCA1'])
        annotations = db.query_by_go_term('GO:0006915')
        annotations = db.query_by_evidence(['EXP', 'IDA'])
        
        # Get as list of dicts
        records = db.to_records()
        
        # Get as dict of lists
        data = db.to_dict()
        
        # Filter and export
        filtered = db.filter(gene_symbols=['TP53'], aspect='P')
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def query_by_gene(
        self,
        gene_ids: List[str],
        id_type: str = 'symbol'
    ) -> List[GOAnnotationRecord]:
        """Query annotations by gene identifiers."""
        column = 'gene_symbol' if id_type == 'symbol' else 'gene_id'
        placeholders = ','.join('?' * len(gene_ids))

        query = f"""
            SELECT gene_id, gene_symbol, go_id, evidence_code, aspect, term_name
            FROM go_annotations
            WHERE {column} IN ({placeholders})
        """

        cursor = self.conn.execute(query, gene_ids)
        return [GOAnnotationRecord(**dict(row)) for row in cursor.fetchall()]

    def query_by_go_term(self, go_ids: Union[str, List[str]]) -> List[GOAnnotationRecord]:
        """Query genes annotated with specific GO terms."""
        if isinstance(go_ids, str):
            go_ids = [go_ids]

        placeholders = ','.join('?' * len(go_ids))
        query = f"""
            SELECT gene_id, gene_symbol, go_id, evidence_code, aspect, term_name
            FROM go_annotations
            WHERE go_id IN ({placeholders})
        """

        cursor = self.conn.execute(query, go_ids)
        return [GOAnnotationRecord(**dict(row)) for row in cursor.fetchall()]

    def query_by_evidence(self, evidence_codes: List[str]) -> List[GOAnnotationRecord]:
        """Query annotations with specific evidence codes."""
        placeholders = ','.join('?' * len(evidence_codes))
        query = f"""
            SELECT gene_id, gene_symbol, go_id, evidence_code, aspect, term_name
            FROM go_annotations
            WHERE evidence_code IN ({placeholders})
        """

        cursor = self.conn.execute(query, evidence_codes)
        return [GOAnnotationRecord(**dict(row)) for row in cursor.fetchall()]
    
    def filter(
        self,
        gene_ids: Optional[List[str]] = None,
        gene_symbols: Optional[List[str]] = None,
        go_ids: Optional[List[str]] = None,
        evidence_codes: Optional[List[str]] = None,
        aspect: Optional[str] = None,
        term_name: Optional[str] = None
    ) -> List[GOAnnotationRecord]:
        """
        Flexible filtering with multiple criteria.

        Args:
            gene_ids: Filter by gene IDs (exact match)
            gene_symbols: Filter by gene symbols (exact match)
            go_ids: Filter by GO term IDs (exact match)
            evidence_codes: Filter by evidence codes (exact match)
            aspect: Filter by aspect (P/F/C)
            term_name: Filter by GO term name (case-insensitive substring match)

        Returns:
            List of GOAnnotationRecord objects

        Example:
            >>> db = GOAnnotationDB('go_human.db')
            >>> # Find all DNA-related terms
            >>> results = db.filter(term_name='DNA')
            >>> # Find TP53 with DNA repair terms
            >>> results = db.filter(gene_symbols=['TP53'], term_name='DNA repair')
        """
        conditions = []
        params = []

        if gene_ids:
            placeholders = ','.join('?' * len(gene_ids))
            conditions.append(f"gene_id IN ({placeholders})")
            params.extend(gene_ids)

        if gene_symbols:
            placeholders = ','.join('?' * len(gene_symbols))
            conditions.append(f"gene_symbol IN ({placeholders})")
            params.extend(gene_symbols)

        if go_ids:
            placeholders = ','.join('?' * len(go_ids))
            conditions.append(f"go_id IN ({placeholders})")
            params.extend(go_ids)

        if evidence_codes:
            placeholders = ','.join('?' * len(evidence_codes))
            conditions.append(f"evidence_code IN ({placeholders})")
            params.extend(evidence_codes)

        if aspect:
            conditions.append("aspect = ?")
            params.append(aspect)

        if term_name:
            conditions.append("term_name LIKE ?")
            params.append(f"%{term_name}%")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT gene_id, gene_symbol, go_id, evidence_code, aspect, term_name
            FROM go_annotations
            WHERE {where_clause}
        """

        cursor = self.conn.execute(query, params)
        return [GOAnnotationRecord(**dict(row)) for row in cursor.fetchall()]
    
    def to_records(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Export as list of dictionaries."""
        query = "SELECT * FROM go_annotations"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def to_dict(self, limit: Optional[int] = None) -> Dict[str, List[str]]:
        """Export as dictionary of lists."""
        query = "SELECT * FROM go_annotations"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            return {}
        
        result = {key: [] for key in rows[0].keys()}
        for row in rows:
            for key in result:
                result[key].append(row[key])
        
        return result
    
    def to_gene_sets(self) -> Dict[str, List[str]]:
        """Convert to gene sets format for enrichment analysis."""
        query = """
            SELECT go_id, GROUP_CONCAT(gene_symbol) as genes
            FROM go_annotations
            GROUP BY go_id
        """

        cursor = self.conn.execute(query)
        return {row['go_id']: row['genes'].split(',') for row in cursor.fetchall()}

    def to_dataframe(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Export to DataFrame-compatible format for enrichment analysis.

        Returns data in format compatible with pandas DataFrame:
        - GeneID: Gene symbol
        - TERM: GO term ID (e.g., 'GO:0006915')
        - Aspect: Namespace (P=biological_process, F=molecular_function, C=cellular_component)
        - Evidence: Evidence code (e.g., 'EXP', 'IDA', 'IEA')

        Args:
            limit: Optional limit on number of rows

        Returns:
            List of dicts with keys: GeneID, TERM, Aspect, Evidence

        Example:
            >>> db = GOAnnotationDB('go_human.db')
            >>> df_data = db.to_dataframe()
            >>> # If you have pandas installed:
            >>> import pandas as pd
            >>> df = pd.DataFrame(df_data)
            >>> print(df.head())
               GeneID        TERM Aspect Evidence
            0     A2M  GO:0002576      P      IBA
            1     A2M  GO:0006953      P      IEA
        """
        query = """
            SELECT
                gene_symbol as GeneID,
                go_id as TERM,
                aspect as Aspect,
                evidence_code as Evidence
            FROM go_annotations
            ORDER BY gene_symbol, go_id
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor = self.conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def stats(self) -> Dict[str, int]:
        """Get database statistics."""
        cursor = self.conn.execute("""
            SELECT
                COUNT(*) as total_annotations,
                COUNT(DISTINCT gene_id) as unique_genes,
                COUNT(DISTINCT go_id) as unique_terms,
                COUNT(DISTINCT evidence_code) as unique_evidence_codes
            FROM go_annotations
        """)

        return dict(cursor.fetchone())

    def populate_term_names(self, use_bundled_data: bool = True):
        """
        Populate GO term names in the database.

        This method tries to use bundled term name data from the package first,
        then falls back to QuickGO API if needed.

        Args:
            use_bundled_data: If True, use bundled package data (default: True)
                             Set to False to force QuickGO API calls
        """
        import json
        import time

        # Get unique GO terms that need names
        cursor = self.conn.execute("SELECT DISTINCT go_id FROM go_annotations WHERE term_name IS NULL")
        go_ids = [row[0] for row in cursor.fetchall()]

        if not go_ids:
            print("✓ All GO terms already have names populated")
            return

        print(f"Populating names for {len(go_ids)} GO terms...")

        # Try bundled data first
        total_updated = 0
        if use_bundled_data:
            try:
                from ..data import load_go_term_names, has_go_term_names

                if has_go_term_names():
                    print("  Using bundled term name data (instant!)...")
                    term_names = load_go_term_names()

                    # Update all terms from bundled data
                    for go_id in go_ids:
                        term_name = term_names.get(go_id)
                        if term_name:
                            self.conn.execute(
                                "UPDATE go_annotations SET term_name = ? WHERE go_id = ?",
                                (term_name, go_id)
                            )
                            total_updated += 1

                    self.conn.commit()
                    print(f"  ✓ Updated {total_updated}/{len(go_ids)} terms from bundled data")

                    # Check if we got all terms
                    cursor = self.conn.execute("SELECT DISTINCT go_id FROM go_annotations WHERE term_name IS NULL")
                    remaining = [row[0] for row in cursor.fetchall()]

                    if not remaining:
                        print(f"✓ All GO term names populated successfully!")
                        return
                    else:
                        print(f"  Note: {len(remaining)} terms not found in bundled data")
                        go_ids = remaining  # Continue with QuickGO API for remaining

                else:
                    print("  Note: Bundled term name data not found, using QuickGO API...")

            except Exception as e:
                print(f"  Warning: Could not use bundled data: {e}")
                print("  Falling back to QuickGO API...")

        # Fetch remaining terms from QuickGO API
        if go_ids:
            print(f"  Fetching {len(go_ids)} terms from QuickGO API...")
            base_url = "https://www.ebi.ac.uk/QuickGO/services/ontology/go/terms"

            # Process in batches of 100
            batch_size = 100
            api_updated = 0

            for i in range(0, len(go_ids), batch_size):
                batch = go_ids[i:i+batch_size]
                ids_param = ",".join(batch)

                try:
                    url = f"{base_url}/{ids_param}"
                    with urlopen(url, timeout=30) as response:
                        data = json.loads(response.read().decode('utf-8'))

                        if 'results' in data:
                            for result in data['results']:
                                go_id = result.get('id')
                                term_name = result.get('name')

                                if go_id and term_name:
                                    self.conn.execute(
                                        "UPDATE go_annotations SET term_name = ? WHERE go_id = ?",
                                        (term_name, go_id)
                                    )
                                    api_updated += 1

                    self.conn.commit()
                    print(f"    Processed {min(i+batch_size, len(go_ids))}/{len(go_ids)} terms from API...")

                    # Rate limiting
                    time.sleep(0.2)

                except Exception as e:
                    print(f"    Warning: Failed to fetch batch {i//batch_size + 1}: {e}")
                    continue

            total_updated += api_updated
            print(f"  ✓ Updated {api_updated} terms from QuickGO API")

        print(f"✓ Total: {total_updated} GO term names populated")

    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def download_go_annotations_filtered(
    species: str = 'human',
    evidence_codes: Optional[List[str]] = None,
    output_path: str = 'go_annotations.db',
    return_db: bool = True
) -> Optional[GOAnnotationDB]:
    """Download GO annotations with filtering."""
    TAXID_MAP = {'human': '9606', 'mouse': '10090', 'rat': '10116'}
    taxid = TAXID_MAP.get(species, '9606')
    
    url = f"http://geneontology.org/gene-associations/goa_{species}.gaf.gz"
    valid_evidence = set(evidence_codes) if evidence_codes else None
    
    db = sqlite3.connect(output_path)
    db.execute("""
        CREATE TABLE IF NOT EXISTS go_annotations (
            gene_id TEXT,
            gene_symbol TEXT,
            go_id TEXT,
            evidence_code TEXT,
            aspect TEXT,
            term_name TEXT,
            PRIMARY KEY (gene_id, go_id)
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_gene ON go_annotations(gene_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON go_annotations(gene_symbol)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_go ON go_annotations(go_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_evidence ON go_annotations(evidence_code)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_term_name ON go_annotations(term_name)")

    # Create GO terms lookup table
    db.execute("""
        CREATE TABLE IF NOT EXISTS go_terms (
            go_id TEXT PRIMARY KEY,
            term_name TEXT,
            definition TEXT
        )
    """)
    
    print(f"Downloading GO annotations from {url}...")
    count = 0
    
    try:
        with urlopen(url, timeout=300) as response:
            with gzip.open(response, 'rt') as f:
                for line in f:
                    if line.startswith('!'):
                        continue
                    
                    fields = line.strip().split('\t')
                    if len(fields) < 17:
                        continue
                    
                    gene_id = fields[1]
                    symbol = fields[2]
                    go_id = fields[4]
                    evidence = fields[6]
                    aspect = fields[8]
                    
                    if valid_evidence and evidence not in valid_evidence:
                        continue

                    db.execute(
                        "INSERT OR IGNORE INTO go_annotations VALUES (?, ?, ?, ?, ?, ?)",
                        (gene_id, symbol, go_id, evidence, aspect, None)  # term_name will be populated later
                    )

                    count += 1
                    if count % 100000 == 0:
                        db.commit()
                        print(f"  Processed {count:,} annotations...")
        
        db.commit()
        print(f"✓ Stored {count:,} annotations in {output_path}")
        
    finally:
        db.close()
    
    if return_db:
        return GOAnnotationDB(output_path)
    return None


def load_go_annotations(db_path: str) -> GOAnnotationDB:
    """Load existing GO annotation database."""
    return GOAnnotationDB(db_path)


def get_cache_path(species: str = 'human') -> str:
    """Get the default cache path for GO annotations."""
    from pathlib import Path
    cache_dir = Path.home() / '.pathwaydb_cache' / 'go_annotations'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return str(cache_dir / f'go_{species}_cached.db')


def download_to_cache(
    species: str = 'human',
    evidence_codes: Optional[List[str]] = None,
    fetch_term_names: bool = True,
    force_refresh: bool = False
) -> str:
    """
    Download GO annotations to a centralized cache location.

    This allows you to download once and reuse across multiple projects.

    Args:
        species: Species name ('human', 'mouse', 'rat')
        evidence_codes: Optional list of evidence codes to filter by
        fetch_term_names: If True, fetch term names from QuickGO API (default: True)
        force_refresh: If True, re-download even if cache exists

    Returns:
        Path to the cached database file

    Example:
        # Download once to cache
        cache_path = download_to_cache(species='human')
        print(f"GO annotations cached at: {cache_path}")

        # Use the cache in your project
        db = load_from_cache(species='human')
        annotations = db.filter(gene_symbols=['TP53'])
    """
    import shutil

    cache_path = get_cache_path(species)

    # Check if cache exists and we're not forcing refresh
    if not force_refresh:
        from pathlib import Path
        if Path(cache_path).exists():
            # Check if it has data
            test_db = sqlite3.connect(cache_path)
            cursor = test_db.execute("SELECT COUNT(*) FROM go_annotations")
            count = cursor.fetchone()[0]
            test_db.close()

            if count > 0:
                print(f"✓ GO annotations for {species} already cached ({count:,} annotations)")
                print(f"  Cache location: {cache_path}")
                print(f"  Use force_refresh=True to re-download")
                return cache_path

    print(f"Downloading GO annotations for {species} to cache...")
    print(f"Cache location: {cache_path}")

    # Download to cache
    download_go_annotations_filtered(
        species=species,
        evidence_codes=evidence_codes,
        output_path=cache_path,
        return_db=False
    )

    # Fetch term names if requested
    if fetch_term_names:
        print("\nFetching GO term names from QuickGO API...")
        print("(This takes a few minutes but only needs to be done once)")

        from ..connectors.go import GO
        go = GO(storage_path=cache_path)
        go.populate_term_names()
        print("✓ Term names populated in cache!")

    print(f"\n✓ GO annotations cached successfully at: {cache_path}")
    return cache_path


def load_from_cache(species: str = 'human') -> GOAnnotationDB:
    """
    Load GO annotations from the centralized cache.

    If the cache doesn't exist, it will be downloaded automatically.

    Args:
        species: Species name ('human', 'mouse', 'rat')

    Returns:
        GOAnnotationDB instance connected to the cached database

    Example:
        # Load from cache (downloads automatically if not cached)
        db = load_from_cache(species='human')

        # Query directly from cache
        annotations = db.filter(gene_symbols=['TP53'])
        print(f"Found {len(annotations)} TP53 annotations")
    """
    cache_path = get_cache_path(species)

    # Check if cache exists
    from pathlib import Path
    if not Path(cache_path).exists():
        print(f"Cache not found for {species}. Downloading...")
        download_to_cache(species=species, fetch_term_names=True)

    return GOAnnotationDB(cache_path)


def copy_from_cache(
    species: str = 'human',
    output_path: str = 'go_annotations.db',
    download_if_missing: bool = True
) -> GOAnnotationDB:
    """
    Copy GO annotations from cache to a project-specific database.

    This is useful when you want a local copy that won't be affected
    by cache updates.

    Args:
        species: Species name ('human', 'mouse', 'rat')
        output_path: Path for the copied database
        download_if_missing: If True, download to cache if not found

    Returns:
        GOAnnotationDB instance connected to the copied database

    Example:
        # Copy cache to project database
        db = copy_from_cache(species='human', output_path='my_project_go.db')

        # Now you have a local copy independent of the cache
        annotations = db.filter(gene_symbols=['TP53'])
    """
    import shutil
    from pathlib import Path

    cache_path = get_cache_path(species)

    # Download to cache if missing
    if not Path(cache_path).exists():
        if download_if_missing:
            print(f"Cache not found for {species}. Downloading...")
            download_to_cache(species=species, fetch_term_names=True)
        else:
            raise FileNotFoundError(
                f"GO annotations cache not found for {species}. "
                f"Run download_to_cache('{species}') first or set download_if_missing=True"
            )

    # Copy cache to output path
    print(f"Copying GO annotations from cache to {output_path}...")
    shutil.copy2(cache_path, output_path)
    print(f"✓ Copied {cache_path} to {output_path}")

    return GOAnnotationDB(output_path)

