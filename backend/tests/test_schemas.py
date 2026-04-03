"""Validation tests for Pydantic schemas (QueryRequest, QueryResponse)."""

import pytest
from pydantic import ValidationError

from app.schemas import QueryRequest, QueryResponse


class TestQueryRequest:
    """Boundary-value and edge-case tests for QueryRequest.question field."""

    # --- Valid inputs ---

    def test_minimum_length_exactly_3(self) -> None:
        req = QueryRequest(question="abc")
        assert req.question == "abc"

    def test_maximum_length_exactly_500(self) -> None:
        question = "a" * 500
        req = QueryRequest(question=question)
        assert len(req.question) == 500

    def test_typical_question(self) -> None:
        req = QueryRequest(question="Who led the league in home runs in 2023?")
        assert req.question.startswith("Who")

    def test_question_with_special_characters(self) -> None:
        """Special chars within valid length should be accepted."""
        req = QueryRequest(question="Who hit > .300 in '23?")
        assert req.question is not None

    # --- Invalid: too short ---

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(question="")
        errors = exc_info.value.errors()
        assert any("min_length" in str(e) or "string_too_short" in e["type"] for e in errors)

    def test_one_char_raises(self) -> None:
        with pytest.raises(ValidationError):
            QueryRequest(question="x")

    def test_two_chars_raises(self) -> None:
        with pytest.raises(ValidationError):
            QueryRequest(question="xy")

    # --- Invalid: too long ---

    def test_501_chars_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(question="a" * 501)
        errors = exc_info.value.errors()
        assert any("max_length" in str(e) or "string_too_long" in e["type"] for e in errors)

    def test_very_long_string_raises(self) -> None:
        with pytest.raises(ValidationError):
            QueryRequest(question="z" * 10_000)

    # --- Invalid: wrong type ---

    def test_none_raises(self) -> None:
        with pytest.raises(ValidationError):
            QueryRequest(question=None)  # type: ignore[arg-type]

    def test_integer_raises(self) -> None:
        with pytest.raises(ValidationError):
            QueryRequest(question=42)  # type: ignore[arg-type]

    # --- Boundary: exact length neighbours ---

    def test_length_2_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            QueryRequest(question="ab")

    def test_length_3_is_accepted(self) -> None:
        QueryRequest(question="abc")

    def test_length_500_is_accepted(self) -> None:
        QueryRequest(question="b" * 500)

    def test_length_501_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            QueryRequest(question="b" * 501)


class TestQueryResponse:
    """Basic structural tests for QueryResponse."""

    def test_valid_response(self) -> None:
        resp = QueryResponse(
            question="Who leads in HRs?",
            sql="SELECT * FROM batting_stats",
            result=[{"home_runs": 62}],
            answer="Aaron Judge led with 62.",
        )
        assert resp.question == "Who leads in HRs?"
        assert resp.sql == "SELECT * FROM batting_stats"
        assert resp.result == [{"home_runs": 62}]
        assert resp.answer == "Aaron Judge led with 62."

    def test_empty_result_list_is_valid(self) -> None:
        resp = QueryResponse(
            question="Who leads?",
            sql="SELECT 1",
            result=[],
            answer="No results.",
        )
        assert resp.result == []

    def test_missing_field_raises(self) -> None:
        with pytest.raises(ValidationError):
            QueryResponse(  # type: ignore[call-arg]
                question="test",
                sql="SELECT 1",
                result=[],
                # answer is missing
            )
