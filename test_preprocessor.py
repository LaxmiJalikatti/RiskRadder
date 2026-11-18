import sys
from modules.file_reader import read_file, FileReadError
from modules.preprocessor import preprocess_document

path = sys.argv[1] if len(sys.argv) > 1 else "data/sample.txt"

try:
    text = read_file(path)
except FileReadError as error:
    print("Error:", error)
    sys.exit(1)

clauses = preprocess_document(text)
print(f"Found {len(clauses)} clauses\n")
for item in clauses:
    print(f"[{item['id']}] ORIGINAL : {item['original']}")
    print(f"    PROCESSED: {item['processed']}\n")
