import subprocess

def write_to_influxDB(FILE_INPUT:str, BUCKET_NAME:str):
    """
    Reads a .line and writes to the influxDB database through the commandline

    :param FILE_INPUT: Name of .line File
    :param BUCKET_NAME: Name of Output File
    """
    BUCKET_NAME:str = "TESTING"
    FILE_PATH:str = "Path_to_data"
    HOST_NAME:str
    ORG:str
    TOKEN:str

    with open("srck/known-to-influxdb/influxdb2_parameters/influxdb2-admin-token", "r") as file:
        ORG = file.read()
    with open("src\known-to-influxdb\influxdb2_parameters\influxdb2-org", "r") as file:
        ORG = file.read()
    with open("src/known-to-influxdb/influxdb2_parameters/influxdb2-admin-token", "r") as file:
        TOKEN = file.read()

    '''
    follows the command structure:
        influx write --bucket <your-bucket-name> --file /path/to/your/data.csv --org <your-organization> --token <your-token>
    '''    
    command = [
        "influx", "write",
        "--host", 
        "--bucket", BUCKET_NAME,
        "--file", FILE_PATH,
        "--org", ORG,
        "--token", TOKEN
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    print("STDOUT: ", result.stdout)
    print("STDERR: ", result.stderr)