# ADAPTED FROM: https://github.com/Mines-Formula/DBCProcesser/blob/main/daq_deserializer.py

import os


def deserialize(input_filepath: str, output_filepath: str) -> None:
    if not os.path.exists(input_filepath):
        raise FileNotFoundError("input_filepath does not exist")

    with open(input_filepath, "rb") as file:
        input_data = file.read()
    output_string = ""

    # Data file structure

    # String structure
    # 1B length + 127
    # xB data

    # CAN message structure
    # 1B length
    # 4B time (big endian)
    # 4B message id (big endian)
    # xB data

    data_length = 0
    cur_data_index = 0
    string_read_mode = False

    for i, byte in enumerate(input_data):

        # tranisiton to reading next line
        if cur_data_index == data_length:
            data_length = byte
            output_string = output_string[:-1]  # remove previous line's trailing comma
            output_string += "\n"
            if byte > 127:
                data_length -= 127
                string_read_mode = True
                cur_data_index = 0  # start directly at the string data
            else:
                string_read_mode = False
                cur_data_index = -8  # start by reading this line's metadata

        # read data in current line
        else:
            if string_read_mode:
                output_string += chr(byte)
            else:
                if (
                    cur_data_index < 0
                ):  # read message metadata (time and id, each 4 bytes)
                    relative_index = (cur_data_index + 1) % 4
                    if relative_index == 0:
                        number = int.from_bytes(input_data[i - 3 : i + 1])
                        output_string += str(number) + ","

                else:
                    output_string += str(byte) + ","
            cur_data_index += 1

    if cur_data_index != data_length:
        raise Exception("file corruption detected")

    output_string = output_string[:-1]  # remove final trailing comma
    with open(output_filepath, "w") as file:
        file.write(output_string)
