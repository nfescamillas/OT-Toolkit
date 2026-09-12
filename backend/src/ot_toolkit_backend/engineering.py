from __future__ import annotations

import ipaddress
import math
import re
import struct

from .models import FrameDecode, SubnetResult


INTEGER_FORMATS = {
    "UInt8": (8, False), "Int8": (8, True),
    "UInt16": (16, False), "Int16": (16, True),
    "UInt32": (32, False), "Int32": (32, True),
    "UInt64": (64, False), "Int64": (64, True),
}


def parse_integer(value: str, base: int | None = None) -> int:
    text = value.strip().replace("_", "")
    if not text:
        raise ValueError("Enter a value.")
    if text.lower().startswith("16#"):
        return int(text[3:], 16)
    if base is None:
        base = 16 if text.lower().startswith("0x") else 2 if text.lower().startswith("0b") else 8 if text.lower().startswith("0o") else 10
    return int(text, base)


def convert_number(value: str, numeric_format: str) -> dict[str, str | int]:
    if numeric_format not in INTEGER_FORMATS:
        raise ValueError(f"Unsupported numeric format: {numeric_format}")
    bits, signed = INTEGER_FORMATS[numeric_format]
    parsed = parse_integer(value)
    minimum = -(1 << (bits - 1)) if signed else 0
    maximum = (1 << (bits - 1)) - 1 if signed else (1 << bits) - 1
    if not minimum <= parsed <= maximum:
        raise ValueError(f"Value must be between {minimum} and {maximum} for {numeric_format}.")
    unsigned = parsed & ((1 << bits) - 1)
    return {
        "decimal": parsed,
        "binary": format(unsigned, f"0{bits}b"),
        "hex": format(unsigned, f"0{bits // 4}X"),
        "octal": format(unsigned, "o"),
        "bits": bits,
    }


def reinterpret_integer(value: int, bits: int, signed: bool) -> int:
    mask = (1 << bits) - 1
    raw = value & mask
    if signed and raw & (1 << (bits - 1)):
        return raw - (1 << bits)
    return raw


def ieee_float_to_hex(value: float, precision: int) -> str:
    fmt = ">f" if precision == 32 else ">d" if precision == 64 else None
    if fmt is None:
        raise ValueError("Precision must be 32 or 64.")
    return struct.pack(fmt, value).hex().upper()


def ieee_hex_to_float(value: str, precision: int) -> float:
    raw = clean_hex(value)
    expected = precision // 8
    if precision not in (32, 64) or len(raw) != expected:
        raise ValueError(f"Float{precision} requires exactly {expected} bytes.")
    return struct.unpack(">f" if precision == 32 else ">d", raw)[0]


def clean_hex(value: str) -> bytes:
    text = re.sub(r"(?:0x|16#|[\s,_:-])", "", value.strip(), flags=re.IGNORECASE)
    if not text or len(text) % 2 or not re.fullmatch(r"[0-9a-fA-F]+", text):
        raise ValueError("Enter complete hexadecimal bytes, for example: 01 03 00 00.")
    return bytes.fromhex(text)


def reorder_four_bytes(value: str, order: str) -> bytes:
    raw = clean_hex(value)
    if len(raw) != 4:
        raise ValueError("Enter exactly four bytes.")
    indexes = {"ABCD": (0, 1, 2, 3), "BADC": (1, 0, 3, 2), "CDAB": (2, 3, 0, 1), "DCBA": (3, 2, 1, 0)}
    if order not in indexes:
        raise ValueError("Order must be ABCD, BADC, CDAB, or DCBA.")
    return bytes(raw[i] for i in indexes[order])


def decode_endianness(value: str) -> dict[str, dict[str, int | float | str]]:
    labels = {"ABCD": "No swap", "BADC": "Byte swap", "CDAB": "Word swap", "DCBA": "Byte + word swap"}
    result = {}
    for order, label in labels.items():
        raw = reorder_four_bytes(value, order)
        result[order] = {
            "operation": label,
            "hex": raw.hex().upper(),
            "uint32": int.from_bytes(raw, "big"),
            "int32": int.from_bytes(raw, "big", signed=True),
            "float32": struct.unpack(">f", raw)[0],
        }
    return result


def decode_registers(registers: list[int]) -> dict[str, dict[str, int | float | str]]:
    if len(registers) not in (2, 4) or any(not 0 <= x <= 0xFFFF for x in registers):
        raise ValueError("Enter two or four 16-bit register values.")
    raw = b"".join(x.to_bytes(2, "big") for x in registers)
    result: dict[str, dict[str, int | float | str]] = {}
    if len(raw) == 4:
        result = decode_endianness(raw.hex())
    else:
        arrangements = {
            "ABCDEFGH": raw,
            "BADCFEHG": b"".join(raw[i:i+2][::-1] for i in range(0, 8, 2)),
            "GHEFCDAB": b"".join(raw[i:i+2] for i in (6, 4, 2, 0)),
            "HGFEDCBA": raw[::-1],
        }
        for order, value in arrangements.items():
            result[order] = {"hex": value.hex().upper(), "uint64": int.from_bytes(value, "big"), "int64": int.from_bytes(value, "big", signed=True), "float64": struct.unpack(">d", value)[0]}
    result["ASCII"] = {"text": "".join(chr(b) if 32 <= b < 127 else "." for b in raw)}
    return result


def modbus_address(reference: str | int) -> dict[str, str | int]:
    text = str(reference).strip()
    if not text.isdigit() or len(text) < 5:
        raise ValueError("Use a traditional reference such as 40001.")
    number = int(text)
    area = number // 10000
    types = {0: "Coil", 1: "Discrete Input", 3: "Input Register", 4: "Holding Register"}
    if area not in types or number % 10000 == 0:
        raise ValueError("Reference must be in 00001, 10001, 30001, or 40001 format.")
    one_based = number % 10000
    return {"type": types[area], "reference": f"{area}{one_based:04d}", "zero_based_offset": one_based - 1, "one_based_offset": one_based}


def modbus_crc(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


FUNCTION_CODES = {1: "Read Coils", 2: "Read Discrete Inputs", 3: "Read Holding Registers", 4: "Read Input Registers", 5: "Write Single Coil", 6: "Write Single Register", 15: "Write Multiple Coils", 16: "Write Multiple Registers", 22: "Mask Write Register", 23: "Read/Write Multiple Registers", 43: "Encapsulated Interface Transport"}


def decode_modbus_frame(value: str) -> FrameDecode:
    frame = clean_hex(value)
    if len(frame) < 4:
        raise ValueError("A Modbus RTU frame requires address, function, and two CRC bytes.")
    body, received = frame[:-2], frame[-2:]
    crc = modbus_crc(body)
    calculated = crc.to_bytes(2, "little")
    function = body[1]
    payload = body[2:]
    details: dict[str, int | str] = {}
    if function in (1, 2, 3, 4) and len(payload) == 4:
        details = {"start_address": int.from_bytes(payload[:2], "big"), "quantity": int.from_bytes(payload[2:], "big")}
    elif function & 0x80 and payload:
        details = {"exception_code": payload[0]}
    return FrameDecode(body[0], function, FUNCTION_CODES.get(function & 0x7F, "Unknown function"), payload.hex(" ").upper(), received.hex(" ").upper(), calculated.hex(" ").upper(), received == calculated, details)


def calculate_subnet(ip: str, mask_or_cidr: str) -> SubnetResult:
    suffix = mask_or_cidr.strip()
    network = ipaddress.IPv4Network(f"{ip.strip()}/{suffix.lstrip('/')}", strict=False)
    hosts = max(network.num_addresses - 2, 0)
    first = network.network_address if network.prefixlen >= 31 else network.network_address + 1
    last = network.broadcast_address if network.prefixlen >= 31 else network.broadcast_address - 1
    return SubnetResult(network.prefixlen, str(network.netmask), str(network.network_address), str(network.broadcast_address), str(first), str(last), hosts)


def same_subnet(ip_a: str, ip_b: str, mask_or_cidr: str) -> dict[str, str | bool]:
    first = calculate_subnet(ip_a, mask_or_cidr)
    second = calculate_subnet(ip_b, mask_or_cidr)
    return {"same": first.network == second.network, "network_a": first.network, "network_b": second.network}


def validate_ips(values: list[str], mask_or_cidr: str | None = None) -> list[dict[str, str | bool]]:
    counts = {value.strip(): sum(x.strip() == value.strip() for x in values) for value in values}
    output = []
    for value in values:
        text = value.strip()
        try:
            address = ipaddress.IPv4Address(text)
            item: dict[str, str | bool] = {"ip": text, "valid": True, "duplicate": counts[text] > 1, "kind": "host"}
            if mask_or_cidr:
                net = ipaddress.IPv4Network(f"{text}/{mask_or_cidr.strip().lstrip('/')}", strict=False)
                item["kind"] = "network" if address == net.network_address else "broadcast" if address == net.broadcast_address else "host"
            output.append(item)
        except ValueError as exc:
            output.append({"ip": text, "valid": False, "duplicate": False, "kind": "invalid", "error": str(exc)})
    return output


def generate_commands(host: str, port: int | None = None) -> dict[str, list[str]]:
    try:
        safe_host = str(ipaddress.ip_address(host.strip()))
    except ValueError:
        if not re.fullmatch(r"(?=.{1,253}$)(?!-)[A-Za-z0-9.-]+(?<!-)", host.strip()):
            raise ValueError("Enter a valid IP address or hostname.")
        safe_host = host.strip()
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("TCP port must be between 1 and 65535.")
    windows = [f"ping {safe_host}", "ipconfig /all", "arp -a", f"tracert {safe_host}", "netstat -ano"]
    linux = [f"ping -c 4 {safe_host}", "ip addr", "ip route", "arp -a", f"traceroute {safe_host}", "ss -tulpn"]
    if port:
        windows.append(f"Test-NetConnection {safe_host} -Port {port}")
        linux.append(f"nc -vz {safe_host} {port}")
    return {"windows": windows, "linux": linux}

