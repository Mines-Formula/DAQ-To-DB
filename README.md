# Data-to-DB Pipeline — Mines Formula SAE

A telemetry data processing pipeline that ingests raw vehicle sensor data, decodes it using CAN database definitions, and stores it in InfluxDB for time-series analysis. Data can also be exported to Rerun format for lap replay and visualization.

## Getting Started

### Running with Docker

```bash
docker-compose up --build
```

The Flask app starts on port `6767`.

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
| 2. Deserialize | `src/raw_to_unknown/` | Parses binary packets into raw CAN frames |
| 3. Decode | `src/unknown_to_known/` | Maps CAN IDs to named sensors via `.dbc` files; filters GPS outliers |
| 4. Time conversion | `src/known_to_influxdb/` | Converts relative timestamps to Unix ms using embedded Date/Time sensor rows |
| 5. InfluxDB export | `src/known_to_influxdb/` | Formats data as InfluxDB line protocol |
| 6. Write to DB | `src/influx/` | Pushes line protocol data to InfluxDB |
| 7. Rerun export | `src/csv_to_rerun/` | Converts CSV to `.rrd` for telemetry replay |

## Project Structure

```
thePipeline/
├── src/
│   ├── app/                  # Flask web server (upload UI)
│   ├── raw_to_unknown/       # Binary deserializer
│   ├── unknown_to_known/     # CAN decoder + GPS filter
│   ├── known_to_influxdb/    # Timestamp conversion + line protocol formatter
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
└── docker-compose.yml
```

## CAN Database Files

The `.dbc` files are the key to decoding raw CAN frames — they map numeric CAN IDs and bit offsets to named sensors with units. They live in `data/DBCFiles/` as a git submodule and are kept up to date on the server automatically via `infra/watch_submodule.sh`.

To initialize the submodule locally:

```bash
git submodule update --init --recursive
```

## File Formats

| Extension | Description |
|---|---|
| `.data` | Raw binary telemetry captured on the car |
| `.txt` | Intermediate CAN frame dump (time, ID, payload bytes) |
| `.csv` | Decoded sensor data — columns: `Timestamp, CANID, Sensor, Value, Unit` |
| `.line` | InfluxDB line protocol, ready for upload |
| `.rrd` | Rerun SDK recording for lap replay and visualization |

## Tests

The test suite covers the core backend modules — no mocks, each test exercises real logic with temporary files.

**Modules covered:**

| Module | Tests |
|---|---|
| `known_to_influxdb/line_protocol.py` | InfluxDB special-character escaping for measurement names and tags |
| `known_to_influxdb/convert_unix_time.py` | Timestamp parsing, date/time reference building, Unix ms conversion |
| `unknown_to_known/filter_gps.py` | GPS bounds filtering (removes readings outside continental North America) |
| `raw_to_unknown/deserializer.py` | Binary packet parsing for CAN frames and string entries |
| `csv_to_rerun/csv_to_rerun.py` | GPS availability detection for Rerun export |

**Run the tests:**

```bash
# From the repo root
pip install pytest pandas
pytest tests/
```

To see per-test output:

```bash
pytest tests/ -v
```