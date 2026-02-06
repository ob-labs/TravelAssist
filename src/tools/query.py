"""
Query Tool for OBMMS.

Provides vector search and geographic filtering capabilities
for finding travel attractions.
"""

from typing import Any, Dict, List, Optional

from pyobvector import ST_GeomFromText, st_dwithin
from sqlalchemy import Table, and_, func, text

from ..common import (
    FIELD_DEPARTURE,
    FIELD_DISTANCE,
    FIELD_SCORE,
    FIELD_SEASON,
    create_db_client,
    geocode,
    parse_distance,
    parse_season_str,
)
from ..common.config import get_config
from ..common.logger import get_logger
from ..llm.embedding import embedding
from .tool import Tool

logger = get_logger(__name__)


class QueryTool(Tool):
    """
    Query Tool for travel attraction search.

    This tool provides semantic search combined with geographic
    filtering to find travel attractions that match user requirements.
    """

    # Column configuration
    OUTPUT_COLUMNS = [
        "attraction_name",
        "address_text",
        "score",
        "season",
        "ticket",
    ]

    def __init__(
        self,
        table_name: str,
        topk: int,
        echo: bool = False,
        departure_field: str = FIELD_DEPARTURE,
        distance_field: str = FIELD_DISTANCE,
        score_field: str = FIELD_SCORE,
        season_field: str = FIELD_SEASON,
        **kwargs,
    ) -> None:
        """
        Initialize the Query Tool.

        Args:
            table_name: Name of the database table to search.
            topk: Maximum number of results to return.
            echo: Whether to echo SQL statements.
            departure_field: Field name for departure location.
            distance_field: Field name for search distance.
            score_field: Field name for score filter.
            season_field: Field name for season filter.
            **kwargs: Additional arguments for database client.

        Raises:
            ValueError: If required API keys are not configured.
        """
        logger.info(f"[QueryTool] Initializing with table={table_name}, topk={topk}")

        self._table_name = table_name
        self._topk = topk

        # Field mappings
        self._departure_field = departure_field
        self._distance_field = distance_field
        self._score_field = score_field
        self._season_field = season_field

        # Initialize database client
        logger.info("[QueryTool] Creating database client...")
        self._client = create_db_client(echo=echo, **kwargs)
        logger.info("[QueryTool] Database client created successfully")

        # Validate API key for geocoding
        cfg = get_config()
        self._amap_api_key = cfg.amap_api_key

        if not self._amap_api_key:
            logger.error("[QueryTool] Missing required API key")
            raise ValueError(
                "Required API key not configured. "
                "Please set AMAP_API_KEY environment variable."
            )

    @property
    def table_name(self) -> str:
        """Get the table name."""
        return self._table_name

    @property
    def topk(self) -> int:
        """Get the maximum number of results."""
        return self._topk

    def _build_where_clause(
        self,
        table: Table,
        departure_coords: tuple,
        distance_meters: float,
        score: int,
        season_mask: int,
    ) -> List:
        """
        Build the WHERE clause for the search query.

        Args:
            table: SQLAlchemy Table object.
            departure_coords: (latitude, longitude) tuple.
            distance_meters: Search radius in meters.
            score: Minimum score filter.
            season_mask: Season bitmask filter.

        Returns:
            List of WHERE clause conditions.
        """
        return [
            and_(
                text(f"score >= {score} AND season & {season_mask} = {season_mask}"),
                st_dwithin(
                    table.c["address"],
                    ST_GeomFromText(departure_coords, 4326),
                    distance_meters,
                ),
            ),
        ]

    def call(
        self,
        necessary_info: Dict[str, Any],
        summary: str,
        str_list: Optional[List[str]] = None,
        **kwargs,
    ) -> Any:
        """
        Search for attractions matching the given criteria.

        Args:
            necessary_info: Dictionary containing search parameters:
                - departure: Departure location string
                - distance: Search radius string (e.g., "10km")
                - score: Minimum score requirement
                - season: Season preference string
            summary: Summary text for semantic search.
            str_list: Optional list to store SQL statements.
            **kwargs: Additional arguments (unused).

        Returns:
            Database query result object.
        """
        logger.info(f"[QueryTool] Starting search with criteria: {necessary_info}")

        # Extract and convert parameters
        departure_str = necessary_info[self._departure_field]
        logger.info(f"[QueryTool] Geocoding departure: {departure_str}")
        departure_coords = geocode(departure_str)
        logger.debug(f"[QueryTool] Departure coordinates: {departure_coords}")

        distance_str = necessary_info[self._distance_field]
        distance_meters = parse_distance(distance_str)
        logger.info(f"[QueryTool] Distance: {distance_str} -> {distance_meters}m")

        season_str = necessary_info[self._season_field]
        season_mask = parse_season_str(season_str)
        logger.debug(f"[QueryTool] Season: {season_str} -> mask={season_mask}")

        score = necessary_info[self._score_field]
        logger.info(f"[QueryTool] Minimum score: {score}")

        # Generate embedding for semantic search via embedding module
        logger.info("[QueryTool] Generating embedding for summary...")
        summary_embedding = embedding([summary])[0]
        logger.debug(f"[QueryTool] Embedding dimension: {len(summary_embedding)}")

        # Get table reference
        table = Table(
            self._table_name,
            self._client.metadata_obj,
            autoload_with=self._client.engine,
        )

        # Build query
        where_clause = self._build_where_clause(
            table=table,
            departure_coords=departure_coords,
            distance_meters=distance_meters,
            score=score,
            season_mask=season_mask,
        )

        # Execute search
        logger.info(f"[QueryTool] Executing ANN search on table {self._table_name}...")
        results = self._client.post_ann_search(
            table_name=self._table_name,
            vec_data=summary_embedding,
            vec_column_name="intro_vec",
            distance_func=func.l2_distance,
            with_dist=False,
            topk=self._topk,
            output_column_names=self.OUTPUT_COLUMNS,
            extra_output_cols=[text("st_astext(address)")],
            where_clause=where_clause,
            str_list=str_list,
        )

        logger.info("[QueryTool] Search completed successfully")
        if str_list:
            logger.debug(f"[QueryTool] Generated SQL: {str_list[0][:200]}...")

        return results

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<QueryTool table={self._table_name} topk={self._topk}>"
