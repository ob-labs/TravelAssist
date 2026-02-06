"""
Embedding utilities for TravelAssist.

Provides text embedding generation via DashScope API.
"""

from http import HTTPStatus
from typing import List

import dashscope

from src.common.config import get_config
from pyseekdb import get_default_embedding_function


def embedding(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.
    """
    return default_embedding(texts)

def tongyi_embedding(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors.

    Raises:
        ValueError: If embedding generation fails.
    """
    response = dashscope.TextEmbedding.call(
        model=dashscope.TextEmbedding.Models.text_embedding_v3,
        input=texts,
        api_key=get_config().dashscope_api_key,
    )

    if response.status_code == HTTPStatus.OK:
        return [emb["embedding"] for emb in response.output["embeddings"]]

    raise ValueError(f"Embedding generation failed: {response}")


default_embedding_function = get_default_embedding_function()

def default_embedding(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings using the default pyseekdb embedding function.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors.

    Raises:
        ValueError: If embedding generation fails.
    """
    try:
        return default_embedding_function(texts)
    except Exception as e:
        raise ValueError(f"Default embedding generation failed: {e}")

