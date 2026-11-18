"""
file_reader.py
Reads PDF, DOCX, TXT and image files and returns their text as a plain string.
"""

import shutil
from pathlib import Path

import pdfplumber
from docx import Document

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp")
SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".txt") + IMAGE_EXTENSIONS

TESSERACT_PATHS = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)


class FileReadError(Exception):
    """Raised when a file cannot be read. The message is safe to show to the user."""


def read_txt(path):
    """Read a text file, trying common encodings until one works."""
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise FileReadError("Could not decode the text file.")


def read_pdf(path):
    """Extract text from every page of a PDF."""
    try:
        pages = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)
    except Exception as error:
        raise FileReadError(f"Could not open the PDF: {error}")

    text = "\n".join(pages)
    if not text.strip():
        raise FileReadError(
            "No text found in this PDF. It may be a scanned document. "
            "Try saving its pages as images and using the Photo option."
        )
    return text


def read_docx(path):
    """Extract text from paragraphs and tables of a Word document."""
    try:
        document = Document(path)
    except Exception as error:
        raise FileReadError(f"Could not open the DOCX file: {error}")

    parts = [p.text for p in document.paragraphs if p.text.strip()]

    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text)

    return "\n".join(parts)


def _find_tesseract():
    """Return the path of tesseract.exe, or None if it is not installed."""
    on_path = shutil.which("tesseract")
    if on_path:
        return on_path
    for candidate in TESSERACT_PATHS:
        if Path(candidate).exists():
            return candidate
    return None


def read_image(path):
    """Extract text from a photo or screenshot using Tesseract OCR."""
    try:
        import pytesseract
        from PIL import Image, ImageOps
    except ImportError:
        raise FileReadError(
            "Photo support needs two extra packages. "
            "Run: pip install pytesseract pillow"
        )

    tesseract = _find_tesseract()
    if tesseract is None:
        raise FileReadError(
            "Tesseract OCR is not installed, so photos cannot be read. "
            "Install it from the UB-Mannheim page and try again."
        )
    pytesseract.pytesseract.tesseract_cmd = tesseract

    try:
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert("L")
            if image.width < 1500:
                factor = 2
                image = image.resize(
                    (image.width * factor, image.height * factor),
                    Image.Resampling.LANCZOS,
                )
            text = pytesseract.image_to_string(image)
    except Exception as error:
        raise FileReadError(f"Could not read the image: {error}")

    if not text.strip():
        raise FileReadError(
            "No text was found in this image. "
            "Try a clearer, straighter and brighter photo."
        )
    return text


def read_file(path):
    """
    Read any supported file and return its text.
    Raises FileReadError with a friendly message if something is wrong.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileReadError(f"File not found: {file_path}")

    extension = file_path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise FileReadError(
            f"Unsupported file type '{extension}'. "
            "Please use PDF, DOCX, TXT or an image."
        )

    if extension == ".pdf":
        text = read_pdf(file_path)
    elif extension == ".docx":
        text = read_docx(file_path)
    elif extension in IMAGE_EXTENSIONS:
        text = read_image(file_path)
    else:
        text = read_txt(file_path)

    if not text.strip():
        raise FileReadError("The file is empty.")

    return text
