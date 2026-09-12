from __future__ import annotations

import json
import os
from dataclasses import fields
from importlib.resources import files
from pathlib import Path
from typing import Any

from .. import engineering
from ..models import Comparison, GlossaryEntry, PortEntry, SearchResult, Technology
from .base import ToolkitService


class MockToolkitService(ToolkitService):
    """Complete local backend: bundled JSON, calculations, and local favorites."""

    def __init__(self, favorites_path: Path | None = None) -> None:
        self._technologies = self._load_technologies()
        self._ports = tuple(PortEntry(**row) for row in self._read_json("ports.json"))
        self._glossary = self._load_glossary()
        self._validate_relationships()
        self._favorites_path = favorites_path or self._default_favorites_path()

    @staticmethod
    def _read_json(name: str) -> list[dict[str, Any]]:
        return json.loads(files("ot_toolkit.data").joinpath(name).read_text(encoding="utf-8"))

    @classmethod
    def _load_technologies(cls) -> dict[str, Technology]:
        required = {"id", "name", "acronym", "category", "classification", "overview"}
        allowed = {item.name for item in fields(Technology)}
        scalar_optionals = {"architecture", "physical_medium", "topology", "speed", "addressing", "organization", "standard"}
        output: dict[str, Technology] = {}
        for index, source in enumerate(cls._read_json("technologies.json")):
            missing, unknown = required - source.keys(), source.keys() - allowed
            if missing or unknown:
                raise ValueError(f"Technology record {index} invalid; missing={missing}, unknown={unknown}")
            row = dict(source)
            for key in allowed - required - scalar_optionals:
                if key in row:
                    row[key] = tuple(row[key])
            item = Technology(**row)
            if item.id in output:
                raise ValueError(f"Duplicate technology id: {item.id}")
            output[item.id] = item
        return output

    @classmethod
    def _load_glossary(cls) -> tuple[GlossaryEntry, ...]:
        output = []
        for source in cls._read_json("glossary.json"):
            row = dict(source)
            row["related"] = tuple(row.get("related", ()))
            output.append(GlossaryEntry(**row))
        return tuple(output)

    def _validate_relationships(self) -> None:
        ids = set(self._technologies)
        external = {"mbp", "cip", "com-dcom", "udp"}
        for item in self._technologies.values():
            unresolved = (set(item.related) | set(item.runs_over)) - ids - external
            if unresolved:
                raise ValueError(f"{item.id} has unresolved relationships: {sorted(unresolved)}")
        terms = [item.term.casefold() for item in self._glossary]
        if len(terms) != len(set(terms)):
            raise ValueError("Glossary terms must be unique.")

    @staticmethod
    def _default_favorites_path() -> Path:
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "OTToolkit" / "favorites.json"

    def list_technologies(self, category: str | None = None) -> list[Technology]:
        items = list(self._technologies.values())
        if category:
            items = [item for item in items if item.category == category]
        return sorted(items, key=lambda item: item.name.casefold())

    def get_technology(self, technology_id: str) -> Technology:
        try:
            return self._technologies[technology_id]
        except KeyError as exc:
            raise KeyError(f"Unknown technology: {technology_id}") from exc

    def list_categories(self) -> list[str]:
        order = ["Physical & Serial", "Network / Bus", "Field & Device", "Industrial Ethernet", "Instrumentation", "OPC / Interoperability", "IIoT", "Building", "Power", "Supporting Network"]
        present = {item.category for item in self._technologies.values()}
        return [name for name in order if name in present]

    def list_ports(self, query: str = "") -> list[PortEntry]:
        needle = query.strip().casefold()
        return [item for item in self._ports if not needle or needle in " ".join((item.port, item.transport, item.name, item.technology, item.purpose)).casefold()]

    def list_glossary(self, query: str = "") -> list[GlossaryEntry]:
        needle = query.strip().casefold()
        matches = [item for item in self._glossary if not needle or needle in " ".join((item.term, item.definition, item.category, *item.related)).casefold()]
        if not needle:
            return matches
        return sorted(matches, key=lambda item: (
            0 if item.term.casefold() == needle else 1 if item.definition.casefold().startswith(needle) else 2,
            item.term.casefold(),
        ))

    def list_troubleshooting(self) -> dict[str, list[str]]:
        return {item.id: list(item.troubleshooting) for item in self._technologies.values() if item.troubleshooting}

    def search(self, query: str) -> list[SearchResult]:
        needle = query.strip().casefold()
        if not needle:
            return []
        ranked: list[tuple[int, SearchResult]] = []
        for item in self._technologies.values():
            text = " ".join((item.name, item.acronym, item.classification, item.overview, item.standard, *item.ports, *item.files, *item.key_concepts, *item.related)).casefold()
            if needle in text:
                exact_terms = {item.name.casefold(), item.acronym.casefold(), *(value.casefold() for value in item.files), *(value.casefold() for value in item.key_concepts)}
                ranked.append((0 if needle in exact_terms else 1, SearchResult("Technology", item.id, item.name, f"{item.classification} · {item.category}")))
        for item in self._ports:
            if needle in " ".join((item.port, item.name, item.technology, item.purpose)).casefold():
                ranked.append((0 if needle == item.port.casefold() else 2, SearchResult("Port", item.port, f"{item.port} · {item.name}", f"{item.transport} · {item.purpose}")))
        for item in self._glossary:
            if needle in " ".join((item.term, item.definition, *item.related)).casefold():
                ranked.append((1 if needle == item.term.casefold() else 2, SearchResult("Glossary", item.term, item.term, item.definition)))
        seen, output = set(), []
        for _, result in sorted(ranked, key=lambda pair: (pair[0], pair[1].title.casefold())):
            key = (result.kind, result.id)
            if key not in seen:
                seen.add(key)
                output.append(result)
        return output[:100]

    def compare(self, left_id: str, right_id: str) -> Comparison:
        left, right = self.get_technology(left_id), self.get_technology(right_id)
        fields_to_compare = [("Classification", "classification"), ("Category / layer", "category"), ("Runs over", "runs_over"), ("Architecture", "architecture"), ("Physical medium", "physical_medium"), ("Topology", "topology"), ("Speed", "speed"), ("Addressing", "addressing"), ("Common ports", "ports"), ("Configuration files", "files"), ("Typical devices", "typical_devices"), ("Applications", "applications"), ("Strengths", "advantages"), ("Limitations", "limitations"), ("Organization", "organization"), ("Standard", "standard")]
        def display(value: Any) -> str:
            return ", ".join(value) if isinstance(value, tuple) else str(value or "—")
        return Comparison(left, right, tuple((label, display(getattr(left, key)), display(getattr(right, key))) for label, key in fields_to_compare))

    def hierarchy(self, technology_id: str) -> dict[str, Any]:
        item = self.get_technology(technology_id)
        return {"technology": item, "runs_over": [self._technologies[x] for x in item.runs_over if x in self._technologies], "used_by": [x for x in self._technologies.values() if item.id in x.runs_over], "related": [self._technologies[x] for x in item.related if x in self._technologies]}

    def favorites(self) -> set[str]:
        try:
            values = json.loads(self._favorites_path.read_text(encoding="utf-8"))
            return {str(item) for item in values if isinstance(item, str)}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return set()

    def set_favorite(self, item_id: str, enabled: bool) -> None:
        values = self.favorites()
        values.add(item_id) if enabled else values.discard(item_id)
        self._favorites_path.parent.mkdir(parents=True, exist_ok=True)
        self._favorites_path.write_text(json.dumps(sorted(values), indent=2), encoding="utf-8")

    def number_conversion(self, value: str, numeric_format: str) -> dict[str, Any]: return engineering.convert_number(value, numeric_format)
    def ieee_to_hex(self, value: float, precision: int) -> str: return engineering.ieee_float_to_hex(value, precision)
    def ieee_from_hex(self, value: str, precision: int) -> float: return engineering.ieee_hex_to_float(value, precision)
    def endian_decode(self, value: str) -> dict[str, Any]: return engineering.decode_endianness(value)
    def modbus_address(self, reference: str) -> dict[str, Any]: return engineering.modbus_address(reference)
    def modbus_registers(self, registers: list[int]) -> dict[str, Any]: return engineering.decode_registers(registers)
    def modbus_crc(self, value: str) -> dict[str, str]:
        crc = engineering.modbus_crc(engineering.clean_hex(value))
        return {"crc": f"{crc:04X}", "transmission_order": crc.to_bytes(2, "little").hex(" ").upper()}
    def modbus_frame(self, value: str): return engineering.decode_modbus_frame(value)
    def subnet(self, ip: str, mask_or_cidr: str): return engineering.calculate_subnet(ip, mask_or_cidr)
    def same_subnet(self, ip_a: str, ip_b: str, mask_or_cidr: str) -> dict[str, Any]: return engineering.same_subnet(ip_a, ip_b, mask_or_cidr)
    def validate_ips(self, values: list[str], mask_or_cidr: str | None = None) -> list[dict[str, Any]]: return engineering.validate_ips(values, mask_or_cidr)
    def commands(self, host: str, port: int | None = None) -> dict[str, list[str]]: return engineering.generate_commands(host, port)
