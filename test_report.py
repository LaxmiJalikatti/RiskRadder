import os
import sys
from pathlib import Path

from modules.file_reader import read_file
from modules.recommender import add_guidance
from modules.report_generator import generate_report
from modules.risk_engine import analyze_text

path = sys.argv[1] if len(sys.argv) > 1 else "data/sample.txt"
result = add_guidance(analyze_text(read_file(path)))
report = generate_report(result, source_name=Path(path).name)

print("Report saved to:", report)
try:
    os.startfile(report)  # opens the PDF on Windows
except Exception:
    pass
