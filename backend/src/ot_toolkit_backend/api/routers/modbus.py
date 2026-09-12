from fastapi import APIRouter, Depends

from ..auth import get_store
from ..models import (
    FrameDecodeOut, HexBytesRequest, ModbusAddressOut, ModbusAddressRequest,
    ModbusCrcOut, RegisterDecodeRequest, RegisterInterpretation,
)
from ..store import DatabaseStore
from .data_tools import safe_float_fields


router = APIRouter(prefix="/tools/modbus", tags=["Modbus tools"])


@router.post("/address", response_model=ModbusAddressOut)
def convert_address(payload: ModbusAddressRequest, store: DatabaseStore = Depends(get_store)):
    return store.service.modbus_address(payload.reference)


@router.post("/registers/decode", response_model=dict[str, RegisterInterpretation])
def decode_registers(payload: RegisterDecodeRequest, store: DatabaseStore = Depends(get_store)):
    return safe_float_fields(store.service.modbus_registers(payload.registers))


@router.post("/crc", response_model=ModbusCrcOut)
def calculate_crc(payload: HexBytesRequest, store: DatabaseStore = Depends(get_store)):
    return store.service.modbus_crc(payload.hex)


@router.post("/frame/decode", response_model=FrameDecodeOut)
def decode_frame(payload: HexBytesRequest, store: DatabaseStore = Depends(get_store)):
    return store.service.modbus_frame(payload.hex)
