### Project to collect data from car and pipe it to database
---
This project takes the .data files and pipes them through the following levels
1. Unknown (*.data*) files are submitted to the WEB GUI and downloaded to the Mines FSAE Linux Server.
2. Converts unknown (*.data*) files into known (*.csv*) files.
3. Takes the known (*.csv*) files and converts them into InfluxDB (*.line*) files.
4. The InfluxDB (*.line*) file is then written to the database locally on the Mines FSAE Linux Server. 
5. Takes the known (*.csv*) files and converts them into Rerun (*.rrd*) files.
