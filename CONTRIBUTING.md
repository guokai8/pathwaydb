# Contributing to PathwayDB

Thank you for your interest in contributing to PathwayDB! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/guokai8/pathwaydb.git
   cd pathwaydb
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install in development mode**:
   ```bash
   pip install -e ".[dev]"
   # Or install dev requirements separately
   pip install -r requirements-dev.txt
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Your Changes

Follow these guidelines:

- **Code Style**: Use `black` for formatting and follow PEP 8
- **Documentation**: Add docstrings to all public functions/classes
- **Type Hints**: Use type hints for function arguments and return values
- **No External Dependencies**: Keep the package stdlib-only (unless absolutely necessary)

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pathwaydb --cov-report=html

# Run specific test file
pytest tests/test_kegg.py
```

### 4. Format Your Code

```bash
# Format with black
black pathwaydb/

# Sort imports
isort pathwaydb/

# Check linting
flake8 pathwaydb/

# Type checking
mypy pathwaydb/
```

### 5. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add WikiPathways connector

- Implement WikiPathways API client
- Add local storage support
- Include tests and documentation"
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear description of changes
- Reference to related issues
- Screenshots/examples if applicable

## Adding a New Database Connector

See [CLAUDE.md](CLAUDE.md) for detailed architecture information. Here's a quick template:

### 1. Create Connector Class

`pathwaydb/connectors/newdb.py`:

```python
"""NewDB API client with local storage support."""
from typing import List, Optional
from ..core.models import Pathway
from ..core.constants import DEFAULT_RATE_LIMIT
from ..http.client import HTTPClient

class NewDB:
    """NewDB database client."""

    def __init__(self, species: str = 'human', cache_dir: Optional[str] = None):
        self.species = species
        self.base_url = 'https://api.newdb.org'
        self.client = HTTPClient(cache_dir=cache_dir, rate_limit=DEFAULT_RATE_LIMIT)

    def get_pathway(self, pathway_id: str) -> Pathway:
        """Get pathway by ID."""
        pass

    def list_pathways(self) -> List[Pathway]:
        """List all pathways."""
        pass
```

### 2. Add Storage Class (Optional)

`pathwaydb/storage/newdb_db.py`:

```python
import sqlite3
from typing import List, Dict
from pathlib import Path

class NewDBStorage:
    """Local storage for NewDB data."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._create_tables()

    def _create_tables(self):
        """Create database schema."""
        pass
```

### 3. Add Tests

`tests/test_newdb.py`:

```python
import pytest
from pathwaydb import NewDB

def test_newdb_init():
    db = NewDB(species='human')
    assert db.species == 'human'

def test_get_pathway():
    db = NewDB()
    pathway = db.get_pathway('TEST001')
    assert pathway.id == 'TEST001'
```

### 4. Update Exports

`pathwaydb/__init__.py`:

```python
from pathwaydb.connectors.newdb import NewDB

__all__ = [
    # ... existing ...
    'NewDB',
]
```

### 5. Update Documentation

- Add examples to README.md
- Document API in docstrings
- Update CLAUDE.md if architecture changes

## Code Review Process

All submissions require review. We'll look for:

1. **Functionality**: Does it work as intended?
2. **Tests**: Are there adequate tests?
3. **Documentation**: Is it well documented?
4. **Code Quality**: Is it clean, readable, maintainable?
5. **No Breaking Changes**: Unless absolutely necessary
6. **Performance**: Is it reasonably efficient?

## Types of Contributions

### Bug Reports

- Use the GitHub issue tracker
- Include Python version, OS, and error messages
- Provide minimal reproducible example

### Feature Requests

- Open an issue first to discuss
- Explain the use case and benefits
- Consider backward compatibility

### Documentation

- Fix typos, improve clarity
- Add examples and tutorials
- Improve docstrings

### Code Contributions

- Bug fixes
- New database connectors
- Performance improvements
- Test coverage improvements

## Questions?

- Open an issue for questions
- Check [CLAUDE.md](CLAUDE.md) for architecture details
- Email: guokai8@gmail.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to PathwayDB!
