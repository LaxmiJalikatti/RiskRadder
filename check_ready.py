from pathlib import Path
from modules.file_reader import _find_tesseract

checks = {
    "Trained model": Path("models/risk_model.joblib").exists(),
    "Sample agreement": Path("data/sample.txt").exists(),
    "Mild sample": Path("data/sample_mild.txt").exists(),
    "Sample photo": Path("data/sample_photo.png").exists(),
    "Tesseract (photo input)": _find_tesseract() is not None,
    "Reports folder": Path("reports").exists(),
}
for name, ok in checks.items():
    print("OK     " if ok else "MISSING", name)
