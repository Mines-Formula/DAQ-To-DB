from __future__ import annotations

import io
import pytest


@pytest.fixture
def upload_app(monkeypatch):
    import app.app as app_module

    captured = []

    def fake_convert_files(files, schema_data=None, **kwargs):
        captured.append((files, schema_data, kwargs))

    class ImmediateThread:
        name = "test-upload-thread"

        def __init__(self, target, args=(), kwargs=None, **_options):
            self.target = target
            self.args = args
            self.kwargs = kwargs or {}

        def start(self):
            self.target(*self.args, **self.kwargs)

    monkeypatch.setattr(app_module, "convert_files", fake_convert_files)
    monkeypatch.setattr(app_module.threading, "Thread", ImmediateThread)
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client(), captured


def test_upload_accepts_can_binary(upload_app):
    client, captured = upload_app

    response = client.post(
        "/upload",
        data={
            "files": (io.BytesIO(b"can bytes"), "capture.data"),
            "input_format": "formula_binary",
            "debug": "true",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    files, schema, kwargs = captured[-1]
    assert files == [("capture.data", b"can bytes")]
    assert schema is None
    assert kwargs["input_config"].input_format.value == "formula_binary"


def test_upload_accepts_protobuf_capture_and_schema(upload_app):
    client, captured = upload_app

    response = client.post(
        "/upload",
        data={
            "files": (io.BytesIO(b"protobuf bytes"), "capture.pb"),
            "schema_file": (io.BytesIO(b'syntax = "proto3"; message Test {}'), "test.proto"),
            "input_format": "protobuf_delimited",
            "message_type": "telemetry.Test",
            "debug": "true",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    files, schema, kwargs = captured[-1]
    assert files == [("capture.pb", b"protobuf bytes")]
    assert schema == ("test.proto", b'syntax = "proto3"; message Test {}')
    config = kwargs["input_config"]
    assert config.input_format.value == "protobuf_delimited"
    assert config.message_type == "telemetry.Test"
    assert config.schema is not None
    assert config.protobuf_output_mode.value == "raw_can"
    assert config.length_prefix_encoding.value == "varint"


def test_upload_rejects_invalid_schema_extension(upload_app):
    client, _ = upload_app

    response = client.post(
        "/upload",
        data={
            "files": (io.BytesIO(b"protobuf bytes"), "capture.pb"),
            "schema_file": (io.BytesIO(b"not a schema"), "schema.txt"),
            "input_format": "protobuf_delimited",
            "message_type": "telemetry.Test",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "proto extension" in response.json["error"]


def test_upload_rejects_single_message_protobuf(upload_app):
    client, _ = upload_app

    response = client.post(
        "/upload",
        data={
            "files": (io.BytesIO(b"protobuf bytes"), "capture.pb"),
            "schema_file": (io.BytesIO(b"syntax = \"proto3\"; message Test {}"), "test.proto"),
            "input_format": "protobuf_binary",
            "message_type": "telemetry.Test",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "full protobuf capture" in response.json["error"]
