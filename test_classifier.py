import sys

from modules.classifier import classify_clauses
from modules.file_reader import read_file
from modules.preprocessor import preprocess_document, preprocess_for_model

if len(sys.argv) > 1:
    # Test your own sentences: python test_classifier.py "your sentence here"
    sentences = sys.argv[1:]
    results = classify_clauses([preprocess_for_model(s) for s in sentences])
    for sentence, r in zip(sentences, results):
        print(f"{r['category']} ({r['confidence']:.0%})  <-  {sentence}")
else:
    clauses = preprocess_document(read_file("data/sample.txt"))
    results = classify_clauses([c["processed"] for c in clauses])
    for clause, r in zip(clauses, results):
        print(f"[{clause['id']:>2}] {r['category']:<30} {r['confidence']:.0%}   {clause['original'][:60]}")
