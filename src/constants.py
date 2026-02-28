from os import environ
from pathlib import Path

DATA_DIR = Path(environ.get("DATA_DIR", "/data"))
CSV_DIR = DATA_DIR / Path("csv")
RERUN_DIR = DATA_DIR / Path("rerun")
