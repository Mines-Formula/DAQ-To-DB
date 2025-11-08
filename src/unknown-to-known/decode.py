import cantools
import pandas as pd

def make_known(unknown_file_name: str, output_file_name: str):

    """Takes input file of unknown data and decodes it writing into a csv. Uses MF13Beta.dbc file.
    
    :param unknown_file_name: Name of the file with unknown/raw data
    :param output_file_name: Name of the csv file decoded data will be written to
    """

    db = cantools.database.load_file('MF13Beta.dbc')
    fields = ['Timestamp', 'CANID', 'Sensor', 'Value', 'Unit'] #Timestamp,CANID,Sensor,Value,Unit
    data_file = unknown_file_name
    output_file = output_file_name

    with open(data_file, 'r') as unknown:
        header = unknown.readline()
        data = []
        print(header)
        for line in unknown:
            dataLst = []
            lineLst = line.split(',')
            timestamp = int(lineLst[0])
            dataLst.append(timestamp)
            canID = int(lineLst[1])
            dataLst.append(canID)
            dataDecimal = lineLst[2:]
            # for i in range(len(dataDecimal)):
            #     dataDecimal[i] = hex(int(dataDecimal[i].strip()))
            # dataBytes = bytes('/'.join(dataDecimal), 'ascii')
            for i in range(len(dataDecimal)):
                dataDecimal[i] = int(dataDecimal[i].strip())
            dataBytes = bytes(dataDecimal)
            dataLst.append(dataBytes)
            # print(dataLst)
            data.append(dataLst)

    failed_lines = 0
    skipped_ids = []
    writable_lines = []
    for dataset in data:
        try:
            write_this = []
            values = []
            units = []
            sensors = []
            decoded = db.decode_message(dataset[1], dataset[2])
            message = db.get_message_by_frame_id(dataset[1])
            write_this.append(dataset[0]) #timestamp
            write_this.append(dataset[1]) #CAN ID
            for signal in message.signals:
                sensor = signal.name
                sensors.append(sensor)
                value = decoded.get(sensor)
                values.append(value)
                unit = signal.unit
                if unit == None:
                    unit = ''
                units.append(unit)
                # print(f'{sensor},{value},{unit} END')
                # print(f'UNIT TYPE: {type(unit)}')
                # print('')
            # print(dataset)
            # print(decoded)
            # print(type(decoded))
            # print(decoded.keys()) #decode.keys prints "dict_keys(['XRoll', 'YRoll', 'ZRoll', 'GyroTemp'])"
            # sensors = list(decoded.keys())
            # print(sensors) #Listing decode.keys() just returns the list "['XRoll', 'YRoll', 'ZRoll', 'GyroTemp']"
            write_this.append(sensors)
            # for sensor in sensors:
            #     value = decoded[sensor]
            #     values.append(value)
            write_this.append(values)
            write_this.append(units)
            writable_lines.append(write_this)
            # print(write_this)
            # print('')

        except Exception as e:
            # print(dataset)
            # print(f'Decode Failure ---> {e}')
            # print('')
            if dataset[1] not in skipped_ids:
                skipped_ids.append(dataset[1])
            failed_lines += 1
            continue

    with open(output_file, 'w') as file:
        file.write(f'{','.join(fields)}\n')
        for line in writable_lines:
            time = line[0]
            canbus_id = line[1]
            for i in range(len(line[2])):
                sense = line[2][i]
                val = line[3][i]
                unt = line[4][i]
                data_entry = f'{time},{canbus_id},{sense},{val},{unt}\n'
                # print(data_entry)
                file.write(data_entry)

    print(f'DATA DECODED INTO FILE: {output_file}')
    print(f'LINES SKIPPED: {failed_lines}')
    print(f'SKIPPED IDS: {skipped_ids}')
