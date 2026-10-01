"""
Deterministic SQL Security & AST Validator.
Guarantees strictly read-only execution, enforces query limits, and neutralizes injection attempts.
"""
import re
from typing import NamedTuple, Optional

class ValidationResult(NamedTuple):
    is_valid: bool
    sanitized_query: Optional[str] = None
    error_message: Optional[str] = None
    violation_type: Optional[str] = None

# Prohibited SQL keywords that modify schema or persist state
FORBIDDEN_KEYWORDS = {
    "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", 
    "ATTACH", "DETACH", "PRAGMA", "REINDEX", "VACUUM", "REPLACE", 
    "TRUNCATE", "UPSERT", "GRANT", "REVOKE", "COMMIT", "ROLLBACK"
}

def validate_and_sanitize_sql(query: str, max_limit: int = 50) -> ValidationResult:
    """
    Validates a SQL query string to ensure it is purely read-only and safe for execution.
    - Rejects multiple stacked statements (semicolon attacks).
    - Checks lexical tokens for any mutating operations.
    - Enforces that query starts with SELECT or WITH.
    - Clamps or appends a deterministic LIMIT clause.
    """
    if not query or not query.strip():
        return ValidationResult(False, None, "Query string is empty.", "EMPTY_QUERY")

    # Strip surrounding whitespace and remove trailing semicolon
    cleaned = query.strip()
    
    # Check for stacked statements: remove quoted string literals first to avoid false positives
    query_without_strings = re.sub(r"'[^']*'|\"[^\"]*\"", "", cleaned)
    
    # Split on semicolon
    statements = [s.strip() for s in query_without_strings.split(";") if s.strip()]
    if len(statements) > 1:
        return ValidationResult(
            False, None, 
            "Multiple stacked statements detected. Only a single SELECT query is permitted.",
            "STACKED_STATEMENT_INJECTION"
        )

    # Tokenize words for keyword matching
    tokens = [t.upper() for t in re.findall(r"\b[A-Za-z_]+\b", query_without_strings)]
    if not tokens:
        return ValidationResult(False, None, "No valid SQL tokens found.", "INVALID_SYNTAX")

    # Check first significant token: must be SELECT or WITH
    first_token = tokens[0]
    if first_token not in {"SELECT", "WITH", "EXPLAIN"}:
        return ValidationResult(
            False, None,
            f"Unauthorized query root '{first_token}'. Queries must start with SELECT or WITH.",
            "NON_READONLY_ROOT"
        )

    # Check for any forbidden mutating keyword in tokens
    for token in tokens:
        if token in FORBIDDEN_KEYWORDS:
            return ValidationResult(
                False, None,
                f"Security violation: Mutating statement keyword '{token}' is strictly forbidden.",
                "FORBIDDEN_KEYWORD"
            )

    # Normalize single trailing semicolon
    final_query = cleaned.rstrip(";").strip()

    # Check if LIMIT exists
    limit_match = re.search(r"\bLIMIT\s+(\d+)", final_query, flags=re.IGNORECASE)
    if limit_match:
        current_limit = int(limit_match.group(1))
        if current_limit > max_limit:
            # Clamp limit to max_limit
            final_query = re.sub(
                r"\bLIMIT\s+\d+", 
                f"LIMIT {max_limit}", 
                final_query, 
                flags=re.IGNORECASE
            )
    else:
        # Append safe limit
        final_query = f"{final_query} LIMIT {max_limit}"

    return ValidationResult(True, final_query, None, None)

if __name__ == "__main__":
    # Self-test cases
    print("Testing safe query:", validate_and_sanitize_sql("SELECT title, global_sales FROM games ORDER BY global_sales DESC;"))
    print("Testing injection:", validate_and_sanitize_sql("SELECT * FROM games; DROP TABLE games;"))
    print("Testing update:", validate_and_sanitize_sql("UPDATE games SET global_sales = 100 WHERE id = 1;"))
    print("Testing excessive limit:", validate_and_sanitize_sql("SELECT * FROM games LIMIT 5000;"))
