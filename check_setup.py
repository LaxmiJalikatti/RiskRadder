import nltk

for pkg in ("punkt", "punkt_tab"):
    nltk.download(pkg, quiet=True)

import customtkinter, sklearn, pandas, joblib, pdfplumber, docx, reportlab

print("customtkinter:", customtkinter.__version__)
print("scikit-learn :", sklearn.__version__)
print("pandas       :", pandas.__version__)
print("pdfplumber   :", pdfplumber.__version__)
print("reportlab    :", reportlab.Version)
print("NLTK tokenizer:", nltk.sent_tokenize("This works. Setup is done!"))
print("\nAll set. Ready for Step 2.")
