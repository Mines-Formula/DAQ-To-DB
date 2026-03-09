# ADAPTED FROM: https://github.com/Mines-Formula/DBCProcesser/blob/main/daq_deserializer.py
import os


def deserialize(input_filepath: str, output_filepath: str) -> None:
    if not os.path.exists(input_filepath):
        raise FileNotFoundError("input_filepath does not exist")

    with open(input_filepath, "rb") as file:
        input_data = file.read()

    output_parts = []
    i = 0
    data_size = len(input_data)

    while i < data_size:
        header_byte = input_data[i]
        i += 1

        if header_byte > 127:
            # String record
            length = header_byte - 127

            if i + length > data_size:
                raise Exception("file corruption detected")

            # Closest behavior to original chr(byte) logic
            string_content = "".join(map(chr, input_data[i:i + length]))
            output_parts.append(string_content)
            i += length

        else:
            # CAN record
            length = header_byte

            if i + 8 + length > data_size:
                raise Exception("file corruption detected")

            time_val = int.from_bytes(input_data[i:i + 4], "big")
            msg_id = int.from_bytes(input_data[i + 4:i + 8], "big")
            payload = input_data[i + 8:i + 8 + length]

            if length > 0:
                row = f"{time_val},{msg_id},{','.join(map(str, payload))}"
            else:
                row = f"{time_val},{msg_id}"

            output_parts.append(row)
            i += 8 + length

        output_parts.append("\n")

    with open(output_filepath, "w") as file:
        file.write("".join(output_parts).rstrip("\n"))