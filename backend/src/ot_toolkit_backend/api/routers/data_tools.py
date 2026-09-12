from __future__ import annotations

import math
from typing import Any

from fastapi import APIRouter, Depends

from ..auth import get_store
from ..models import (
    EndiannessOut, FloatOut, HexBytesRequest, HexOut, IeeeDecodeRequest,
    IeeeEncodeRequest, NumberConversionOut, NumberConversionRequest,
)
from ..store import InMemoryStore


router = APIRouter(prefix="/tools", tags=["Data tools"])


def safe_float(value: float) -> float | str:
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return value


def safe_float_fields(value: Any) -> Any:
    if isinstance(value, float):
        return safe_float(value)
    if isinstance(value, dict):
        return {key: safe_float_fields(item) for key, item in value.items()}
    if isinstance(value, list):
        return [safe_float_fields(item) for item in value]
    return value


@router.post("/numbers/convert", response_model=NumberConversionOut)
def convert_number(payload: NumberConversionRequest, store: InMemoryStore = Depends(get_store)):
    return store.service.number_conversion(payload.value, payload.numeric_format)


@router.post("/ieee754/encode", response_model=HexOut)
def encode_ieee754(payload: IeeeEncodeRequest, store: InMemoryStore = Depends(get_store)):
    return HexOut(hex=store.service.ieee_to_hex(payload.value, payload.precision))


@router.post("/ieee754/decode", response_model=FloatOut)
def decode_ieee754(payload: IeeeDecodeRequest, store: InMemoryStore = Depends(get_store)):
    return FloatOut(value=safe_float(store.service.ieee_from_hex(payload.hex, payload.precision)))


@router.post("/endianness/decode", response_model=EndiannessOut)
def decode_endianness(payload: HexBytesRequest, store: InMemoryStore = Depends(get_store)):
    return safe_float_fields(store.service.endian_decode(payload.hex))

