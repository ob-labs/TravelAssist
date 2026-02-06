"""
Database configuration for OBMMS.

Provides database connection configuration and client creation.
"""

from typing import Any, Optional

from pyobvector import ObVecClient, POINT, VECTOR, VectorIndex
from sqlalchemy import Column, Index, Integer, JSON, String
from sqlalchemy.dialects.mysql import LONGTEXT

from .config import DatabaseConfig, get_config
from .logger import get_logger

logger = get_logger(__name__)


def create_db_client(
    config: Optional[DatabaseConfig] = None,
    echo: bool = False,
    **kwargs: Any,
) -> ObVecClient:
    """
    Create an OceanBase vector database client.

    Args:
        config: Database configuration. If None, creates from application config.
        echo: Whether to echo SQL statements.
        **kwargs: Additional arguments to pass to ObVecClient.

    Returns:
        An ObVecClient instance.
    """
    logger.info("[Database] Creating database client...")

    if config is None:
        config = get_config().database_config
        logger.debug(
            f"[Database] Config from app: host={config.host}, port={config.port}, db={config.database}"
        )

    connect_args = config.get_connect_args()

    if connect_args:
        logger.info("[Database] SSL connection enabled")

    client_kwargs = {
        "uri": config.uri,
        "user": config.user,
        "password": "***",  # Don't log password
        "db_name": config.database,
        "echo": echo,
        **kwargs,
    }

    logger.debug(
        f"[Database] Connection params: uri={config.uri}, user={config.user}, db={config.database}"
    )

    # Restore actual password for connection
    client_kwargs["password"] = config.password

    if connect_args:
        client_kwargs["connect_args"] = connect_args

    client = ObVecClient(**client_kwargs)
    logger.info("[Database] Database client created successfully")

    return client


def create_table(table_name: str | None = None) -> None:
    """
    Create the OBMMS attractions table if it doesn't exist.

    Args:
        table_name: Name of the table to create.
    """
    if table_name is None:
        table_name = get_config().default_table_name
    client = create_db_client()

    # Check if table already exists
    if client.check_table_exists(table_name=table_name):
        logger.info(f"Table {table_name} already exists")
        return

    # Define columns
    columns = [
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("attraction_name", String(1024), nullable=False),
        Column("address_text", LONGTEXT, nullable=False),
        Column("address", POINT(srid=4326), nullable=False),
        Column("intro", LONGTEXT, nullable=False),
        Column("intro_vec", VECTOR(384), nullable=False),
        Column("img_url", String(1024), nullable=False),
        Column("score", Integer, nullable=False),
        Column("season", Integer, nullable=False),
        Column("ticket", JSON),
    ]

    # Define indexes
    indexes = [
        Index("address_idx", "address"),
        VectorIndex(
            "intro_vidx",
            "intro_vec",
            params="distance=l2, type=hnsw, lib=vsag",
        ),
    ]

    # Create table
    client.create_table(
        table_name=table_name,
        columns=columns,
        indexes=indexes,
    )

    logger.info(f"Created table {table_name}")
