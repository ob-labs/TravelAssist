"""
Constants for OBMMS.

Contains field names, display names, and default values used
throughout the application.
"""

from pathlib import Path

# Project root (src/common/constants.py -> parent.parent.parent)
_BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Path configuration
UPLOAD_DIR = _BASE_DIR / "data" / "uploads"
# All file under UPLOAD_DIR have been uploaded to the database
UPLOADED_DIR = _BASE_DIR / "data" / "uploaded"
CITYDATA_DIR = _BASE_DIR / "data" / "citydata"
ERROR_DIR = _BASE_DIR / "data" / "error"


# Field names (internal use)
FIELD_DEPARTURE = "departure"
FIELD_DISTANCE = "distance"
FIELD_SCORE = "score"
FIELD_SEASON = "season"

# Field display names (Chinese - for user interaction)
FIELD_DEPARTURE_CN = "旅行目的省市"
FIELD_DISTANCE_CN = "行程范围"
FIELD_SCORE_CN = "景点评分"
FIELD_SEASON_CN = "出行季节"

# Mapping from internal field names to display names
FIELD_NAME_MAP = {
    FIELD_DEPARTURE: FIELD_DEPARTURE_CN,
    FIELD_DISTANCE: FIELD_DISTANCE_CN,
    FIELD_SCORE: FIELD_SCORE_CN,
    FIELD_SEASON: FIELD_SEASON_CN,
}

# Vector search settings
VECTOR_DIMENSION = 1024
EMBEDDING_MODEL = "text_embedding_v3"

# API URLs
AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"
