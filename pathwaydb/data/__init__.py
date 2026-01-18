"""Package data utilities."""
import json
from pathlib import Path
from typing import Dict, Optional


def get_data_dir() -> Path:
    """Get the package data directory."""
    return Path(__file__).parent


def get_go_term_names_path() -> Path:
    """Get path to bundled GO term name mapping file."""
    return get_data_dir() / 'go_term_names.json'


def has_go_term_names() -> bool:
    """Check if GO term name mapping is bundled with the package."""
    return get_go_term_names_path().exists()


def load_go_term_names() -> Dict[str, str]:
    """
    Load bundled GO term name mapping.

    Returns:
        Dictionary mapping GO IDs to term names

    Raises:
        FileNotFoundError: If term name mapping is not bundled

    Example:
        term_names = load_go_term_names()
        print(term_names['GO:0006281'])  # DNA repair
    """
    term_names_path = get_go_term_names_path()

    if not term_names_path.exists():
        raise FileNotFoundError(
            "GO term name mapping not found in package data. "
            "Run: python scripts/prepare_go_term_names.py"
        )

    with open(term_names_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_go_term_name(go_id: str) -> Optional[str]:
    """
    Get term name for a GO ID from bundled data.

    Args:
        go_id: GO term ID (e.g., 'GO:0006281')

    Returns:
        Term name or None if not found

    Example:
        name = get_go_term_name('GO:0006281')
        print(name)  # DNA repair
    """
    try:
        term_names = load_go_term_names()
        return term_names.get(go_id)
    except FileNotFoundError:
        return None


def get_go_data_path(species: str = 'human') -> Path:
    """
    Get path to bundled GO annotation data.

    Args:
        species: Species name ('human', 'mouse', 'rat')

    Returns:
        Path to bundled GO annotation database (may not exist)
    """
    data_dir = get_data_dir() / 'go_annotations'
    return data_dir / f'go_{species}.db'


def has_go_data(species: str = 'human') -> bool:
    """
    Check if GO annotation data is bundled with the package.

    Args:
        species: Species name ('human', 'mouse', 'rat')

    Returns:
        True if data is bundled, False otherwise
    """
    return get_go_data_path(species).exists()


def list_bundled_species() -> list:
    """
    List species with bundled GO annotation data.

    Returns:
        List of species names with bundled data
    """
    data_dir = get_data_dir() / 'go_annotations'
    if not data_dir.exists():
        return []

    species = []
    for db_file in data_dir.glob('go_*.db'):
        # Extract species from filename: go_human.db -> human
        species_name = db_file.stem.replace('go_', '')
        species.append(species_name)

    return sorted(species)
