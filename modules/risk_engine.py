"""
risk_engine.py
Turns classifier predictions into severity levels and an overall risk score.
"""

from modules.classifier import SAFE_LABEL, classify_clauses
from modules.preprocessor import preprocess_document

# ---- Settings you can adjust ------------------------------------------------

MIN_CONFIDENCE = 0.40  # predictions below this are too uncertain to report

CATEGORY_SEVERITY = {
    "Data Sharing": "High",
    "Arbitration Clause": "High",
    "Liability Limitation": "High",
    "Location Tracking": "High",
    "Auto Renewal": "Medium",
    "No Refund Policy": "Medium",
    "Account Termination": "Medium",
    "Data Retention": "Medium",
    "Policy Change Without Notice": "Medium",
    "Marketing Consent": "Low",
}

SEVERITY_POINTS = {"High": 10, "Medium": 6, "Low": 3}

# A Medium clause containing one of these phrases is raised to High.
ESCALATION_PHRASES = (
    "without notice",
    "without prior notice",
    "without warning",
    "without informing",
    "without telling",
    "without notifying",
    "sole discretion",
    "for any reason",
    "indefinitely",
    "forever",
    "permanently",
)

SCORE_REFERENCE = 60  # total points that correspond to a score of 100
HIGH_LEVEL_FROM = 60
MEDIUM_LEVEL_FROM = 30

# -----------------------------------------------------------------------------


def severity_for(category, processed_text):
    """Return (severity, escalated) for a flagged clause."""
    severity = CATEGORY_SEVERITY.get(category, "Medium")
    escalated = False
    if severity == "Medium" and any(p in processed_text for p in ESCALATION_PHRASES):
        severity, escalated = "High", True
    return severity, escalated


def calculate_score(flagged):
    """Weighted score from 0 to 100. Each category counts once, plus a small repeat bonus."""
    points_by_category = {}
    for clause in flagged:
        points_by_category.setdefault(clause["category"], []).append(
            SEVERITY_POINTS[clause["severity"]]
        )

    total = 0.0
    for points in points_by_category.values():
        top = max(points)
        repeat_bonus = min(0.5 * top, 0.2 * top * (len(points) - 1))
        total += top + repeat_bonus

    return min(100, round(100 * total / SCORE_REFERENCE))


def level_for_score(score):
    if score >= HIGH_LEVEL_FROM:
        return "High"
    if score >= MEDIUM_LEVEL_FROM:
        return "Medium"
    return "Low"


def analyze_text(text):
    """
    Main function used by the rest of the app.
    Returns a dictionary with the flagged clauses, counts, score and level.
    """
    clauses = preprocess_document(text)
    if not clauses:
        raise ValueError("No readable clauses were found in this document.")

    predictions = classify_clauses([c["processed"] for c in clauses])

    flagged = []
    for clause, prediction in zip(clauses, predictions):
        category = prediction["category"]
        if category == SAFE_LABEL or prediction["confidence"] < MIN_CONFIDENCE:
            continue
        severity, escalated = severity_for(category, clause["processed"])
        flagged.append(
            {
                "id": clause["id"],
                "original": clause["original"],
                "category": category,
                "severity": severity,
                "escalated": escalated,
                "confidence": prediction["confidence"],
            }
        )

    severity_counts = {"High": 0, "Medium": 0, "Low": 0}
    category_counts = {}
    for item in flagged:
        severity_counts[item["severity"]] += 1
        category_counts[item["category"]] = category_counts.get(item["category"], 0) + 1

    score = calculate_score(flagged)
    return {
        "total_clauses": len(clauses),
        "flagged": flagged,
        "severity_counts": severity_counts,
        "category_counts": category_counts,
        "score": score,
        "level": level_for_score(score),
    }
