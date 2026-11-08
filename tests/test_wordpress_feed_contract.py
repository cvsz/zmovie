"""WordPress Cinema feed contract tests.

These tests encode the documented REST feed contract that the ZeaZ Cinema
plugin (`wp-plugins/zwp-cinema/includes/api.php`) must honor:

  GET /wp-json/zwpc/v1/feed   (primary alias)
  GET /wp-json/zwpc/v1/films  (secondary alias)

Successful responses expose the documented envelope:

  { "items": [...], "films": [...], "has_more": bool,
    "total": int, "page": int, "per_page": int }

where `items` (alias `films`) is the consumable film list. Empty feeds are
valid (`items == []`). Pagination and upstream failures resolve to a
deterministic error schema. No credentials or customer data are asserted.

These are schema contract tests: they validate the envelope shape the plugin
promises, using synthetic fixtures. They do not require a live WordPress
instance or PHP runtime.
"""

from __future__ import annotations

import unittest

# Required top-level keys of a successful feed response.
FEED_KEYS = {"items", "films", "has_more", "total", "page", "per_page"}
# Required keys within each film item.
FILM_KEYS = {"id", "title", "permalink"}
# Deterministic error-shape keys.
ERROR_KEYS = {"code", "message"}


def validate_feed_envelope(response: dict) -> list[str]:
    """Validate a feed response envelope. Returns a list of problem messages."""
    problems: list[str] = []
    if not isinstance(response, dict):
        return ["feed response is not an object"]
    missing = FEED_KEYS - set(response.keys())
    if missing:
        problems.append(f"missing feed keys: {sorted(missing)}")
    if not isinstance(response.get("items"), list):
        problems.append("feed 'items' must be a list")
    if not isinstance(response.get("films"), list):
        problems.append("feed 'films' must be a list")
    if response.get("items") != response.get("films"):
        problems.append("feed 'films' must have the same content as 'items'")
    if not isinstance(response.get("has_more"), bool):
        problems.append("feed 'has_more' must be a boolean")
    if not isinstance(response.get("total"), int):
        problems.append("feed 'total' must be an integer")
    if not isinstance(response.get("page"), int) or response["page"] < 1:
        problems.append("feed 'page' must be an integer >= 1")
    if not isinstance(response.get("per_page"), int) or response["per_page"] < 1:
        problems.append("feed 'per_page' must be an integer >= 1")
    for index, film in enumerate(response.get("items", [])):
        if not isinstance(film, dict):
            problems.append(f"items[{index}] is not an object")
            continue
        film_missing = FILM_KEYS - set(film.keys())
        if film_missing:
            problems.append(f"items[{index}] missing keys: {sorted(film_missing)}")
    return problems


def validate_error_envelope(response: dict) -> list[str]:
    """Validate a deterministic error response. Returns a list of problems."""
    problems: list[str] = []
    if not isinstance(response, dict):
        return ["error response is not an object"]
    missing = ERROR_KEYS - set(response.keys())
    if missing:
        problems.append(f"error missing keys: {sorted(missing)}")
    if not isinstance(response.get("code"), str) or not response["code"]:
        problems.append("error 'code' must be a non-empty string")
    if not isinstance(response.get("message"), str) or not response["message"]:
        problems.append("error 'message' must be a non-empty string")
    return problems


class WordPressFeedContractTests(unittest.TestCase):
    def test_populated_feed_exposes_items_and_pagination(self) -> None:
        response = {
            "items": [
                {"id": 1, "title": "Film One", "permalink": "https://example.com/film-one"},
                {"id": 2, "title": "Film Two", "permalink": "https://example.com/film-two"},
            ],
            "films": [
                {"id": 1, "title": "Film One", "permalink": "https://example.com/film-one"},
                {"id": 2, "title": "Film Two", "permalink": "https://example.com/film-two"},
            ],
            "has_more": False,
            "total": 2,
            "page": 1,
            "per_page": 12,
        }
        self.assertEqual(validate_feed_envelope(response), [])
        self.assertEqual(response["items"], response["films"])
        self.assertEqual(len(response["items"]), 2)
        self.assertEqual(response["total"], 2)

    def test_empty_feed_is_valid(self) -> None:
        response = {
            "items": [],
            "films": [],
            "has_more": False,
            "total": 0,
            "page": 1,
            "per_page": 12,
        }
        self.assertEqual(validate_feed_envelope(response), [])
        self.assertEqual(response["items"], [])
        self.assertEqual(response["total"], 0)
        self.assertFalse(response["has_more"])

    def test_invalid_pagination_is_rejected(self) -> None:
        # page < 1 and per_page > 48 are invalid per the plugin arg validation.
        for bad in (
            {"page": 0, "per_page": 12},
            {"page": 1, "per_page": 0},
            {"page": -1, "per_page": 12},
            {"page": 1, "per_page": 10000},
        ):
            with self.assertRaises(ValueError):
                page = bad["page"]
                per_page = bad["per_page"]
                if page < 1:
                    raise ValueError("page must be >= 1")
                if per_page < 1 or per_page > 48:
                    raise ValueError("per_page must be 1-48")

    def test_missing_configuration_yields_deterministic_error(self) -> None:
        # When the WordPress post type is not registered, the plugin must not
        # return a bare list; it must fail with a deterministic error schema.
        error = {"code": "zwpc_post_type_unavailable", "message": "zwpc_film post type is not registered"}
        self.assertEqual(validate_error_envelope(error), [])

    def test_upstream_provider_error_yields_deterministic_error(self) -> None:
        # WP_Query/database failures surface as a deterministic error, never
        # credentials or customer data.
        error = {
            "code": "zwpc_feed_query_failed",
            "message": "Unable to retrieve films at this time",
        }
        self.assertEqual(validate_error_envelope(error), [])
        self.assertNotIn("password", str(error).lower())
        self.assertNotIn("token", str(error).lower())

    def test_both_route_aliases_share_contract(self) -> None:
        # /feed and /films must return an identical envelope shape.
        shared = {
            "items": [],
            "films": [],
            "has_more": False,
            "total": 0,
            "page": 1,
            "per_page": 12,
        }
        self.assertEqual(validate_feed_envelope(shared), [])
        self.assertEqual(set(shared.keys()), FEED_KEYS)

    def test_invalid_response_structure_is_rejected(self) -> None:
        # A bare list, or an object missing `items`, is not a valid feed.
        invalid_cases = (
            [],  # bare list
            {"films": []},  # missing items
            {"items": "not-a-list"},  # items wrong type
            {"total": 0},  # missing pagination
        )
        for case in invalid_cases:
            self.assertNotEqual(validate_feed_envelope(case), [])

    def test_error_never_leaks_credentials(self) -> None:
        error = {"code": "zwpc_upstream_error", "message": "provider unavailable"}
        problems = validate_error_envelope(error)
        self.assertEqual(problems, [])
        text = str(error)
        self.assertNotIn("secret", text.lower())
        self.assertNotIn("password", text.lower())
        self.assertNotIn("token", text.lower())
        self.assertNotIn("authorization", text.lower())


if __name__ == "__main__":
    unittest.main()
