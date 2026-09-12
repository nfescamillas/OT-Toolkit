from fastapi import APIRouter, Depends, Query

from ..auth import get_store
from ..models import ComparisonOut, ComparisonRequest, ComparisonRow, HierarchyOut, SearchResultOut
from ..store import DatabaseStore


router = APIRouter(tags=["Discovery"])


@router.get("/search", response_model=list[SearchResultOut])
def search(q: str = Query(min_length=1), store: DatabaseStore = Depends(get_store)):
    return store.service.search(q)


@router.post("/comparisons", response_model=ComparisonOut)
def compare(payload: ComparisonRequest, store: DatabaseStore = Depends(get_store)):
    result = store.service.compare(payload.left_id, payload.right_id)
    return ComparisonOut(
        left=result.left,
        right=result.right,
        rows=[ComparisonRow(label=label, left=left, right=right) for label, left, right in result.rows],
    )


@router.get("/technologies/{technology_id}/hierarchy", response_model=HierarchyOut)
def hierarchy(technology_id: str, store: DatabaseStore = Depends(get_store)):
    return store.service.hierarchy(technology_id)
