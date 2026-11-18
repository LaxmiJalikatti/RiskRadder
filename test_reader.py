import sys
from modules.file_reader import read_file, FileReadError

if len(sys.argv) < 2:
    print("Usage: python test_reader.py <path to file>")
    sys.exit(1)

try:
    text = read_file(sys.argv[1])
    print("Characters:", len(text))
    print("Words     :", len(text.split()))
    print("\n--- First 400 characters ---")
    print(text[:400])
except FileReadError as error:
    print("Error:", error)
