"""Setup configuration for pathwaydb package."""
from setuptools import setup, find_packages
from pathlib import Path

# Read version from package
with open("pathwaydb/__init__.py", "r") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split('"')[1]
            break

# Read long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="pathwaydb",
    version=version,
    author="Kai Guo",
    author_email="guokai8@gmail.com",
    description="Biological pathway and gene set annotation toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/guokai8/pathwaydb",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - stdlib only!
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
        ],
    },
    keywords="bioinformatics pathway annotation KEGG GO MSigDB gene-sets enrichment",
    project_urls={
        "Bug Reports": "https://github.com/guokai8/pathwaydb/issues",
        "Source": "https://github.com/guokai8/pathwaydb",
    },
)
