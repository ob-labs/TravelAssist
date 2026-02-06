"""
Text processing utilities for OBMMS.

Provides text parsing and formatting functions.
"""

import json
import re
from typing import Any, Dict, Optional

from .logger import get_logger

logger = get_logger(__name__)


def extract_json_from_response(response_text: str) -> Dict[str, Any]:
    """
    Extract and parse JSON from an LLM response.

    This function handles common issues with LLM responses such as:
    - Extra whitespace and newlines
    - Markdown code blocks
    - Leading/trailing text

    Args:
        response_text: The raw response text from the LLM.

    Returns:
        The parsed JSON as a dictionary.

    Raises:
        ValueError: If no valid JSON could be extracted.
    """
    if not response_text:
        raise ValueError("Response text is empty")

    # Clean up the text
    cleaned_text = response_text.strip()

    # Try to extract JSON from markdown code blocks
    code_block_pattern = r"```(?:json)?\s*\n?([\s\S]*?)\n?```"
    code_block_match = re.search(code_block_pattern, cleaned_text)
    if code_block_match:
        cleaned_text = code_block_match.group(1).strip()

    # Try to find JSON object in the text
    json_pattern = r"\{[\s\S]*\}"
    json_match = re.search(json_pattern, cleaned_text)
    if json_match:
        cleaned_text = json_match.group()

    # Remove extra whitespace within the JSON
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)
    cleaned_text = cleaned_text.replace(" }", "}").replace("{ ", "{")
    cleaned_text = cleaned_text.replace(" ,", ",").replace(", ", ",")
    cleaned_text = cleaned_text.replace(" :", ":").replace(": ", ":")

    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}, text: {cleaned_text[:200]}...")
        raise ValueError(f"Failed to extract valid JSON from response: {e}")


def replace_folded_vectors(text: str) -> str:
    """
    Replace vector data in SQL strings with a placeholder for readability.

    Args:
        text: The text containing SQL with vector data.

    Returns:
        The text with vector data replaced by '<FOLDED VECTOR DATA>'.
    """
    return re.sub(r"'\[.*?\]'", "<FOLDED VECTOR DATA>", text)


def format_numbered_list(items: list, start: int = 1) -> str:
    """
    Format a list of items as a numbered list string.

    Args:
        items: The list of items to format.
        start: The starting number (default: 1).

    Returns:
        A formatted numbered list string.

    Examples:
        >>> format_numbered_list(["item1", "item2"])
        '1. item1\\n2. item2\\n'
    """
    lines = [f"{i}. {item}" for i, item in enumerate(items, start=start)]
    return "\n".join(lines) + "\n" if lines else ""
