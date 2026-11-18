import sys

from modules.file_reader import read_file
from modules.risk_engine import analyze_text

path = sys.argv[1] if len(sys.argv) > 1 else "data/sample.txt"
result = analyze_text(read_file(path))

print(f"Document: {path}")
print(f"Clauses analysed: {result['total_clauses']}   Flagged: {len(result['flagged'])}\n")

for item in result["flagged"]:
    note = "  (escalated)" if item["escalated"] else ""
    print(f"[{item['id']:>2}] {item['severity']:<6} {item['category']:<30} {item['confidence']:.0%}{note}")
    print(f"      {item['original'][:80]}")

print("\nSeverity counts:", result["severity_counts"])
print(f"OVERALL RISK SCORE: {result['score']}/100  ->  {result['level']}")
