"""
Validation helpers for OBMMS.

Provides strict type and range checks for values that originate from
untrusted sources, such as LLM output or client requests.
"""

from typing import Any, Dict

from .constants import FIELD_DEPARTURE, FIELD_DISTANCE, FIELD_SCORE, FIELD_SEASON

# Inclusive range accepted for the attraction score filter.
MIN_SCORE = 0
MAX_SCORE = 100

# Fields that must be plain strings (or null) in extracted travel info.
_TEXT_FIELDS = (FIELD_DEPARTURE, FIELD_DISTANCE, FIELD_SEASON)


def coerce_score(value: Any) -> int:
    """
    Coerce a score value into a bounded integer.

    Args:
        value: Raw score value, typically coming from an LLM response.

    Returns:
        The score as an int within [MIN_SCORE, MAX_SCORE].

    Raises:
        ValueError: If the value is not an integer score in range.
    """
    if isinstance(value, bool):
        raise ValueError(f"Invalid score: {value!r}")

    if isinstance(value, str):
        try:
            value = int(value.strip())
        except ValueError as e:
            raise ValueError(f"Invalid score: {value!r}") from e
    elif isinstance(value, float) and value.is_integer():
        value = int(value)

    if not isinstance(value, int):
        raise ValueError(f"Invalid score: {value!r}")

    if not MIN_SCORE <= value <= MAX_SCORE:
        raise ValueError(
            f"Score out of range [{MIN_SCORE}, {MAX_SCORE}]: {value}"
        )

    return value


def validate_extracted_info(raw: Any) -> Dict[str, Any]:
    """
    Validate LLM-extracted travel info against a field type whitelist.

    Unknown fields are dropped; a field with an unexpected type makes the
    whole payload invalid, so it never reaches the conversation state or
    query construction.

    Args:
        raw: Parsed JSON value returned by the LLM.

    Returns:
        A dict holding only the known fields with validated values.

    Raises:
        ValueError: If the payload is not an object or a field type is invalid.
    """
    if not isinstance(raw, dict):
        raise ValueError(
            f"Extracted info must be an object, got {type(raw).__name__}"
        )

    validated: Dict[str, Any] = {}

    for field in _TEXT_FIELDS:
        value = raw.get(field)
        if value is None:
            validated[field] = None
        elif isinstance(value, str):
            validated[field] = value
        else:
            raise ValueError(
                f"Invalid type for {field}: {type(value).__name__}"
            )

    score = raw.get(FIELD_SCORE)
    validated[FIELD_SCORE] = None if score is None else coerce_score(score)

    return validated
