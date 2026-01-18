"""Core data models."""
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from enum import Enum


class IDType(Enum):
    """Supported identifier types."""
    SYMBOL = "symbol"
    ENTREZ = "entrez"
    ENSEMBL = "ensembl"
    UNIPROT = "uniprot"
    REFSEQ = "refseq"
    KEGG = "kegg"


@dataclass(frozen=True)
class Gene:
    """Gene representation."""
    id: str
    symbol: Optional[str] = None
    name: Optional[str] = None
    synonyms: List[str] = field(default_factory=list)
    species: Optional[str] = None
    source: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def __str__(self) -> str:
        return f"{self.symbol or self.id} ({self.source})"


@dataclass(frozen=True)
class Pathway:
    """Pathway/gene set representation."""
    id: str
    name: str
    description: Optional[str] = None
    genes: List[str] = field(default_factory=list)
    species: Optional[str] = None
    source: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def __len__(self) -> int:
        return len(self.genes)


@dataclass(frozen=True)
class Term:
    """Ontology term (GO, etc)."""
    id: str
    name: str
    namespace: Optional[str] = None
    definition: Optional[str] = None
    is_obsolete: bool = False
    parents: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class Annotation:
    """Gene-to-term annotation."""
    gene_id: str
    term_id: str
    gene_symbol: Optional[str] = None
    evidence_code: Optional[str] = None
    aspect: Optional[str] = None
    species: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

