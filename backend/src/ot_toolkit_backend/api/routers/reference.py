from fastapi import APIRouter, Depends, Query

from ..auth import get_store
from ..models import GlossaryOut, PortOut, TechnologyOut
from ..store import InMemoryStore


router = APIRouter(tags=["Reference"])


@router.get("/technologies", response_model=list[TechnologyOut])
def list_technologies(
    category: str | None = Query(default=None),
    store: InMemoryStore = Depends(get_store),
):
    return store.service.list_technologies(category)


@router.get("/technologies/{technology_id}", response_model=TechnologyOut)
def get_technology(technology_id: str, store: InMemoryStore = Depends(get_store)):
    return store.service.get_technology(technology_id)


@router.get("/categories", response_model=list[str])
def list_categories(store: InMemoryStore = Depends(get_store)):
    return store.service.list_categories()


@router.get("/ports", response_model=list[PortOut])
def list_ports(q: str = Query(default=""), store: InMemoryStore = Depends(get_store)):
    return store.service.list_ports(q)


@router.get("/glossary", response_model=list[GlossaryOut])
def list_glossary(q: str = Query(default=""), store: InMemoryStore = Depends(get_store)):
    return store.service.list_glossary(q)


@router.get("/troubleshooting", response_model=dict[str, list[str]])
def list_troubleshooting(store: InMemoryStore = Depends(get_store)):
    return store.service.list_troubleshooting()

