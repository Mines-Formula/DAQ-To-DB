# Data-to-DB Pipeline — Mines Formula SAE

A telemetry data processing pipeline that ingests raw vehicle sensor data, decodes it using CAN database definitions, and stores it in InfluxDB for time-series analysis. Data can also be exported to Rerun format for lap replay and visualization.

## Getting Started

### Running with Docker

For normal local development, use the canonical Compose file:

```bash
docker compose up --build
```

The Flask app starts on port `6767`.

On the `fsaelinux` server, run the base Compose file plus the server override:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.server.yml \
  up -d
```

The server override switches the web service to host networking and clears the inherited `ports` mapping. It preserves the base service definition, including the `./data:/data` bind mount, environment, restart policy, build context, and stop signal. The watcher in `infra/watch_submodule.sh` uses the same two-file Compose command when it redeploys after DBC submodule updates.

### Usage

1. Open `http://localhost:6767` in a browser
2. Upload one or more `.data` files from the vehicle
3. The pipeline processes them automatically end-to-end
4. Monitor progress in the web UI
5. Outputs land in `data/csv/` (decoded sensor data) and `data/rerun/` (replay files)

## How It Works

```
Raw Binary          Intermediate        InfluxDB Format     Database
  (.data)    →        (.csv)       →       (.line)       →   InfluxDB
                      ↓
                  Rerun Format
               (.rrd for replay)
```

| Stage | Module | What it does |
|---|---|---|
| 1. Upload | `src/app/` | Flask web UI accepts `.data` files |
| 2. Binary to CAN | `src/binary_to_can/` | Parses binary packets into raw CAN frames |
| 3. CAN to CSV | `src/can_to_csv/` | Maps CAN IDs to named sensors via `.dbc` files; filters GPS outliers |
| 4. CSV to InfluxDB time conversion | `src/csv_to_influxdb/` | Converts relative timestamps to Unix ms using embedded Date/Time sensor rows |
| 5. CSV to InfluxDB export | `src/csv_to_influxdb/` | Formats data as InfluxDB line protocol |
| 6. Write to DB | `src/influx/` | Pushes line protocol data to InfluxDB |
| 7. Rerun export | `src/csv_to_rerun/` | Converts CSV to `.rrd` for telemetry replay |

## Project Structure

```
thePipeline/
├── src/
│   ├── app/                  # Flask web server (upload UI)
│   ├── binary_to_can/        # Binary deserializer
│   ├── can_to_csv/            # CAN decoder + GPS filter
│   ├── csv_to_influxdb/       # Timestamp conversion + line protocol formatter
│   ├── influx/               # InfluxDB writer
│   ├── csv_to_rerun/         # Rerun SDK exporter
│   └── constants.py          # Shared paths and config
├── data/
│   ├── DBCFiles/             # CAN database files (git submodule)
│   ├── raw/                  # Uploaded .data files
│   ├── csv/                  # Decoded CSV output
│   └── rerun/                # Rerun .rrd output
├── tests/
│   └── conftest.py           # Full test suite
├── infra/
│   └── watch_submodule.sh    # Auto-updates DBCFiles on the server
├── Lib/
│   └── ProtobufLib/          # Protocol Buffers source (git submodule)
└── docker-compose.yml
```

### Git submodules

This repository uses Git submodules for the CAN database files and the Protocol
Buffers source. A normal `git clone` does not populate submodules automatically.
To clone the repository with all submodules initialized, use:

```bash
git clone --recurse-submodules <repository-url>
```

If you have already cloned the repository, initialize or update all submodules
with:

```bash
git submodule update --init --recursive
```

## CAN Database Files

The `.dbc` files are the key to decoding raw CAN frames — they map numeric CAN IDs and bit offsets to named sensors with units. They live in `data/DBCFiles/` as a git submodule and are kept up to date on the server automatically via `infra/watch_submodule.sh`.

## File Formats

| Extension | Description |
|---|---|
| `.data` | Raw Formula binary telemetry captured on the car |
| `.pb`, `.protobuf`, `.bin` | Protobuf telemetry (select the format explicitly) |
| `.txt` | Intermediate CAN frame dump (time, ID, payload bytes) |
| `.csv` | Decoded sensor data — columns: `Timestamp, CANID, Sensor, Value, Unit` |
| `.line` | InfluxDB line protocol, ready for upload |
| `.rrd` | Rerun SDK recording for lap replay and visualization |

## Tests

The test suite covers the core backend modules — no mocks, each test exercises real logic with temporary files.

**Modules covered:**

| Module | Tests |
|---|---|
| `csv_to_influxdb/line_protocol.py` | InfluxDB special-character escaping for measurement names and tags |
| `csv_to_influxdb/convert_unix_time.py` | Timestamp parsing, date/time reference building, Unix ms conversion |
| `can_to_csv/filter_gps.py` | GPS bounds filtering (removes readings outside continental North America) |
| `binary_to_can/deserializer.py` | Binary packet parsing for CAN frames and string entries |
| `csv_to_rerun/csv_to_rerun.py` | GPS availability detection for Rerun export |

**Run the tests:**

```bash
# From the repo root
pip install -r tests/requirements-frontend.txt
pytest tests/
```

To see per-test output:

```bash
pytest tests/ -v
```

## Protobuf telemetry

The `telemetry_input` package is the shared streaming input boundary.
`InputConfig` selects `formula_binary`, `protobuf_binary` (one message), or
`protobuf_delimited` (multiple messages with varint or fixed32 length
prefixes). Protobuf configurations require a schema or generated module and a
fully qualified message type; protobuf is never guessed from arbitrary bytes.

```python
from telemetry_input import InputConfig, decode_to_csv

config = InputConfig(
    input_format="protobuf_delimited",
    schema="schemas/",
    message_type="telemetry.VehicleMessage",
    protobuf_output_mode="raw_can",
    field_mapping={
        "timestamp": "timestamp",
        "can_id": "frame.can_id",
        "payload": "frame.payload",
    },
)
decode_to_csv("run.pb", "run.csv", config)
```

Use `protobuf_output_mode="raw_can"` to route timestamp, CAN ID, and payload
through the existing DBC decoder. Use `"decoded_telemetry"` with `timestamp`,
`sensor`, `value`, and `unit` mappings to bypass DBC and write the same
five-column CSV contract directly.

For production, generate modules once during the build:

```bash
cd src
python -m tools.generate_protobuf ../schemas generated \
  --expected-version="libprotoc 31.1"
```

The upload API accepts matching form fields: `input_format`, `schema`,
`generated_module`, `message_type`, `protobuf_output_mode`, `include_paths`,
`length_prefix_encoding`, `byte_order`, `field_mapping` (JSON),
`error_policy`, `maximum_message_size`, `maximum_nesting_depth`, and
`preserve_unknown_fields`. Schema paths refer to trusted server files; a
schema-upload UI can be added separately.

Once a representative vehicle schema and capture are available, measure the
protobuf portion separately from total CSV conversion:

```bash
cd src
python -m tools.benchmark_protobuf ../run.pb \
  --schema ../schemas \
  --message-type telemetry.VehicleMessage \
  --format protobuf_delimited \
  --mode raw_can
```
