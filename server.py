
"""
server.py
RiskRadder website backend (Flask).
Serves the web page and reuses the same Python modules as the desktop app.
"""

import os
import socket
import tempfile
import threading
import uuid
from collections import OrderedDict
from pathlib import Path

from flask import Flask, Response, abort, jsonify, request, send_file

from modules.file_reader import SUPPORTED_EXTENSIONS, FileReadError, read_file
from modules.recommender import GUIDANCE, add_guidance
from modules.report_generator import REPORTS_DIR, generate_report
from modules.risk_engine import CATEGORY_SEVERITY, analyze_text
from modules.text_output import build_text_report


BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"

app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024  # 15 MB uploads

MAX_TEXT_CHARS = 300_000
CACHE_LIMIT = 50

_cache = OrderedDict()
_lock = threading.Lock()


def error(message, status=400):
    return jsonify({"error": message}), status


def remember(result):
    """Keep recent results in memory so reports can be downloaded by id."""
    result_id = uuid.uuid4().hex[:12]
    result["id"] = result_id

    with _lock:
        _cache[result_id] = result

        while len(_cache) > CACHE_LIMIT:
            _cache.popitem(last=False)

    return result_id


def recall(result_id):
    if not result_id.isalnum():
        abort(404)

    with _lock:
        result = _cache.get(result_id)

    if result is None:
        abort(404)

    return result


@app.errorhandler(413)
def too_large(_):
    return error("That file is larger than 15 MB.", 413)


@app.get("/")
def home():
    return send_file(WEB_DIR / "index.html")


@app.get("/api/categories")
def categories():
    order = {"High": 0, "Medium": 1, "Low": 2}

    items = [
        {
            "name": name,
            "severity": CATEGORY_SEVERITY.get(name, "Medium"),
            "explanation": info["explanation"],
            "recommendation": info["recommendation"],
        }
        for name, info in GUIDANCE.items()
    ]

    items.sort(key=lambda item: (order[item["severity"]], item["name"]))

    return jsonify(items)


@app.post("/api/analyze")
def analyze():
    source = "Pasted text"

    try:
        upload = request.files.get("file")

        if upload:
            name = Path(upload.filename or "upload").name
            extension = Path(name).suffix.lower()

            if extension not in SUPPORTED_EXTENSIONS:
                return error(
                    "Unsupported file type. Use PDF, DOCX, TXT or an image."
                )

            handle, temp_path = tempfile.mkstemp(suffix=extension)
            os.close(handle)

            try:
                upload.save(temp_path)
                text = read_file(temp_path)

            finally:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

            source = name

        else:
            payload = request.get_json(silent=True) or {}
            text = str(payload.get("text", "")).strip()

            if not text:
                return error("Paste some text or choose a file first.")

            if len(text) > MAX_TEXT_CHARS:
                return error(
                    "That text is too long. Please paste up to 300,000 characters."
                )

        result = add_guidance(analyze_text(text))
        result["source"] = source

        remember(result)

        return jsonify(result)

    except (FileReadError, ValueError) as problem:
        return error(str(problem))

    except Exception:
        app.logger.exception("Analysis failed")
        return error(
            "Something went wrong while analyzing this document.",
            500
        )


@app.get("/api/report/<rid>.pdf")
def report_pdf(rid):
    result = recall(rid)

    REPORTS_DIR.mkdir(exist_ok=True)

    path = REPORTS_DIR / f"web_{rid}.pdf"

    if not path.exists():
        generate_report(result, result["source"], path)

    return send_file(
        path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="RiskRadder_Report.pdf",
    )


@app.get("/api/report/<rid>.txt")
def report_text(rid):
    result = recall(rid)

    text = build_text_report(result, result["source"])

    headers = {}

    if request.args.get("download"):
        headers["Content-Disposition"] = (
            'attachment; filename="RiskRadder_Report.txt"'
        )

    return Response(
        text,
        mimetype="text/plain",
        headers=headers
    )


def local_ip():
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))

        address = probe.getsockname()[0]
        probe.close()

        return address

    except OSError:
        return "127.0.0.1"


if __name__ == "__main__":

    # Render provides PORT automatically.
    # When running locally, the default port is 5000.
    port = int(os.environ.get("PORT", 5000))

    print("\nRiskRadder website is starting...")
    print(f"  Local address : http://127.0.0.1:{port}")

    if "PORT" not in os.environ:
        print(
            f"  On your phone : http://{local_ip()}:{port} "
            "(same Wi-Fi)"
        )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
