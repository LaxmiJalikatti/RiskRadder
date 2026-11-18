"""
preprocessor.py
Cleans raw agreement text and splits it into individual clauses.
Each clause is returned in two forms:
  original  - for showing to the user
  processed - lowercase, punctuation-free, for the machine-learning model
"""

import re

import nltk

# Make sure the sentence tokenizer data is available.
for _pkg in ("punkt", "punkt_tab"):
    try:
        nltk.data.find(f"tokenizers/{_pkg}")
    except LookupError:
        nltk.download(_pkg, quiet=True)

MIN_WORDS = 4  # clauses shorter than this are ignored

# Matches list markers at the start of a line: "1.", "2)", "1.2.", "(a)", "a.", "-", bullets
NUMBER_PATTERN = re.compile(
    r"^\s*(?:\(?\d{1,3}[\.\)]|\d{1,3}(?:\.\d{1,3})+\.?|\(?[A-Za-z][\.\)]|[-\u2022*\u25cf\u25aa\u2013])\s+"
)

TERMINAL_PUNCTUATION = (".", ";", ":", ",", "?", "!")


def clean_text(text):
    """Normalise line endings, quotes and spacing."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    text = (
        text.replace("\u2018", "'").replace("\u2019", "'")
        .replace("\u201c", '"').replace("\u201d", '"')
    )
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _looks_like_heading(line):
    """A short line that starts with a capital and has no ending punctuation."""
    words = line.split()
    return (
        0 < len(words) <= 6
        and line[0].isupper()
        and not line.endswith(TERMINAL_PUNCTUATION)
    )


def split_into_blocks(text):
    """
    Group lines into blocks. A new block starts at a blank line,
    a numbered/bulleted line, or after a heading.
    """
    blocks, current = [], []

    def flush():
        if current:
            blocks.append(" ".join(current))
            current.clear()

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if NUMBER_PATTERN.match(stripped):
            flush()
            stripped = NUMBER_PATTERN.sub("", stripped, count=1).strip()
        if _looks_like_heading(stripped):
            flush()
            continue
        current.append(stripped)

    flush()
    return blocks


def split_into_clauses(text):
    """Return a list of clause strings from raw text."""
    clauses = []
    for block in split_into_blocks(clean_text(text)):
        for sentence in nltk.sent_tokenize(block):
            sentence = sentence.strip()
            if len(sentence.split()) >= MIN_WORDS:
                clauses.append(sentence)
    return clauses


def preprocess_for_model(clause):
    """Lowercase and strip punctuation, keeping meaningful words like 'not' and 'without'."""
    clause = clause.lower()
    clause = clause.replace("-", " ")
    clause = re.sub(r"[^a-z0-9\s]", " ", clause)
    clause = re.sub(r"\s+", " ", clause)
    return clause.strip()


def preprocess_document(text):
    """
    Main function used by the rest of the app.
    Returns a list of dicts: {"id": 1, "original": "...", "processed": "..."}
    """
    results = []
    for number, clause in enumerate(split_into_clauses(text), start=1):
        results.append(
            {
                "id": number,
                "original": clause,
                "processed": preprocess_for_model(clause),
            }
        )
    return results
