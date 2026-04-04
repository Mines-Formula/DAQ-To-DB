# Data-to-DB Pipeline for Mines Formula SAE

## Overview

This project is a **telemetry data processing pipeline**. It ingests raw vehicle sensor data, processes it through multiple formats, and stores it in InfluxDB while also preparing it for replay visualization.

### What It Does

The pipeline transforms raw telemetry data through the following stages:

```
Raw Data Files        CSV Files       InfluxDB Format   Database Storage
    (.data)    →      (.csv)      →      (.line)       →   InfluxDB
                        ↓
                    Rerun Format
                (.rrd for replay)
```

1. **Upload**: Raw `.data` files are uploaded via flask app `fsaelinux:6767`
2. **Decode**: Converts unknown `.data` format to standard `.csv` using CAN database definitions (`.dbc` files)
3. **Time Conversion**: Processes Unix timestamps in the data
4. **InfluxDB Export**: Reformats CSV data for InfluxDB line protocol
5. **Database Storage**: Writes data to InfluxDB for time-series analysis
6. **Replay Format**: Converts CSV to Rerun format (`.rrd`) for telemetry replay and visualization

## Getting Started

### Prerequisites (for running locally)

- Docker and Docker Compose
- Python 3.x (for local development)
- CAN database files (`.dbc`) for vehicle data decoding

### Installation & Running Locally

```bash
# Install dependencies
pip install -r src/requirements.txt

# Run the Flask app
cd src
python -m app.app
```

**Using Docker (Required locally):**

```bash
docker-compose up --build
```

This starts the Flask web server on port `6767`.

### Usage

1. Open your browser to `http://localhost:6767`
2. Upload one or more `.data` files from your vehicle
3. The system automatically processes them through the entire pipeline
4. Track progress on the web UI
5. Processed CSV files are saved to the `data/csvFiles/` directory

## Data Format References

### CAN Database Files (.dbc)

This file is the 'map' used to convert unknown to known
- Uses git submodule of DBCFiles from the Github
- Automatically updated on server through `watch_submodule.sh` script 
- Located in `data/DBCFiles/`

### File Formats

- **`.data`**: Raw binary telemetry from vehicle sensors
- **`.csv`**: Main data format almost any data analysis tool uses
- **`.line`**: InfluxDB line protocol for upload
- **`.rrd`**: Rerun SDK format for telemetry replay and visualization