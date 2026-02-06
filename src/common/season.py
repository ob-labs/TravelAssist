"""
Season utilities for OBMMS.

Provides season parsing and constants for travel planning.
"""

# Season bit flags
SEASON_SPRING = 1       # 0001
SEASON_SUMMER = 1 << 1  # 0010
SEASON_AUTUMN = 1 << 2  # 0100
SEASON_WINTER = 1 << 3  # 1000
ALL_SEASONS = (1 << 4) - 1  # 1111 = 15


def parse_season_str(season_str: str) -> int:
    """
    Parse a season string into a bitmask representation.

    The season string can contain Chinese characters for seasons:
    - 春 (Spring)
    - 夏 (Summer)
    - 秋 (Autumn)
    - 冬 (Winter)
    - 四季/全年 (All seasons)

    Args:
        season_str: A string containing season indicators.

    Returns:
        An integer bitmask representing the seasons.
        - Bit 0: Spring
        - Bit 1: Summer
        - Bit 2: Autumn
        - Bit 3: Winter

    Examples:
        >>> parse_season_str("春夏")
        3  # 0011
        >>> parse_season_str("四季皆宜")
        15  # 1111
        >>> parse_season_str("秋")
        4  # 0100
    """
    # Handle all seasons keywords
    if "四季" in season_str or "全年" in season_str:
        return ALL_SEASONS

    result = 0

    if "春" in season_str:
        result |= SEASON_SPRING
    if "夏" in season_str:
        result |= SEASON_SUMMER
    if "秋" in season_str:
        result |= SEASON_AUTUMN
    if "冬" in season_str:
        result |= SEASON_WINTER

    # Default to all seasons if no season specified
    return result if result != 0 else ALL_SEASONS


def season_mask_to_str(mask: int) -> str:
    """
    Convert a season bitmask to a human-readable string.

    Args:
        mask: The season bitmask.

    Returns:
        A string representation of the seasons.
    """
    if mask == ALL_SEASONS:
        return "四季皆宜"

    seasons = []
    if mask & SEASON_SPRING:
        seasons.append("春")
    if mask & SEASON_SUMMER:
        seasons.append("夏")
    if mask & SEASON_AUTUMN:
        seasons.append("秋")
    if mask & SEASON_WINTER:
        seasons.append("冬")

    return "".join(seasons) if seasons else "四季皆宜"
