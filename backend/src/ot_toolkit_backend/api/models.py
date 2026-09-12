from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class ErrorResponse(ApiModel):
    code: str
    message: str
    field: str | None = None


class TechnologyOut(ApiModel):
    id: str
    name: str
    acronym: str
    category: str
    classification: str
    overview: str
    runs_over: list[str] = Field(default_factory=list)
    related: list[str] = Field(default_factory=list)
    architecture: str = ""
    physical_medium: str = ""
    topology: str = ""
    speed: str = ""
    addressing: str = ""
    ports: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    typical_devices: list[str] = Field(default_factory=list)
    applications: list[str] = Field(default_factory=list)
    key_concepts: list[str] = Field(default_factory=list)
    advantages: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    faults: list[str] = Field(default_factory=list)
    troubleshooting: list[str] = Field(default_factory=list)
    organization: str = ""
    standard: str = ""
    sources: list[str] = Field(default_factory=list)


class PortOut(ApiModel):
    port: str
    transport: str
    name: str
    technology: str
    purpose: str


class GlossaryOut(ApiModel):
    term: str
    definition: str
    category: str
    related: list[str] = Field(default_factory=list)
    technology_id: str | None = None


class SearchResultOut(ApiModel):
    kind: Literal["Technology", "Port", "Glossary"]
    id: str
    title: str
    subtitle: str


class HierarchyOut(ApiModel):
    technology: TechnologyOut
    runs_over: list[TechnologyOut]
    used_by: list[TechnologyOut]
    related: list[TechnologyOut]


class ComparisonRequest(ApiModel):
    left_id: str = Field(min_length=1)
    right_id: str = Field(min_length=1)


class ComparisonRow(ApiModel):
    label: str
    left: str
    right: str


class ComparisonOut(ApiModel):
    left: TechnologyOut
    right: TechnologyOut
    rows: list[ComparisonRow]


class FavoritesOut(ApiModel):
    items: list[str]


class SetFavoriteRequest(ApiModel):
    enabled: bool


NumericFormat = Literal["UInt8", "Int8", "UInt16", "Int16", "UInt32", "Int32", "UInt64", "Int64"]


class NumberConversionRequest(ApiModel):
    value: str = Field(min_length=1)
    numeric_format: NumericFormat


class NumberConversionOut(ApiModel):
    decimal: int
    binary: str
    hex: str
    octal: str
    bits: Literal[8, 16, 32, 64]


class IeeeEncodeRequest(ApiModel):
    value: float
    precision: Literal[32, 64]


class IeeeDecodeRequest(ApiModel):
    hex: str = Field(min_length=8, max_length=16)
    precision: Literal[32, 64]


class HexOut(ApiModel):
    hex: str


class FloatOut(ApiModel):
    value: float | Literal["nan", "inf", "-inf"]


class HexBytesRequest(ApiModel):
    hex: str = Field(min_length=2)


class EndiannessInterpretation(ApiModel):
    operation: str
    hex: str
    uint32: int
    int32: int
    float32: float | Literal["nan", "inf", "-inf"]


class EndiannessOut(ApiModel):
    ABCD: EndiannessInterpretation
    BADC: EndiannessInterpretation
    CDAB: EndiannessInterpretation
    DCBA: EndiannessInterpretation


class ModbusAddressRequest(ApiModel):
    reference: str = Field(min_length=5)


class ModbusAddressOut(ApiModel):
    type: Literal["Coil", "Discrete Input", "Input Register", "Holding Register"]
    reference: str
    zero_based_offset: int
    one_based_offset: int


class RegisterDecodeRequest(ApiModel):
    registers: list[int] = Field(min_length=2, max_length=4)

    @field_validator("registers")
    @classmethod
    def validate_register_count_and_range(cls, values: list[int]) -> list[int]:
        if len(values) not in (2, 4):
            raise ValueError("Enter exactly two or four registers.")
        if any(value < 0 or value > 0xFFFF for value in values):
            raise ValueError("Registers must be unsigned 16-bit values.")
        return values


class RegisterInterpretation(ApiModel):
    operation: str | None = None
    hex: str | None = None
    uint32: int | None = None
    int32: int | None = None
    float32: float | Literal["nan", "inf", "-inf"] | None = None
    uint64: int | None = None
    int64: int | None = None
    float64: float | Literal["nan", "inf", "-inf"] | None = None
    text: str | None = None


class ModbusCrcOut(ApiModel):
    crc: str
    transmission_order: str


class FrameDecodeOut(ApiModel):
    address: int
    function_code: int
    function_name: str
    payload_hex: str
    crc_received: str
    crc_calculated: str
    crc_valid: bool
    details: dict[str, Any]


class SubnetRequest(ApiModel):
    ip: str = Field(min_length=1)
    mask_or_cidr: str = Field(min_length=1)


class SubnetOut(ApiModel):
    cidr: int
    subnet_mask: str
    network: str
    broadcast: str
    first_host: str
    last_host: str
    usable_hosts: int


class SameSubnetRequest(ApiModel):
    ip_a: str = Field(min_length=1)
    ip_b: str = Field(min_length=1)
    mask_or_cidr: str = Field(min_length=1)


class SameSubnetOut(ApiModel):
    same: bool
    network_a: str
    network_b: str


class IpValidationRequest(ApiModel):
    values: list[str] = Field(min_length=1)
    mask_or_cidr: str | None = None


class IpValidationOut(ApiModel):
    ip: str
    valid: bool
    duplicate: bool
    kind: Literal["host", "network", "broadcast", "invalid"]
    error: str | None = None


class CommandRequest(ApiModel):
    host: str = Field(min_length=1)
    port: int | None = Field(default=None, ge=1, le=65535)


class CommandOut(ApiModel):
    windows: list[str]
    linux: list[str]


class RegisterRequest(ApiModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=256)


class LoginRequest(ApiModel):
    username: str
    password: str


class UserOut(ApiModel):
    username: str


class TokenOut(ApiModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int

