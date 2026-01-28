"""GO annotation storage with DataFrame-like interface."""
import gzip
import sqlite3
from typing import List, Optional, Dict, Union
from urllib.request import urlopen, Request
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

    def populate_term_names(self, source: str = 'auto'):
        """
        Populate GO term names in the database.

        Args:
            source: Source for term names. Options:
                - 'auto': Try bundled data first, then OBO file, then QuickGO API (default)
                - 'obo': Download and parse GO OBO file (recommended, ~35MB download)
                - 'bundled': Use bundled package data only
                - 'quickgo': Use QuickGO API only (slow, may have rate limits)

        Example:
            >>> db = GOAnnotationDB('go_human.db')
            >>> db.populate_term_names()  # Auto-detect best source
            >>> db.populate_term_names(source='obo')  # Force OBO file
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

        total_updated = 0
        remaining_ids = go_ids

        # Step 1: Try bundled data first (if auto or bundled)
        if source in ('auto', 'bundled'):
            try:
                from ..data import load_go_term_names, has_go_term_names

                if has_go_term_names():
                    print("  Using bundled term name data (instant!)...")
                    term_names = load_go_term_names()

                    for go_id in remaining_ids:
                        term_name = term_names.get(go_id)
                        if term_name:
                            self.conn.execute(
                                "UPDATE go_annotations SET term_name = ? WHERE go_id = ?",
                                (term_name, go_id)
                            )
                            total_updated += 1

                    self.conn.commit()
                    print(f"  ✓ Updated {total_updated}/{len(go_ids)} terms from bundled data")

                    # Check remaining
                    cursor = self.conn.execute("SELECT DISTINCT go_id FROM go_annotations WHERE term_name IS NULL")
                    remaining_ids = [row[0] for row in cursor.fetchall()]

                    if not remaining_ids:
                        print(f"✓ All GO term names populated successfully!")
                        return

                    if source == 'bundled':
                        print(f"  Note: {len(remaining_ids)} terms not found in bundled data")
                        return
                else:
                    if source == 'bundled':
                        print("  Warning: Bundled term name data not found")
                        return

            except Exception as e:
                if source == 'bundled':
                    print(f"  Error: Could not use bundled data: {e}")
                    return
                print(f"  Note: Bundled data not available: {e}")

        # Step 2: Try OBO file (if auto or obo)
        if source in ('auto', 'obo') and remaining_ids:
            try:
                print("  Downloading GO OBO file (contains all term names)...")
                term_names = download_go_obo()

                obo_updated = 0
                for go_id in remaining_ids:
                    term_name = term_names.get(go_id)
                    if term_name:
                        self.conn.execute(
                            "UPDATE go_annotations SET term_name = ? WHERE go_id = ?",
                            (term_name, go_id)
                        )
                        obo_updated += 1

                self.conn.commit()
                total_updated += obo_updated
                print(f"  ✓ Updated {obo_updated} terms from GO OBO file")

                # Check remaining
                cursor = self.conn.execute("SELECT DISTINCT go_id FROM go_annotations WHERE term_name IS NULL")
                remaining_ids = [row[0] for row in cursor.fetchall()]

                if not remaining_ids:
                    print(f"✓ All GO term names populated successfully!")
                    return

                if source == 'obo':
                    if remaining_ids:
                        print(f"  Note: {len(remaining_ids)} terms not found in OBO file (may be obsolete)")
                    return

            except Exception as e:
                if source == 'obo':
                    print(f"  Error downloading OBO file: {e}")
                    return
                print(f"  Note: OBO file not available: {e}")

        # Step 3: Try QuickGO API (if auto or quickgo)
        if source in ('auto', 'quickgo') and remaining_ids:
            print(f"  Fetching {len(remaining_ids)} terms from QuickGO API...")
            base_url = "https://www.ebi.ac.uk/QuickGO/services/ontology/go/terms"

            batch_size = 100
            api_updated = 0

            for i in range(0, len(remaining_ids), batch_size):
                batch = remaining_ids[i:i+batch_size]
                ids_param = ",".join(batch)

                try:
                    url = f"{base_url}/{ids_param}"
                    request = Request(url, headers={'User-Agent': 'pathwaydb/0.2.0 (Python)'})
                    with urlopen(request, timeout=30) as response:
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
                    print(f"    Processed {min(i+batch_size, len(remaining_ids))}/{len(remaining_ids)} terms...")

                    time.sleep(0.2)  # Rate limiting

                except Exception as e:
                    print(f"    Warning: Failed to fetch batch: {e}")
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


# Mapping of species names to GO annotation file names and taxonomy IDs
# Files are downloaded from http://geneontology.org/gene-associations/
GO_SPECIES_MAP = {
    # Mammals
    'human': {'file': 'goa_human', 'taxid': '9606'},
    'mouse': {'file': 'mgi', 'taxid': '10090'},
    'rat': {'file': 'rgd', 'taxid': '10116'},
    'pig': {'file': 'goa_pig', 'taxid': '9823'},
    'cow': {'file': 'goa_cow', 'taxid': '9913'},
    'dog': {'file': 'goa_dog', 'taxid': '9615'},
    'chicken': {'file': 'goa_chicken', 'taxid': '9031'},
    # Fish
    'zebrafish': {'file': 'zfin', 'taxid': '7955'},
    # Invertebrates
    'fly': {'file': 'fb', 'taxid': '7227'},
    'worm': {'file': 'wb', 'taxid': '6239'},
    # Plants
    'arabidopsis': {'file': 'tair', 'taxid': '3702'},
    # Fungi
    'yeast': {'file': 'sgd', 'taxid': '559292'},
}


def get_supported_species() -> list:
    """Return list of supported species for GO annotations."""
    return sorted(GO_SPECIES_MAP.keys())


def download_go_annotations_filtered(
    species: str = 'human',
    evidence_codes: Optional[List[str]] = None,
    output_path: str = 'go_annotations.db',
    return_db: bool = True
) -> Optional[GOAnnotationDB]:
    """Download GO annotations with filtering.

    Supported species: human, mouse, rat, pig, cow, dog, chicken,
                       zebrafish, fly, worm, arabidopsis, yeast
    """
    if species not in GO_SPECIES_MAP:
        supported = ', '.join(get_supported_species())
        raise ValueError(f"Unsupported species: {species}. Supported: {supported}")

    species_info = GO_SPECIES_MAP[species]
    file_name = species_info['file']
    taxid = species_info['taxid']

    url = f"http://geneontology.org/gene-associations/{file_name}.gaf.gz"
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
        # Add User-Agent header to avoid 403 Forbidden errors
        request = Request(url, headers={'User-Agent': 'pathwaydb/0.2.0 (Python)'})
        with urlopen(request, timeout=300) as response:
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


def download_go_obo(cache_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Download and parse GO OBO file to get all GO term names.

    This is a reliable alternative to QuickGO API - downloads the official
    GO ontology file (~35MB) and parses term IDs and names.

    Args:
        cache_dir: Directory to cache the OBO file. If None, uses ~/.pathwaydb_cache/

    Returns:
        Dict mapping GO IDs to term names (e.g., {'GO:0006281': 'DNA repair'})

    Example:
        >>> term_names = download_go_obo()
        >>> print(term_names['GO:0006281'])
        'DNA repair'
    """
    from pathlib import Path
    import os

    # Setup cache directory
    if cache_dir is None:
        cache_dir = Path.home() / '.pathwaydb_cache'
    else:
        cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    obo_path = cache_dir / 'go-basic.obo'
    obo_url = 'http://purl.obolibrary.org/obo/go/go-basic.obo'

    # Download OBO file if not cached or if it's older than 30 days
    should_download = True
    if obo_path.exists():
        import time
        file_age_days = (time.time() - obo_path.stat().st_mtime) / (60 * 60 * 24)
        if file_age_days < 30:
            should_download = False
            print(f"  Using cached GO OBO file ({file_age_days:.1f} days old)")

    if should_download:
        print(f"  Downloading GO OBO file from {obo_url}...")
        request = Request(obo_url, headers={'User-Agent': 'pathwaydb/0.2.0 (Python)'})
        with urlopen(request, timeout=300) as response:
            with open(obo_path, 'wb') as f:
                f.write(response.read())
        print(f"  ✓ Downloaded GO OBO file to {obo_path}")

    # Parse OBO file
    print("  Parsing GO term names from OBO file...")
    term_names = {}
    current_id = None
    current_name = None
    is_obsolete = False

    with open(obo_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            if line == '[Term]':
                # Save previous term if valid
                if current_id and current_name and not is_obsolete:
                    term_names[current_id] = current_name
                # Reset for new term
                current_id = None
                current_name = None
                is_obsolete = False
            elif line.startswith('id: GO:'):
                current_id = line[4:]  # Remove 'id: ' prefix
            elif line.startswith('name: '):
                current_name = line[6:]  # Remove 'name: ' prefix
            elif line == 'is_obsolete: true':
                is_obsolete = True

        # Don't forget the last term
        if current_id and current_name and not is_obsolete:
            term_names[current_id] = current_name

    print(f"  ✓ Parsed {len(term_names):,} GO term names")
    return term_names


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
        fetch_term_names: If True, populate term names from bundled package data (default: True)
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

    # Populate term names from bundled data (instant!)
    if fetch_term_names:
        print("\nPopulating GO term names from bundled package data...")
        db = GOAnnotationDB(cache_path)
        db.populate_term_names(source='bundled')
        db.close()

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

