import convert_unix_time as convert_unix_time
import line_protocol
import write_to_influxDB

FILE_NAME:str = "./tests_data/CAN3File15.data_known.csv"
FILE_OUTPUT:str = "./output.line" 
convert_unix_time.convert_to_unix(FILE_NAME=FILE_NAME, FILE_OUTPUT="./output.csv")
line_protocol.convert_to_lineprotocol(FILE_NAME="./output.csv", FILE_OUTPUT=FILE_OUTPUT)
#write_to_influxDB.write_to_influxDB(FILE_NAME=FILE_OUTPUT)
# commented out until I can figure out how to not crash server