"""
Common utilities for TravelAssist.

Provides shared utilities, configuration, and helpers used across the application.
"""

from .async_utils import run_blocking_in_executor
from .config import (
    Config,
    DatabaseConfig,
    get_config,
)
from .constants import (
    FIELD_DEPARTURE,
    FIELD_DEPARTURE_CN,
    FIELD_DISTANCE,
    FIELD_DISTANCE_CN,
    FIELD_NAME_MAP,
    FIELD_SCORE,
    FIELD_SCORE_CN,
    FIELD_SEASON,
    FIELD_SEASON_CN,
)
from .database import create_db_client, create_table
from .distance import parse_distance
from .geo import geocode, parse_point_coordinates
from .logger import get_logger, setup_logger
from .season import (
    ALL_SEASONS,
    SEASON_AUTUMN,
    SEASON_SPRING,
    SEASON_SUMMER,
    SEASON_WINTER,
    parse_season_str,
)
from .text import (
    extract_json_from_response,
    format_numbered_list,
    replace_folded_vectors,
)

__all__ = [
    # Logger
    "setup_logger",
    "get_logger",
    # Config
    "Config",
    "get_config",
    "DatabaseConfig",
    # Database
    "create_db_client",
    "create_table",
    # Constants - Field names
    "FIELD_DEPARTURE",
    "FIELD_DISTANCE",
    "FIELD_SCORE",
    "FIELD_SEASON",
    # Constants - Field display names
    "FIELD_DEPARTURE_CN",
    "FIELD_DISTANCE_CN",
    "FIELD_SCORE_CN",
    "FIELD_SEASON_CN",
    # Constants - Mappings
    "FIELD_NAME_MAP",
    # Geo utilities
    "geocode",
    "parse_point_coordinates",
    # Season utilities
    "parse_season_str",
    "SEASON_SPRING",
    "SEASON_SUMMER",
    "SEASON_AUTUMN",
    "SEASON_WINTER",
    "ALL_SEASONS",
    # Distance utilities
    "parse_distance",
    # Text utilities
    "extract_json_from_response",
    "replace_folded_vectors",
    "format_numbered_list",
    # Async utilities
    "run_blocking_in_executor",
]
