from fastapi import APIRouter, Depends

from ..auth import get_store
from ..models import (
    CommandOut, CommandRequest, IpValidationOut, IpValidationRequest,
    SameSubnetOut, SameSubnetRequest, SubnetOut, SubnetRequest,
)
from ..store import InMemoryStore


router = APIRouter(prefix="/tools/network", tags=["Network tools"])


@router.post("/subnet", response_model=SubnetOut)
def calculate_subnet(payload: SubnetRequest, store: InMemoryStore = Depends(get_store)):
    return store.service.subnet(payload.ip, payload.mask_or_cidr)


@router.post("/same-subnet", response_model=SameSubnetOut)
def same_subnet(payload: SameSubnetRequest, store: InMemoryStore = Depends(get_store)):
    return store.service.same_subnet(payload.ip_a, payload.ip_b, payload.mask_or_cidr)


@router.post("/validate-ips", response_model=list[IpValidationOut])
def validate_ips(payload: IpValidationRequest, store: InMemoryStore = Depends(get_store)):
    return store.service.validate_ips(payload.values, payload.mask_or_cidr)


@router.post("/commands", response_model=CommandOut)
def commands(payload: CommandRequest, store: InMemoryStore = Depends(get_store)):
    return store.service.commands(payload.host, payload.port)

