import subprocess


def write_to_influxDB(FILE_INPUT: str):
    """
    Reads a .line and writes to the influxDB database through the commandline

    :param FILE_INPUT: Name of .line File
    :param BUCKET_NAME: Name of Output File
    """
    BUCKET_NAME: str = "TESTING"
    FILE_PATH: str = "Path_to_data"
    HOST_NAME: str
    ORG: str
    TOKEN: str

    with open("data/influxdb2_parameters/influxdb2-admin-token") as file:
        HOST_NAME = file.read()
    with open("data/influxdb2_parameters/influxdb2-org") as file:
        ORG = file.read()
    with open("data/influxdb2_parameters/influxdb2-admin-token") as file:
        TOKEN = file.read()

    """
    follows the command structure:
        influx write --bucket <your-bucket-name> --file /path/to/your/data.csv --org <your-organization> --token <your-token>
    """
    command = [
        "influx",
        "write",
        "--host",
        HOST_NAME,
        "--bucket",
        BUCKET_NAME,
        "--file",
        FILE_PATH,
        "--org",
        ORG,
        "--token",
        TOKEN,
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    print("STDOUT: ", result.stdout)
    print("STDERR: ", result.stderr)
