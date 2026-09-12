from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Technology:
    id: str
    name: str
    acronym: str
    category: str
    classification: str
    overview: str
    runs_over: tuple[str, ...] = ()
    related: tuple[str, ...] = ()
    architecture: str = ""
    physical_medium: str = ""
    topology: str = ""
    speed: str = ""
    addressing: str = ""
    ports: tuple[str, ...] = ()
    files: tuple[str, ...] = ()
    typical_devices: tuple[str, ...] = ()
    applications: tuple[str, ...] = ()
    key_concepts: tuple[str, ...] = ()
    advantages: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    faults: tuple[str, ...] = ()
    troubleshooting: tuple[str, ...] = ()
    organization: str = ""
    standard: str = ""
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class PortEntry:
    port: str
    transport: str
    name: str
    technology: str
    purpose: str


@dataclass(frozen=True)
class GlossaryEntry:
    term: str
    definition: str
    category: str
    related: tuple[str, ...] = ()
    technology_id: str | None = None


@dataclass(frozen=True)
class SearchResult:
    kind: str
    id: str
    title: str
    subtitle: str


@dataclass(frozen=True)
class Comparison:
    left: Technology
    right: Technology
    rows: tuple[tuple[str, str, str], ...]


@dataclass(frozen=True)
class SubnetResult:
    cidr: int
    subnet_mask: str
    network: str
    broadcast: str
    first_host: str
    last_host: str
    usable_hosts: int


@dataclass(frozen=True)
class FrameDecode:
    address: int
    function_code: int
    function_name: str
    payload_hex: str
    crc_received: str
    crc_calculated: str
    crc_valid: bool
    details: dict[str, Any] = field(default_factory=dict)

