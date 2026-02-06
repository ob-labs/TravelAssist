"""
Distance utilities for OBMMS.

Provides distance parsing and conversion functions.
"""

import re
from typing import Optional

# Unit conversion factors to meters
UNIT_CONVERSIONS = {
    "m": 1.0,
    "km": 1000.0,
    "cm": 0.01,
    "mm": 0.001,
}


def parse_distance(distance_str: str) -> float:
    """
    Parse a distance string into meters.

    Args:
        distance_str: A string containing a number and unit (e.g., "10km", "500m").

    Returns:
        The distance in meters as a float.

    Raises:
        ValueError: If the format is invalid or the unit is unsupported.

    Examples:
        >>> parse_distance("10km")
        10000.0
        >>> parse_distance("500m")
        500.0
        >>> parse_distance("50.5km")
        50500.0
    """
    if not distance_str:
        raise ValueError("Distance string cannot be empty")

    # Pattern to match number and unit
    pattern = r"^([\d.]+)\s*([a-zA-Z]+)$"
    match = re.match(pattern, distance_str.strip())

    if not match:
        raise ValueError(f"Invalid distance format: {distance_str}")

    value_str, unit = match.groups()

    try:
        value = float(value_str)
    except ValueError:
        raise ValueError(f"Invalid numeric value in distance: {value_str}")

    unit_lower = unit.lower()
    if unit_lower not in UNIT_CONVERSIONS:
        raise ValueError(f"Unsupported unit: {unit}. Supported units: {list(UNIT_CONVERSIONS.keys())}")

    return value * UNIT_CONVERSIONS[unit_lower]


def format_distance(meters: float, unit: str = "km") -> str:
    """
    Format a distance in meters to a string with the specified unit.

    Args:
        meters: The distance in meters.
        unit: The target unit (default: "km").

    Returns:
        A formatted distance string.

    Raises:
        ValueError: If the unit is unsupported.
    """
    unit_lower = unit.lower()
    if unit_lower not in UNIT_CONVERSIONS:
        raise ValueError(f"Unsupported unit: {unit}")

    value = meters / UNIT_CONVERSIONS[unit_lower]
    
    # Format with appropriate precision
    if value == int(value):
        return f"{int(value)}{unit}"
    return f"{value:.2f}{unit}"
