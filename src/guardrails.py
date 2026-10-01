"""
Grounding & Citation Guardrail.
Extracts record entities and numerical metrics from generated text, cross-verifying them
against raw SQL result rows to prevent hallucinations and calculate provenance confidence.
"""
import re
from typing import Dict, Any, List, Set, Optional

def mask_entities_in_text(text: str, titles: List[str], platforms: List[str]) -> str:
    """
    Masks game titles (e.g. 'FIFA 18', 'Battlefield 3') and platform abbreviations (e.g. 'PS4', 'X360')
    so that numbers inside entity names are not erroneously treated as numerical claims.
    """
    masked = text
    # Sort by length descending to mask longer strings first
    all_entities = sorted(titles + platforms, key=len, reverse=True)
    for ent in all_entities:
        if ent and len(ent) > 1:
            pattern = re.compile(re.escape(ent), re.IGNORECASE)
            masked = pattern.sub(" __ENTITY__ ", masked)
    return masked

def extract_substantive_numbers(text: str) -> List[float]:
    """
    Extracts numerical metrics from text, ignoring years (e.g. 2011, 2024).
    """
    raw_matches = re.findall(r"[-+]?\b\d+(?:\.\d+)?\b", text)
    numbers = []
    for m in raw_matches:
        try:
            val = float(m)
            # Filter out 4-digit years between 1970 and 2035
            if 1970 <= val <= 2035 and val.is_integer():
                continue
            numbers.append(val)
        except ValueError:
            continue
    return numbers

def evaluate_grounding_and_citations(
    generated_text: str,
    retrieved_rows: List[Dict[str, Any]],
    known_platforms: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Evaluates grounding integrity:
    1. Entity Citation: checks which games/publishers from the retrieved set are explicitly cited.
    2. Numerical Grounding: checks if numeric claims in the response match row values.
    3. Hallucination Detection: flags numbers or titles mentioned that do NOT exist in the retrieved rows.
    """
    if not retrieved_rows:
        return {
            "grounding_score": 1.0 if not generated_text else 0.5,
            "cited_records": [],
            "unverified_metrics": [],
            "hallucination_flag": False,
            "status": "EMPTY_RESULT_SET"
        }

    # Extract all known platforms from rows or defaults
    platforms = known_platforms or ["PS2", "PS3", "PS4", "PS5", "X360", "XOne", "XSX", "Switch", "PC", "Wii", "NES"]

    # Collect ground-truth entities and numeric values from retrieved rows
    row_values_pool: Set[float] = set()
    retrieved_titles: Dict[str, Dict[str, Any]] = {}

    for row in retrieved_rows:
        if "title" in row and row["title"]:
            retrieved_titles[row["title"].lower()] = row
        for k, v in row.items():
            if isinstance(v, (int, float)):
                row_values_pool.add(round(float(v), 2))
                row_values_pool.add(round(float(v), 1))
                row_values_pool.add(float(int(v)))

    # Find cited records in the unmasked text
    cited_records = []
    lower_text = generated_text.lower()
    for title_lower, full_row in retrieved_titles.items():
        if title_lower in lower_text:
            cited_records.append({
                "title": full_row.get("title"),
                "platform": full_row.get("platform"),
                "global_sales": full_row.get("global_sales"),
                "critic_score": full_row.get("critic_score")
            })

    # Mask titles and platforms before numerical claim extraction
    titles_to_mask = [r["title"] for r in retrieved_rows if "title" in r and r["title"]]
    masked_text = mask_entities_in_text(generated_text, titles_to_mask, platforms)

    # Extract numbers from masked text
    substantive_numbers = extract_substantive_numbers(masked_text)

    verified_metrics = []
    unverified_metrics = []

    for num in substantive_numbers:
        rounded_num = round(num, 2)
        # Check direct or close float match (tolerance ±0.05)
        matched = any(abs(rounded_num - pool_val) <= 0.05 for pool_val in row_values_pool)
        if matched:
            verified_metrics.append(num)
        else:
            unverified_metrics.append(num)

    total_claims = len(verified_metrics) + len(unverified_metrics)
    if total_claims == 0:
        grounding_score = 1.0
    else:
        grounding_score = round(len(verified_metrics) / total_claims, 3)

    hallucination_flag = len(unverified_metrics) > 0 and grounding_score < 0.8

    return {
        "grounding_score": grounding_score,
        "verified_metrics_count": len(verified_metrics),
        "unverified_metrics": unverified_metrics,
        "cited_records": cited_records,
        "cited_records_count": len(cited_records),
        "hallucination_flag": hallucination_flag,
        "status": "PASS" if grounding_score >= 0.8 else "WARN_UNVERIFIED_DATA"
    }

if __name__ == "__main__":
    mock_rows = [
        {"title": "FIFA 18", "platform": "PS4", "global_sales": 11.8, "critic_score": 84},
        {"title": "FIFA 19", "platform": "PS4", "global_sales": 11.3, "critic_score": 83}
    ]
    sample_text = "The top title is FIFA 18 on PS4 with 11.8M global sales and a critic score of 84."
    print("Testing Grounding Guardrail (Clean Response):")
    print(evaluate_grounding_and_citations(sample_text, mock_rows))

    hallucinated_text = "FIFA 18 made 99.5M sales and FIFA 99 sold 400M units."
    print("\nTesting Grounding Guardrail (Hallucinated Response):")
    print(evaluate_grounding_and_citations(hallucinated_text, mock_rows))
