import math

import pytest

from ot_toolkit_backend import engineering


@pytest.mark.parametrize(
    ("value", "kind", "decimal", "hex_value"),
    [("123", "UInt8", 123, "7B"), ("-1", "Int16", -1, "FFFF"), ("0b1010", "UInt16", 10, "000A"), ("16#8401", "UInt16", 33793, "8401")],
)
def test_number_conversion(value, kind, decimal, hex_value):
    result = engineering.convert_number(value, kind)
    assert result["decimal"] == decimal
    assert result["hex"] == hex_value


def test_signed_unsigned_reinterpretation():
    assert engineering.reinterpret_integer(0xFFFF, 16, True) == -1
    assert engineering.reinterpret_integer(-1, 16, False) == 65535


def test_number_conversion_rejects_overflow():
    with pytest.raises(ValueError, match="between"):
        engineering.convert_number("256", "UInt8")


@pytest.mark.parametrize("precision", [32, 64])
def test_ieee_754_round_trip(precision):
    encoded = engineering.ieee_float_to_hex(123.0, precision)
    assert engineering.ieee_hex_to_float(encoded, precision) == pytest.approx(123.0)
    if precision == 32:
        assert encoded == "42F60000"


def test_endianness_arrangements():
    result = engineering.decode_endianness("12 34 56 78")
    assert result["ABCD"]["hex"] == "12345678"
    assert result["BADC"]["hex"] == "34127856"
    assert result["CDAB"]["hex"] == "56781234"
    assert result["DCBA"]["hex"] == "78563412"


def test_modbus_address_conversion():
    result = engineering.modbus_address("40001")
    assert result == {"type": "Holding Register", "reference": "40001", "zero_based_offset": 0, "one_based_offset": 1}


def test_modbus_crc_and_frame_decode():
    request = bytes.fromhex("01 03 00 00 00 02")
    assert engineering.modbus_crc(request) == 0x0BC4
    frame = engineering.decode_modbus_frame("01 03 00 00 00 02 C4 0B")
    assert frame.crc_valid
    assert frame.function_name == "Read Holding Registers"
    assert frame.details == {"start_address": 0, "quantity": 2}


def test_modbus_register_decode():
    decoded = engineering.decode_registers([0x42F6, 0x0000])
    assert decoded["ABCD"]["float32"] == pytest.approx(123.0)
    assert decoded["ABCD"]["uint32"] == 0x42F60000


def test_ipv4_subnet_and_same_subnet():
    subnet = engineering.calculate_subnet("192.168.10.37", "/27")
    assert subnet.network == "192.168.10.32"
    assert subnet.broadcast == "192.168.10.63"
    assert subnet.first_host == "192.168.10.33"
    assert subnet.last_host == "192.168.10.62"
    assert subnet.usable_hosts == 30
    assert engineering.same_subnet("192.168.10.37", "192.168.10.62", "27")["same"]
    assert not engineering.same_subnet("192.168.10.37", "192.168.10.65", "27")["same"]


def test_ip_validation_detects_invalid_special_and_duplicates():
    values = ["10.0.0.0", "10.0.0.4", "10.0.0.4", "10.0.0.255", "300.1.1.1"]
    result = engineering.validate_ips(values, "24")
    assert result[0]["kind"] == "network"
    assert result[1]["duplicate"] is True
    assert result[3]["kind"] == "broadcast"
    assert result[4]["valid"] is False


def test_command_generator_does_not_accept_shell_content():
    with pytest.raises(ValueError):
        engineering.generate_commands("10.0.0.1; whoami", 502)
    commands = engineering.generate_commands("plc-01.local", 502)
    assert commands["windows"][-1] == "Test-NetConnection plc-01.local -Port 502"
