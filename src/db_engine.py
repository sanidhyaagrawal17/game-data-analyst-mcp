"""
Read-Only SQLite Database Execution Engine.
Combines C-level read-only URI constraints with Python lexical validation and latency profiling.
"""
import sqlite3
import os
import time
from typing import Dict, Any, List
from .sql_validator import validate_and_sanitize_sql

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "games.db"))

class DatabaseEngine:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}. Run seed_data.py first.")
        # Formulate read-only URI
        # Using forward slashes for SQLite URI on Windows
        normalized_path = self.db_path.replace("\\", "/")
        self.uri = f"file:///{normalized_path}?mode=ro"

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.uri, uri=True, timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn

    def get_schema_metadata(self) -> Dict[str, Any]:
        """
        Extracts structural schema metadata, categorical sets, and column descriptions.
        """
        schema_info = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row["name"] for row in cursor.fetchall()]

            for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [{"name": r["name"], "type": r["type"], "pk": bool(r["pk"])} for r in cursor.fetchall()]
                
                # Fetch row count
                cursor.execute(f"SELECT COUNT(*) as cnt FROM {table};")
                count = cursor.fetchone()["cnt"]

                schema_info[table] = {
                    "row_count": count,
                    "columns": columns
                }

            # Fetch distinct categorical distributions for games table
            cursor.execute("SELECT DISTINCT genre FROM games ORDER BY genre;")
            genres = [r["genre"] for r in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT platform FROM games ORDER BY platform;")
            platforms = [r["platform"] for r in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT publisher FROM games ORDER BY publisher;")
            publishers = [r["publisher"] for r in cursor.fetchall()]

            schema_info["categorical_vocabularies"] = {
                "genres": genres,
                "platforms": platforms,
                "top_publishers": publishers[:10]
            }

        return schema_info

    def execute_safe_query(self, query: str) -> Dict[str, Any]:
        """
        Executes a validated read-only SQL query with latency tracking and row clamping.
        """
        validation = validate_and_sanitize_sql(query, max_limit=50)
        if not validation.is_valid:
            return {
                "success": False,
                "error": validation.error_message,
                "violation_type": validation.violation_type,
                "rows": [],
                "row_count": 0,
                "latency_ms": 0.0
            }

        sanitized_sql = validation.sanitized_query
        start_time = time.perf_counter()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sanitized_sql)
                rows = cursor.fetchall()
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)

                dict_rows = [dict(r) for r in rows]
                return {
                    "success": True,
                    "sanitized_query": sanitized_sql,
                    "rows": dict_rows,
                    "row_count": len(dict_rows),
                    "latency_ms": elapsed_ms,
                    "error": None
                }
        except sqlite3.Error as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
            return {
                "success": False,
                "error": f"SQLite Execution Error: {str(e)}",
                "violation_type": "SQLITE_EXEC_ERROR",
                "sanitized_query": sanitized_sql,
                "rows": [],
                "row_count": 0,
                "latency_ms": elapsed_ms
            }

if __name__ == "__main__":
    engine = DatabaseEngine()
    print("Schema Metadata:", engine.get_schema_metadata())
    res = engine.execute_safe_query("SELECT title, publisher, global_sales FROM games WHERE publisher = 'Electronic Arts' ORDER BY global_sales DESC LIMIT 5;")
    print("EA Top Titles Query:", res)
