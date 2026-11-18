import sys

from modules.file_reader import read_file
from modules.recommender import add_guidance
from modules.risk_engine import analyze_text

path = sys.argv[1] if len(sys.argv) > 1 else "data/sample.txt"
result = add_guidance(analyze_text(read_file(path)))

print(f"Document: {path}")
print(f"OVERALL RISK SCORE: {result['score']}/100  ->  {result['level']}\n")
print("SUMMARY:", result["summary"])
print("ADVICE :", result["overall_advice"], "\n")

for item in result["flagged"][:3]:
    print(f"[{item['id']}] {item['severity']} - {item['category']}")
    print("  Clause        :", item["original"])
    print("  Explanation   :", item["explanation"])
    print("  Recommendation:", item["recommendation"], "\n")

print(result["disclaimer"])
