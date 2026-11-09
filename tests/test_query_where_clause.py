"""
Tests for QueryTool WHERE clause construction.

These tests exercise clause building only and do not need a database.
"""

import unittest

from sqlalchemy import Column, Integer, MetaData, Table

from src.tools import QueryTool


class TestBuildWhereClause(unittest.TestCase):
    """Tests for QueryTool._build_where_clause."""

    def setUp(self):
        self.table = Table(
            "travel_assist",
            MetaData(),
            Column("score", Integer),
            Column("season", Integer),
            Column("address", Integer),
        )
        self.tool = QueryTool.__new__(QueryTool)

    def _build(self, score):
        return self.tool._build_where_clause(
            table=self.table,
            departure_coords=(30.25, 120.16),
            distance_meters=10000.0,
            score=score,
            season_mask=4,
        )

    def test_score_is_bound_not_interpolated(self):
        clause = self._build("90")
        sql = str(clause[0].compile())

        self.assertIn(":score", sql)
        self.assertNotIn("90", sql)

    def test_numeric_string_score_is_accepted(self):
        clause = self._build("90")

        self.assertEqual(len(clause), 1)

    def test_injection_payload_is_rejected(self):
        for value in ("90 OR 1=1", "90; DROP TABLE travel_assist", "abs(score)"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self._build(value)


if __name__ == "__main__":
    unittest.main()
