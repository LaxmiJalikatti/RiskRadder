"""
text_output.py
Builds the plain-text version of the analysis (for on-screen copy).
"""

from datetime import datetime

from modules.recommender import add_guidance

SEVERITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}
LINE = "-" * 56


def build_text_report(result, source_name="Pasted text"):
    if "summary" not in result:
        add_guidance(result)

    counts = result["severity_counts"]
    lines = [
        "RISKRADDER - TERMS AND CONDITIONS RISK ANALYSIS",
        "=" * 56,
        f"Document : {source_name}",
        f"Date     : {datetime.now():%d %B %Y, %I:%M %p}",
        f"Clauses analysed: {result['total_clauses']}",
        "",
        f"OVERALL RISK SCORE: {result['score']}/100 ({result['level']} risk)",
        f"High: {counts['High']}   Medium: {counts['Medium']}   Low: {counts['Low']}",
        "",
        result["summary"],
    ]
    if result["overall_advice"]:
        lines.append(result["overall_advice"])
    lines.append("")

    ordered = sorted(
        result["flagged"],
        key=lambda item: (SEVERITY_ORDER[item["severity"]], item["id"]),
    )
    for item in ordered:
        lines.append(LINE)
        lines.append(f"[{item['severity'].upper()}] {item['category']} (clause {item['id']})")
        lines.append(f"Clause        : {item['original']}")
        lines.append(f"Why it matters: {item['explanation']}")
        lines.append(f"What to do    : {item['recommendation']}")

    lines.append(LINE)
    lines.append(result["disclaimer"])
    return "\n".join(lines)