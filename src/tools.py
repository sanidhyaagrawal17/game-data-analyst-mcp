"""
Tool Definitions exposing Model Context Protocol (MCP) compliant interfaces for Game Data Analysis.
"""
from typing import Dict, Any, List, Optional
from .db_engine import DatabaseEngine

engine = DatabaseEngine()

def get_database_schema() -> Dict[str, Any]:
    """
    Returns full database schema, column definitions, and distinct categorical vocabularies
    to ground LLM query formulation and prevent hallucinated column names.
    """
    metadata = engine.get_schema_metadata()
    return {
        "success": True,
        "tables": metadata,
        "latency_ms": 0.5
    }

def execute_safe_sql(query: str) -> Dict[str, Any]:
    """
    Executes a read-only SQL query over the video games sales database.
    Query is automatically sanitized, validated against injection, and capped to 50 rows.
    """
    return engine.execute_safe_query(query)

def generate_trend_chart_data(
    group_by: str,
    metric: str = "global_sales",
    agg_func: str = "SUM",
    limit: int = 10
) -> Dict[str, Any]:
    """
    Generates structured aggregation payload for rendering bar and line charts in frontend interfaces.
    - group_by: column to aggregate by ('genre', 'platform', 'year', 'publisher')
    - metric: numeric column ('global_sales', 'na_sales', 'eu_sales', 'critic_score', 'user_score')
    - agg_func: aggregation function ('SUM', 'AVG', 'COUNT', 'MAX', 'MIN')
    """
    valid_group_cols = {"genre", "platform", "year", "publisher"}
    valid_metrics = {"global_sales", "na_sales", "eu_sales", "jp_sales", "other_sales", "critic_score", "user_score"}
    valid_aggs = {"SUM", "AVG", "COUNT", "MAX", "MIN"}

    if group_by.lower() not in valid_group_cols:
        return {"success": False, "error": f"Invalid group_by '{group_by}'. Choose from {valid_group_cols}"}
    if metric.lower() not in valid_metrics:
        return {"success": False, "error": f"Invalid metric '{metric}'. Choose from {valid_metrics}"}
    if agg_func.upper() not in valid_aggs:
        return {"success": False, "error": f"Invalid agg_func '{agg_func}'. Choose from {valid_aggs}"}

    safe_group = group_by.lower()
    safe_metric = metric.lower()
    safe_agg = agg_func.upper()
    safe_limit = min(max(1, limit), 25)

    sql = f"""
    SELECT {safe_group} as label, ROUND({safe_agg}({safe_metric}), 2) as value, COUNT(*) as sample_count
    FROM games
    WHERE {safe_group} IS NOT NULL AND {safe_metric} IS NOT NULL
    GROUP BY {safe_group}
    ORDER BY value DESC
    LIMIT {safe_limit}
    """
    result = engine.execute_safe_query(sql)
    if result["success"]:
        return {
            "success": True,
            "chart_type": "bar" if safe_group != "year" else "line",
            "x_axis": safe_group,
            "y_axis": f"{safe_agg}({safe_metric})",
            "data": result["rows"],
            "telemetry": {
                "rows_analyzed": result["row_count"],
                "latency_ms": result["latency_ms"]
            }
        }
    return result

def get_publisher_benchmarks(publishers: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Computes comparative publisher telemetry across portfolio size, total revenue,
    mean critic reception, and active studio infrastructure.
    """
    where_clause = ""
    if publishers and len(publishers) > 0:
        escaped_pubs = [f"'{p.replace('\'', '\'\'')}'" for p in publishers]
        where_clause = f"WHERE g.publisher IN ({', '.join(escaped_pubs)})"

    sql = f"""
    SELECT 
        g.publisher,
        t.founded_year,
        t.headquarters,
        t.active_studios,
        t.primary_engine,
        COUNT(g.id) as total_titles,
        ROUND(SUM(g.global_sales), 2) as cumulative_global_sales_m,
        ROUND(AVG(g.critic_score), 1) as avg_critic_score,
        ROUND(AVG(g.user_score), 2) as avg_user_score
    FROM games g
    LEFT JOIN publisher_telemetry t ON g.publisher = t.publisher
    {where_clause}
    GROUP BY g.publisher
    ORDER BY cumulative_global_sales_m DESC
    LIMIT 15
    """
    return engine.execute_safe_query(sql)

# Registry of MCP Tool Specifications
TOOL_DEFINITIONS = [
    {
        "name": "get_database_schema",
        "description": "Inspect SQLite schema, tables, column definitions, and distinct categorical values for video games and publishers.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "execute_safe_sql",
        "description": "Execute a read-only SQL query over the video games sales database. Mutating statements and multiple statements are rejected.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The read-only SQL query to execute (e.g. SELECT title, global_sales FROM games WHERE genre='Sports' ORDER BY global_sales DESC LIMIT 10)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "generate_trend_chart_data",
        "description": "Generate aggregated structured chart data for frontend visualization (bar or line charts) by genre, platform, year, or publisher.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "group_by": {"type": "string", "enum": ["genre", "platform", "year", "publisher"]},
                "metric": {"type": "string", "enum": ["global_sales", "na_sales", "eu_sales", "jp_sales", "other_sales", "critic_score", "user_score"], "default": "global_sales"},
                "agg_func": {"type": "string", "enum": ["SUM", "AVG", "COUNT", "MAX", "MIN"], "default": "SUM"},
                "limit": {"type": "integer", "default": 10}
            },
            "required": ["group_by"]
        }
    },
    {
        "name": "get_publisher_benchmarks",
        "description": "Retrieve comprehensive publisher performance analytics, combining sales volume, critic reception, and studio telemetry.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "publishers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of publisher names to filter (e.g. ['Electronic Arts', 'Activision', 'Nintendo'])"
                }
            }
        }
    }
]

def dispatch_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Central dispatcher for tool execution.
    """
    if name == "get_database_schema":
        return get_database_schema()
    elif name == "execute_safe_sql":
        return execute_safe_sql(arguments.get("query", ""))
    elif name == "generate_trend_chart_data":
        return generate_trend_chart_data(
            group_by=arguments.get("group_by", "genre"),
            metric=arguments.get("metric", "global_sales"),
            agg_func=arguments.get("agg_func", "SUM"),
            limit=arguments.get("limit", 10)
        )
    elif name == "get_publisher_benchmarks":
        return get_publisher_benchmarks(arguments.get("publishers"))
    else:
        return {"success": False, "error": f"Unknown tool '{name}'"}
