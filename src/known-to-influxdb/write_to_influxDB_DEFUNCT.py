from influxdb_client import InfluxDBClient, WriteOptions, WritePrecision
from influxdb_client.client.write_api import ASYNCHRONOUS
# InfluxDB info
url = "http://fsaelinux.mines.edu:8086"
token = "theTokenOfMyDreams!"
org = "docs"
bucket = "TESTING"
    
def write_to_influxDB(FILE_NAME:str):
    client = InfluxDBClient(url=url, token=token, org=org)
    write_options = WriteOptions(
        batch_size=20_000,       # num of points to send at a time
        max_retries=5,          # num of retries for each batch
        max_retry_delay=30_000, # delay between retries
    )

    write_api = client.write_api(
        write_options=write_options
    )

    i=0
    buf = []
    BUF = 20_000

    try:
        with open(FILE_NAME, "r") as file:
            for line in file:
                lp = line.strip()
                if not lp: # checks if line is empty
                    continue
                buf.append(lp)
                i += 1

                if len(buf) >= BUF:
                    # Non-blocking enqueue; background thread sends & retries
                    write_api.write(bucket=bucket, record=buf, write_precision=WritePrecision.MS)
                    buf.clear()

                if i % 100_000 == 0:
                    print(f"loaded {i} lines")

            # make sure everything in buffer is sent
            if buf:
                write_api.write(bucket=bucket, record=buf, write_precision=WritePrecision.MS)
        # ensure all internal client buffers are sent
        write_api.flush()

    finally:
        #close writer before client, so thread finishes cleanly
        write_api.close()
        client.close()
        print(f"finished loading {i} lines")

        