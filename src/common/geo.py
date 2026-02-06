"""
Geographic utilities for OBMMS.

Provides geocoding and coordinate parsing functions.
"""

import json
import re
import time
from typing import Tuple

import requests

from .config import get_config
from .logger import get_logger

logger = get_logger(__name__)

# Type alias for coordinates (latitude, longitude)
Coordinates = Tuple[float, float]

# Default map center (Beijing)
DEFAULT_LAT = 39.9042
DEFAULT_LONG = 116.4074


def geocode(address: str) -> Coordinates:
    """
    Convert an address string to geographic coordinates using Amap API.

    Args:
        address: The address string to geocode.

    Returns:
        A tuple of (latitude, longitude).

    Raises:
        KeyError: If the geocoding fails due to invalid address or API error.
        ValueError: If AMAP_API_KEY is not configured.
    """
    logger.debug(f"[Geocode] Converting address: {address}")

    api_key = get_config().amap_api_key or ""
    if not api_key:
        logger.error("[Geocode] AMAP_API_KEY not configured")
        raise ValueError("AMAP_API_KEY environment variable is not set")

    params = {
        "address": address,
        "key": api_key,
    }
    url = "https://restapi.amap.com/v3/geocode/geo"
    max_retries = 10
    retry_count = 0

    while retry_count < max_retries:
        try:
            logger.debug(f"[Geocode] Sending request to Amap API (attempt {retry_count + 1})")
            response = requests.get(url, params=params, timeout=10)
            result = json.loads(response.text)

            # Extract coordinates from response
            location = result["geocodes"][0]["location"]
            longitude_str, latitude_str = location.split(",")
            coords = (float(latitude_str), float(longitude_str))
            logger.debug(f"[Geocode] Success: {address} -> ({coords[0]:.4f}, {coords[1]:.4f})")
            return coords

        except KeyError:
            # Handle rate limiting
            if result.get("info") == "CUQPS_HAS_EXCEEDED_THE_LIMIT":
                retry_count += 1
                logger.warning(
                    f"[Geocode] Rate limit exceeded, retrying ({retry_count}/{max_retries})..."
                )
                time.sleep(1)
                continue
            logger.error(f"[Geocode] Failed for address: {address}, response: {result}")
            raise KeyError(f"Geocoding failed for address: {address}, response: {result}")

    logger.error(f"[Geocode] All retries exhausted for address: {address}")
    raise KeyError(f"Geocoding failed after {max_retries} retries for address: {address}")


def parse_point_coordinates(point_string: str) -> Coordinates:
    """
    Extract coordinates from a WKT POINT string.

    Args:
        point_string: A WKT POINT string, e.g., "POINT(116.4074 39.9042)"

    Returns:
        A tuple of (longitude, latitude).

    Raises:
        ValueError: If the input string format is invalid.
    """
    pattern = r"POINT\(([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+)\)"
    match = re.search(pattern, point_string)

    if match:
        longitude = float(match.group(1))
        latitude = float(match.group(2))
        return (longitude, latitude)

    raise ValueError(f"Invalid POINT format: {point_string}")
