from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

from flask import Flask, jsonify, render_template, request
from pathlib import Path
from src.known_to_influxdb import line_protocol, write_to_influxDB
from src.unknown_to_known import decode

if TYPE_CHECKING:
    from werkzeug.datastructures.file_storage import FileStorage

CSV_PARENT_PATH = Path("data/csv")

DATA_FILENAME = "{}.data"
CSV_FILENAME = "{}.csv"
LINE_FILENAME = "{}.line"

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


def allowed_file(filename: str) -> bool:
    return filename.lower().endswith(".data")


@app.route("/upload", methods=["POST"])
def upload_data():
    if len(request.files) == 0:
        return jsonify({"error": "No file uploaded"}), 400

    if not all(
        file.filename and allowed_file(file.filename) for file in request.files.values()
    ):
        return jsonify({"error": "Invalid types uploaded."}), 400

    for file in request.files.values():
        convert_file(file)

    return jsonify({"message": f"Uploaded {len(request.files)} files."}), 200


def convert_file(file: FileStorage) -> None:
    """
    Converts .data following this flow:
        .data -> .csv -> .line

    Saves the intermediate .csv to CSV_PARENT_PATH

    :param: file The file to convert."""
    assert file.name

    csv_filename = CSV_FILENAME.format(file.name)
    data_filename = DATA_FILENAME.format(file.name)
    line_filename = LINE_FILENAME.format(file.name)

    with tempfile.TemporaryDirectory() as temporary_directory:
        parent_path = Path(temporary_directory)
        data_path = parent_path / data_filename
        csv_path = CSV_PARENT_PATH / csv_filename
        line_path = parent_path / line_filename

        file.save(data_path)  # Save .data file to temp dir

        decode.make_known(
            data_path, csv_path
        )  # Convert .data file to .csv and save to CSV_PARENT_PATH

        line_protocol.convert_to_lineprotocol(
            str(csv_path.resolve()),
            str(line_path.resolve()),
        )  # Convert .csv to .line and save to temp dir

        # write_to_influxDB.write_to_influxDB(csv_filename)


if __name__ == "__main__":
    app.run(debug=True)
