from __future__ import annotations

from flask import Flask, request, jsonify, render_template
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    ...

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


def allowed_file(filename: str) -> bool:
    return filename.lower().endswith(".data")


@app.route("/upload", methods=["POST"])
def upload_csv():
    if len(request.files) == 0:
        return jsonify({"error": "No file uploaded"}), 400

    if not all(
        file.filename and allowed_file(file.filename) for file in request.files.values()
    ):
        return jsonify({"error": "Invalid types uploaded."}), 400

    for file in request.files.values():
        file.save(f"data/{file.filename}")

    return jsonify({"message": f"Uploaded {len(request.files)} files."}), 200


if __name__ == "__main__":
    app.run(debug=True)
