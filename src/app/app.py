from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

from flask import Flask, jsonify, render_template, request
from pathlib import Path
from datetime import datetime

from known_to_influxdb import line_protocol, write_to_influxDB
from unknown_to_known import decode
from csv_to_rerun import csv_to_rerun
from raw_to_unknown import deserializer
from constants import *
from os import urandom
from .models import ConversionProgress, LimitedDict
import threading

from flask import send_from_directory

if TYPE_CHECKING:
    from typing import Any

    from werkzeug.datastructures.file_storage import FileStorage


DATA_FILENAME = "{}.data"
CSV_FILENAME = "{}.csv"
LINE_FILENAME = "{}.line"

app = Flask(__name__)
app.config["tasks"] = LimitedDict(max_size=20)

CSV_DIR.mkdir(parents=True, exist_ok=True)
RERUN_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.get("/progress")
def get_progress():
    thread_name = request.args.get("name")

    if thread_name is None:
        return jsonify({"message": "No name parameter provided!"}), 400

    progress: ConversionProgress | None = app.config["tasks"].get(thread_name)
    if progress is None:
        return jsonify({"message": "Unknown task name."}), 404

    exception_present = progress.exception is not None

    return (
        jsonify(
            {
                "progress": progress.progress,
                "exception": {
                    "present": exception_present,
                    "type": str(progress.exception),
                },
            }
        ),
        200 if progress.finished else 202,
    )


def allowed_file(filename: str) -> bool:
    return filename.lower().endswith(".data")


@app.post("/upload")
def upload_data():
    if len(request.files) == 0:
        return jsonify({"error": "No file uploaded"}), 400

    if not any(
        file.filename and allowed_file(file.filename) for file in request.files.values()
    ):
        return jsonify({"error": "Invalid types uploaded."}), 400

    debug_enabled = request.form.get("debug") == "true"

    # Read all file contents upfront to avoid closed file errors
    files_data = [(file.filename, file.read()) for file in request.files.values()]

    conversion_thread = threading.Thread(
        target=convert_files,
        args=(files_data,),
        kwargs=dict(is_debug=debug_enabled),
        daemon=True,
        name=urandom(8).hex(),
    )

    app.config["tasks"][conversion_thread.name] = ConversionProgress(
        name=conversion_thread.name, progress="starting"
    )
    conversion_thread.start()

    return jsonify({"name": conversion_thread.name})


def convert_files(files, **kwargs: Any):
    for filename, content in files:
        # Create a temporary FileStorage-like object for conversion
        from io import BytesIO
        from werkzeug.datastructures import FileStorage

        file_like = FileStorage(
            stream=BytesIO(content), name=filename, filename=filename
        )

        convert_file(file_like, **kwargs)


def convert_file(file: FileStorage, is_debug: bool) -> None:
    """
    Converts .data following this flow:
        .data (raw) -> .data (unknown) -> .csv (known) -> .line (known)

    Saves the intermediate .csv to CSV_PARENT_PATH

    :param: file The file to convert."""
    assert file.name

    base_name = Path(file.name).stem

    csv_filename = CSV_FILENAME.format(base_name)
    raw_data_filename = DATA_FILENAME.format("raw_" + base_name)
    unknown_data_filename = DATA_FILENAME.format("unknown_" + base_name)
    line_filename = LINE_FILENAME.format(base_name)

    current_thread_name = threading.current_thread().name
    conversion_progress: ConversionProgress = app.config["tasks"][current_thread_name]

    with tempfile.TemporaryDirectory() as temporary_directory:
        parent_path = Path(temporary_directory)
        unknown_data_path = parent_path / unknown_data_filename

        raw_data_path = RAW_DIR / raw_data_filename
        csv_path = CSV_DIR / csv_filename
        line_path = CSV_DIR / line_filename

        file.save(raw_data_path)
        conversion_progress.progress = "deserialize"

        try:
            deserializer.deserialize(
                str(raw_data_path.resolve()), str(unknown_data_path.resolve())
            )
        except Exception as _:
            pass
        else:
            raw_data_path = unknown_data_path
            conversion_progress.progress = "making known"

        try:
            decode.make_known(str(raw_data_path.resolve()), str(csv_path.resolve()))
        except Exception as exec:
            conversion_progress.exception = exec
            return
        else:
            conversion_progress.progress = "line protocol "

        try:
            line_protocol.convert_to_lineprotocol(
                str(csv_path.resolve()),
                str(line_path.resolve()),
            )
        except Exception as exec:
            raise
        else:
            conversion_progress.progress = "uploading to influx"

        try:
            if is_debug:
                app.logger.info(
                    f"Thread {current_thread_name}: Skipping InfluxDB upload (Debug Mode)."
                )
            else:
                write_to_influxDB.write_to_influxDB(str(line_path.resolve()))

        except Exception as exec:
            conversion_progress.exception = exec
            return
        else:
            conversion_progress.progress = "creating rerun file"

        try:
            csv_to_rerun.convert(csv_path.resolve(), RERUN_DIR)
        except Exception as exec:
            conversion_progress.exception = exec
            return
        else:
            conversion_progress.progress = "done"
            conversion_progress.finished = True


@app.route("/files")
def list_files():
    TYPE_TO_DIR = {
        "csv": CSV_DIR,
        "rerun": RERUN_DIR,
        "raw": RAW_DIR,
    }

    type_ = request.args.get("type", "").casefold()

    try:
        dir = TYPE_TO_DIR[type_]
    except KeyError:
        return "Invalid type!", 400

    files = []

    for path in dir.iterdir():
        if path.is_file():
            files.append(
                {
                    "name": path.name,
                    "timestamp": datetime.fromtimestamp(path.stat().st_mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
            )
    files.sort(key=lambda f: f["timestamp"], reverse=True)

    return jsonify(files)


@app.route("/files/download/<path:filename>")
def download_file(filename):
    if (RERUN_DIR / Path(filename)).exists():
        dir = RERUN_DIR
    else:
        dir = CSV_DIR

    return send_from_directory(dir, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
