"""
Data module for OBMMS.

Provides data loading and preprocessing utilities.
"""

from ..common import create_table
from .data_loader import (
    embedding,
    load_csv,
    load_directory,
)

__all__ = [
    "create_table",
    "load_csv",
    "load_directory",
    "generate_embedding",
]
