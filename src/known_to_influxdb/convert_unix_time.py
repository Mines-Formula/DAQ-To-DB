import pandas as pd
from datetime import datetime

"""
@author Will Turchin
Script to convert formula .csv Timestamp's into unix time using the "Time" sensor value
However, the "Time" values from the 2024 Comp data were so noisy that they could not be converted correctly into
usable Unix times, so this code is not currently being used 
"""


def build_time_ref(file) -> float:
    # Read only needed cols for efficiency
    df = pd.read_csv(file)
    DateRow = df[(df["Sensor"] == "Date")]  # DDMMYY
    TimeRow = df[(df["Sensor"] == "Time")]  # HHMMSS.sss

    if(TimeRow.size == 0 or DateRow.size == 0):
        raise(ValueError("Time or Date data entry missing"))

    Date: str = str(DateRow["Value"].iloc[-1])
    Time: int = int(TimeRow["Value"].iloc[-1])

    while (
        len(Date) < 6
    ):  # Edge case, if given 06/05/25 date value is "60525" convert to -> "060525"
        Date = "0" + Date

    day: int = int(Date[0:2])
    month: int = int(Date[2:4])
    year: int = int(Date[4:6]) + 2000

    if (
        int(str(Time)[0:2]) > 23
    ):  # Edge case, if given 3113036044 (HHMMSS.sss) we know that the data was read wrong, as big endian instead of little
        n = int(Time).to_bytes(4, byteorder="little")
        Time = int.from_bytes(n, byteorder="big")
        print(
            f"Exception detected: time was read as big endian, switching to little endian"
        )

    hour: int = int(str(Time)[0:2])
    minute: int = int(str(Time)[2:4])
    second: int = int(str(Time)[4:6])
    ms: int = 0  # UNIX time doesn't need ms
    dt = datetime(year, month, day, hour, minute, second, 0)
    Unix_ms: float = dt.timestamp() * 1000
    return Unix_ms


def convert_to_unix(FILE_NAME: str, FILE_OUTPUT: str):
    """
    Takes input csv and converts timestamps into UNIX time format

    :param FILE_NAME: Name of input file
    :param FILE_OUTPUT: Name of output file
    """

    # Build the reference mapping once (optimization to make code run faster)
    try:
        time_ref: float = build_time_ref(FILE_NAME)
    except ValueError as e:
        raise e

    header_written = False
    for chunk in pd.read_csv(
        FILE_NAME,
        dtype={
            "Timestamp": "int",
            "CANID": "string",
            "Sensor": "string",
            "Value": "string",
            "Unit": "string",
        },
        na_filter=False,
        chunksize=200000,
    ):
        chunk["Timestamp"] += int(time_ref)
        # write once, then append
        if not header_written:
            chunk.head(0).to_csv(FILE_OUTPUT, index=False)
            header_written = True

        chunk.to_csv(FILE_OUTPUT, mode="a", index=False, header=False)
