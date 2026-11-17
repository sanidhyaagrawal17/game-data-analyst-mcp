import pytest
from src.sql_validator import validate_and_sanitize_sql

def test_valid_select_query():
    query = "SELECT title, global_sales FROM games WHERE publisher = 'Electronic Arts'"
    result = validate_and_sanitize_sql(query, max_limit=50)
    assert result.is_valid is True
    assert result.error_message is None
    assert "LIMIT 50" in result.sanitized_query

def test_rejects_mutating_statements():
    mutating_queries = [
        "DROP TABLE games",
        "DELETE FROM games WHERE id = 1",
        "UPDATE games SET global_sales = 999 WHERE id = 1",
        "INSERT INTO games (title) VALUES ('Hacked Game')",
        "ALTER TABLE games ADD COLUMN exploit TEXT"
    ]
    for q in mutating_queries:
        res = validate_and_sanitize_sql(q)
        assert res.is_valid is False
        assert res.violation_type in {"NON_READONLY_ROOT", "FORBIDDEN_KEYWORD"}

def test_rejects_stacked_query_injection():
    stacked = "SELECT * FROM games; DROP TABLE games;"
    res = validate_and_sanitize_sql(stacked)
    assert res.is_valid is False
    assert res.violation_type == "STACKED_STATEMENT_INJECTION"
    assert "Multiple stacked statements" in res.error_message

def test_clamps_excessive_limit():
    query = "SELECT * FROM games LIMIT 1000"
    res = validate_and_sanitize_sql(query, max_limit=50)
    assert res.is_valid is True
    assert "LIMIT 50" in res.sanitized_query

def test_preserves_smaller_limit():
    query = "SELECT * FROM games LIMIT 10"
    res = validate_and_sanitize_sql(query, max_limit=50)
    assert res.is_valid is True
    assert "LIMIT 10" in res.sanitized_query

def test_rejects_empty_query():
    assert validate_and_sanitize_sql("").is_valid is False
    assert validate_and_sanitize_sql("   ").is_valid is False
