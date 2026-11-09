"""
Tests for shared validation helpers.

Covers score coercion and the extracted-info field type whitelist.
"""

import unittest

from src.common import (
    MAX_SCORE,
    MIN_SCORE,
    coerce_score,
    validate_extracted_info,
)
from src.common.constants import (
    FIELD_DEPARTURE,
    FIELD_DISTANCE,
    FIELD_SCORE,
    FIELD_SEASON,
)


class TestCoerceScore(unittest.TestCase):
    """Tests for coerce_score."""

    def test_accepts_int(self):
        self.assertEqual(coerce_score(90), 90)

    def test_accepts_boundaries(self):
        self.assertEqual(coerce_score(MIN_SCORE), MIN_SCORE)
        self.assertEqual(coerce_score(MAX_SCORE), MAX_SCORE)

    def test_accepts_numeric_string(self):
        self.assertEqual(coerce_score("96"), 96)

    def test_accepts_integral_float(self):
        self.assertEqual(coerce_score(90.0), 90)

    def test_rejects_out_of_range(self):
        for value in (MAX_SCORE + 1, MIN_SCORE - 1):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    coerce_score(value)

    def test_rejects_non_numeric_values(self):
        for value in (None, True, 90.5, [], {}, "", "90 OR 1=1", "90; DROP TABLE t"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    coerce_score(value)


class TestValidateExtractedInfo(unittest.TestCase):
    """Tests for validate_extracted_info."""

    def test_accepts_valid_payload(self):
        validated = validate_extracted_info(
            {
                FIELD_DEPARTURE: "杭州",
                FIELD_DISTANCE: "10km",
                FIELD_SCORE: 90,
                FIELD_SEASON: "秋",
            }
        )

        self.assertEqual(validated[FIELD_DEPARTURE], "杭州")
        self.assertEqual(validated[FIELD_DISTANCE], "10km")
        self.assertEqual(validated[FIELD_SCORE], 90)
        self.assertEqual(validated[FIELD_SEASON], "秋")

    def test_accepts_null_fields(self):
        validated = validate_extracted_info(
            {
                FIELD_DEPARTURE: None,
                FIELD_DISTANCE: None,
                FIELD_SCORE: None,
                FIELD_SEASON: None,
            }
        )

        self.assertIsNone(validated[FIELD_DEPARTURE])
        self.assertIsNone(validated[FIELD_SCORE])

    def test_drops_unknown_fields(self):
        validated = validate_extracted_info({"unknown": "value"})

        self.assertNotIn("unknown", validated)
        self.assertEqual(
            set(validated),
            {FIELD_DEPARTURE, FIELD_DISTANCE, FIELD_SCORE, FIELD_SEASON},
        )

    def test_rejects_non_object_payload(self):
        for value in (None, [], "json", 1):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_extracted_info(value)

    def test_rejects_wrong_text_field_type(self):
        for field in (FIELD_DEPARTURE, FIELD_DISTANCE, FIELD_SEASON):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    validate_extracted_info({field: 123})

    def test_rejects_invalid_score(self):
        with self.assertRaises(ValueError):
            validate_extracted_info({FIELD_SCORE: "90 OR 1=1"})


if __name__ == "__main__":
    unittest.main()
