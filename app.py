from __future__ import annotations

import io
import tempfile
from collections import OrderedDict
from pathlib import Path
from uuid import uuid4

import pandas as pd
from flask import Flask, abort, render_template, request, send_file
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from steady_money.reporter import (
    InputDiscoveryError,
    NotesUnreadableError,
    process_folder,
)


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

# Local, short-lived download cache. No uploaded source files are retained.
DOWNLOAD_CACHE: OrderedDict[str, dict[str, bytes]] = OrderedDict()
MAX_CACHED_REPORTS = 20


def valid_upload(
    field_name: str,
    extension: str,
) -> FileStorage | None:
    upload = request.files.get(field_name)
    if upload is None or not upload.filename:
        return None
    if Path(upload.filename).suffix.casefold() != extension:
        return None
    return upload


def remember_downloads(results: bytes, summary: bytes) -> str:
    token = uuid4().hex
    DOWNLOAD_CACHE[token] = {
        "results.csv": results,
        "summary.md": summary,
    }
    while len(DOWNLOAD_CACHE) > MAX_CACHED_REPORTS:
        DOWNLOAD_CACHE.popitem(last=False)
    return token


@app.get("/")
def index():
    return render_template("index.html", error=None)


@app.post("/process")
def process():
    attendance = valid_upload("attendance", ".csv")
    diaries = valid_upload("diaries", ".csv")
    notes = valid_upload("notes", ".txt")
    if not all((attendance, diaries, notes)):
        return (
            render_template(
                "index.html",
                error="Please upload Attendance CSV, Diaries CSV, and Notes TXT files.",
            ),
            400,
        )

    try:
        with tempfile.TemporaryDirectory(prefix="steady-money-flask-") as temporary:
            input_folder = Path(temporary) / "inputs"
            output_folder = Path(temporary) / "outputs"
            input_folder.mkdir()

            for upload in (attendance, diaries, notes):
                filename = secure_filename(upload.filename)
                upload.save(input_folder / filename)

            report = process_folder(input_folder, output_dir=output_folder)
            results_bytes = report.results_path.read_bytes()
            summary_bytes = report.summary_path.read_bytes()
            rows = pd.read_csv(io.BytesIO(results_bytes)).to_dict(orient="records")
            summary_lines = [
                line[2:]
                for line in summary_bytes.decode("utf-8").splitlines()
                if line.startswith("- ")
            ]
            token = remember_downloads(results_bytes, summary_bytes)
    except NotesUnreadableError:
        return (
            render_template(
                "index.html",
                error="ERROR: Cannot read notes. Halting.",
            ),
            400,
        )
    except (InputDiscoveryError, OSError, ValueError) as exc:
        return render_template("index.html", error=f"ERROR: {exc}"), 400

    return render_template(
        "results.html",
        agency_name=report.agency_name,
        total_clients=report.total_clients,
        rows=rows,
        columns=["client_id", "status", "way_to_reach", "why"],
        summary_lines=summary_lines,
        token=token,
        warnings=report.warnings,
    )


@app.get("/download/<token>/<filename>")
def download(token: str, filename: str):
    files = DOWNLOAD_CACHE.get(token)
    if files is None or filename not in {"results.csv", "summary.md"}:
        abort(404)
    content_type = "text/csv" if filename == "results.csv" else "text/markdown"
    return send_file(
        io.BytesIO(files[filename]),
        mimetype=content_type,
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
