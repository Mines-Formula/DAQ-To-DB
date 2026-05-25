import sys
import pathlib
import pytest
import pandas as pd
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

'''
line protocol
'''
from known_to_influxdb.line_protocol import esc_measure, esc_tag


def test_esc_measure_commas():
    assert esc_measure("a,b") == r"a\,b"


def test_esc_measure_spaces():
    assert esc_measure("wheel speed") == r"wheel\ speed"


def test_esc_measure_equals():
    assert esc_measure("a=b") == r"a\=b"


def test_esc_measure_multiple_special_chars():
    assert esc_measure("a,b=c d") == r"a\,b\=c\ d"


def test_esc_measure_no_special_chars():
    assert esc_measure("RPM") == "RPM"


def test_esc_tag_matches_esc_measure():
    for s in ["a,b", "wheel speed", "a=b", "clean"]:
        assert esc_tag(s) == esc_measure(s)

'''
convert unix time
'''
from known_to_influxdb.convert_unix_time import (
    _parse_time_value,
    build_time_ref,
    convert_to_unix,
)


def test_parse_normal_time():
    assert _parse_time_value(123456000) == (12, 34, 56)


def test_parse_short_time_pads():
    assert _parse_time_value(1000) == (0, 0, 1)


def test_parse_midnight():
    assert _parse_time_value(0) == (0, 0, 0)


def test_parse_end_of_day():
    assert _parse_time_value(235959000) == (23, 59, 59)


def test_build_time_ref_falls_back_to_now_when_no_date_or_time(tmp_path):
    f = tmp_path / "data.csv"
    pd.DataFrame({
        "Timestamp": [1],
        "CANID": ["1"],
        "Sensor": ["Speed"],
        "Value": ["55"],
        "Unit": ["mph"],
    }).to_csv(f, index=False)
    before = datetime.now().timestamp() * 1000
    result = build_time_ref(str(f))
    after = datetime.now().timestamp() * 1000
    assert before <= result <= after


def test_build_time_ref_returns_correct_unix_ms(tmp_path):
    # Date "240525" -> day=24, month=05, year=2025; Time 120000000 -> 12:00:00
    f = tmp_path / "data.csv"
    pd.DataFrame({
        "Timestamp": [0, 0],
        "CANID": ["1", "1"],
        "Sensor": ["Date", "Time"],
        "Value": ["240525", "120000000"],
        "Unit": ["", ""],
    }).to_csv(f, index=False)
    result = build_time_ref(str(f))
    expected = datetime(2025, 5, 24, 12, 0, 0).timestamp() * 1000
    assert abs(result - expected) < 1000


def test_build_time_ref_pads_short_date(tmp_path):
    # "60525" -> zero-padded to "060525" -> day=06, month=05, year=2025
    f = tmp_path / "data.csv"
    pd.DataFrame({
        "Timestamp": [0, 0],
        "CANID": ["1", "1"],
        "Sensor": ["Date", "Time"],
        "Value": ["60525", "0"],
        "Unit": ["", ""],
    }).to_csv(f, index=False)
    result = build_time_ref(str(f))
    expected = datetime(2025, 5, 6, 0, 0, 0).timestamp() * 1000
    assert abs(result - expected) < 1000


def test_convert_to_unix_shifts_timestamps(tmp_path):
    f_in = tmp_path / "data.csv"
    f_out = tmp_path / "out.csv"
    pd.DataFrame({
        "Timestamp": [500, 0, 0],
        "CANID": ["1", "1", "1"],
        "Sensor": ["Speed", "Date", "Time"],
        "Value": ["55", "240525", "120000000"],
        "Unit": ["mph", "", ""],
    }).to_csv(f_in, index=False)
    convert_to_unix(str(f_in), str(f_out))
    result = pd.read_csv(f_out)
    expected_ref = int(datetime(2025, 5, 24, 12, 0, 0).timestamp() * 1000)
    speed_ts = result.loc[result["Sensor"] == "Speed", "Timestamp"].iloc[0]
    assert speed_ts == expected_ref + 500


def test_convert_to_unix_produces_output_file(tmp_path):
    f_in = tmp_path / "data.csv"
    f_out = tmp_path / "out.csv"
    pd.DataFrame({
        "Timestamp": [1000],
        "CANID": ["1"],
        "Sensor": ["RPM"],
        "Value": ["3000"],
        "Unit": ["rpm"],
    }).to_csv(f_in, index=False)
    convert_to_unix(str(f_in), str(f_out))
    assert f_out.exists()
    result = pd.read_csv(f_out)
    assert list(result.columns) == ["Timestamp", "CANID", "Sensor", "Value", "Unit"]

'''
filter GPS
'''
from unknown_to_known.filter_gps import filter_gps


def test_filter_gps_removes_out_of_bounds_latitude(tmp_path):
    f = tmp_path / "data.csv"
    pd.DataFrame({
        "Timestamp": [1, 2, 3],
        "CANID": [1, 1, 1],
        "Sensor": ["Latitude", "Latitude", "Speed"],
        "Value": [10.0, 39.0, 55.0],  # 10.0 is outside North America bounds
        "Unit": ["", "", "mph"],
    }).to_csv(f, index=False)
    filter_gps(str(f))
    result = pd.read_csv(f)
    latitudes = result.loc[result["Sensor"] == "Latitude", "Value"]
    assert len(latitudes) == 1
    assert all(latitudes.between(32, 46))


def test_filter_gps_removes_out_of_bounds_longitude(tmp_path):
    f = tmp_path / "data.csv"
    pd.DataFrame({
        "Timestamp": [1, 2, 3],
        "CANID": [1, 1, 1],
        "Sensor": ["Longitude", "Longitude", "Speed"],
        "Value": [-150.0, -105.0, 55.0],  # -150.0 is west of Los Angeles bound
        "Unit": ["", "", "mph"],
    }).to_csv(f, index=False)
    filter_gps(str(f))
    result = pd.read_csv(f)
    longitudes = result.loc[result["Sensor"] == "Longitude", "Value"]
    assert len(longitudes) == 1
    assert all(longitudes.between(-118, -73))


def test_filter_gps_preserves_non_gps_rows(tmp_path):
    f = tmp_path / "data.csv"
    pd.DataFrame({
        "Timestamp": [1, 2, 3],
        "CANID": [1, 1, 1],
        "Sensor": ["Speed", "RPM", "BrakeTemp"],
        "Value": [55.0, 3000.0, 120.0],
        "Unit": ["mph", "rpm", "C"],
    }).to_csv(f, index=False)
    filter_gps(str(f))
    result = pd.read_csv(f)
    assert len(result) == 3


def test_filter_gps_preserves_in_bounds_gps(tmp_path):
    # Golden, CO: lat ~39.7, lon ~-105.2
    f = tmp_path / "data.csv"
    pd.DataFrame({
        "Timestamp": [1, 2],
        "CANID": [1, 1],
        "Sensor": ["Latitude", "Longitude"],
        "Value": [39.7, -105.2],
        "Unit": ["", ""],
    }).to_csv(f, index=False)
    filter_gps(str(f))
    result = pd.read_csv(f)
    assert len(result) == 2


def test_filter_gps_overwrites_file_in_place(tmp_path):
    f = tmp_path / "data.csv"
    pd.DataFrame({
        "Timestamp": [1],
        "CANID": [1],
        "Sensor": ["Latitude"],
        "Value": [5.0],  # out of bounds, will be removed
        "Unit": [""],
    }).to_csv(f, index=False)
    filter_gps(str(f))
    result = pd.read_csv(f)
    assert result.loc[result["Sensor"] == "Latitude"].empty

'''
deserializer
'''
from raw_to_unknown.deserializer import deserialize


def test_deserialize_raises_on_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        deserialize(str(tmp_path / "nonexistent.bin"), str(tmp_path / "out.txt"))


def test_deserialize_can_message(tmp_path):
    f_in = tmp_path / "data.bin"
    f_out = tmp_path / "out.txt"
    # CAN packet: 1B length=2, 4B time big-endian, 4B id big-endian, 2B payload
    time_val, msg_id = 1234, 567
    payload = bytes([0xAB, 0xCD])
    packet = bytes([2]) + time_val.to_bytes(4, "big") + msg_id.to_bytes(4, "big") + payload
    f_in.write_bytes(packet)
    deserialize(str(f_in), str(f_out))
    result = f_out.read_text().strip()
    assert result == f"{time_val},{msg_id},{0xAB},{0xCD}"


def test_deserialize_string_mode(tmp_path):
    f_in = tmp_path / "data.bin"
    f_out = tmp_path / "out.txt"
    message = "hello"
    # header_byte > 127 triggers string mode; length = header_byte - 127
    header = 127 + len(message)
    packet = bytes([header]) + message.encode("ascii")
    f_in.write_bytes(packet)
    deserialize(str(f_in), str(f_out))
    result = f_out.read_text().strip()
    assert result == message


def test_deserialize_mixed_entries(tmp_path):
    f_in = tmp_path / "data.bin"
    f_out = tmp_path / "out.txt"
    # String entry: "hdr"
    msg = "hdr"
    str_packet = bytes([127 + len(msg)]) + msg.encode("ascii")
    # CAN entry: time=100, id=200, data=[15]
    can_packet = bytes([1]) + (100).to_bytes(4, "big") + (200).to_bytes(4, "big") + bytes([15])
    f_in.write_bytes(str_packet + can_packet)
    deserialize(str(f_in), str(f_out))
    lines = f_out.read_text().strip().splitlines()
    assert lines[0] == "hdr"
    assert lines[1] == "100,200,15"


def test_deserialize_multiple_can_messages(tmp_path):
    f_in = tmp_path / "data.bin"
    f_out = tmp_path / "out.txt"

    def make_can(time_val, msg_id, data):
        return bytes([len(data)]) + time_val.to_bytes(4, "big") + msg_id.to_bytes(4, "big") + bytes(data)

    f_in.write_bytes(make_can(1000, 10, [1, 2]) + make_can(2000, 20, [3]))
    deserialize(str(f_in), str(f_out))
    lines = f_out.read_text().strip().splitlines()
    assert lines[0] == "1000,10,1,2"
    assert lines[1] == "2000,20,3"


def test_deserialize_creates_output_file(tmp_path):
    f_in = tmp_path / "data.bin"
    f_out = tmp_path / "out.txt"
    # Minimal CAN message: length=1, time=0, id=0, data=[0]
    f_in.write_bytes(bytes([1]) + (0).to_bytes(4, "big") + (0).to_bytes(4, "big") + bytes([0]))
    deserialize(str(f_in), str(f_out))
    assert f_out.exists()

'''
csv to rerun
'''
from csv_to_rerun.csv_to_rerun import has_gps


def test_has_gps_true():
    df = pd.DataFrame({"Sensor": ["Latitude", "Longitude", "Speed"]})
    assert has_gps(df) is True


def test_has_gps_missing_longitude():
    df = pd.DataFrame({"Sensor": ["Latitude", "Speed"]})
    assert has_gps(df) is False


def test_has_gps_missing_latitude():
    df = pd.DataFrame({"Sensor": ["Longitude", "Speed"]})
    assert has_gps(df) is False


def test_has_gps_no_gps_sensors():
    df = pd.DataFrame({"Sensor": ["Speed", "RPM", "BrakeTemp"]})
    assert has_gps(df) is False


def test_has_gps_empty_dataframe():
    df = pd.DataFrame({"Sensor": []})
    assert has_gps(df) is False


def test_has_gps_ignores_nan_sensors():
    df = pd.DataFrame({"Sensor": ["Latitude", "Longitude", None]})
    assert has_gps(df) is True
