import cantools
import pandas as pd
import csv

def make_known(unknown_file_name, output_file_name):

    """Takes input file of unknown data and decodes it writing into a csv. Uses NEW_MOTEC_MESSAGES.dbc file.
    
    :param unknown_file_name: Name of the file with unknown/raw data
    :param output_file_name: Name of the csv file decoded data will be written to
    """

    # === FILE PATHS ===
    dbc_file = "NEW_MOTEC_MESSAGES.dbc"
    data_file = unknown_file_name
    output_csv = output_file_name

    # === LOAD DBC ===
    db = cantools.database.load_file(dbc_file)

    # === READ ALL LINES (skip headers) ===
    with open(data_file, "r", errors="ignore") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("CAN:")]

    decoded_rows = []
    decoded_count = 0
    skipped_count = 0

    # === PROCESS EACH LINE ===
    for line in lines:
        parts = line.split(",")
        if len(parts) < 3:
            skipped_count += 1
            continue

        try:
            timestamp = int(parts[0])
            can_id = int(parts[1])
            data_bytes = [int(x) for x in parts[2:] if x != ""]
            data_bytes = (data_bytes + [0]*8)[:8]  # pad to 8 bytes

            msg = db.get_message_by_frame_id(can_id)
            decoded = msg.decode(bytes(data_bytes))

            for signal, value in decoded.items():
                unit = msg.get_signal_by_name(signal).unit
                decoded_rows.append({
                    "Timestamp": timestamp,
                    "CANID": can_id,
                    "Sensor": signal,
                    "Value": value,
                    "Unit": unit if unit else ""
                })
            decoded_count += 1

        except Exception:
            skipped_count += 1
            continue

    # === SAVE TO CSV ===
    df = pd.DataFrame(decoded_rows)
    df.to_csv(output_csv, index=False, quoting=csv.QUOTE_MINIMAL)

    # === PRINT SUMMARY ===
    print("\n✅ CAN data decoding complete.")
    print(f"Total frames processed : {len(lines)}")
    print(f"Successfully decoded   : {decoded_count}")
    print(f"Skipped (undecoded)    : {skipped_count}")
    print(f"Output saved to        : {output_csv}")