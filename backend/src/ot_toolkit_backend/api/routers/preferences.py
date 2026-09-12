from fastapi import APIRouter, Depends

from ..auth import get_store, require_user
from ..models import FavoritesOut, SetFavoriteRequest
from ..store import InMemoryStore, UserRecord


router = APIRouter(prefix="/favorites", tags=["Preferences"])


@router.get("", response_model=FavoritesOut)
def list_favorites(
    user: UserRecord = Depends(require_user),
    store: InMemoryStore = Depends(get_store),
):
    return FavoritesOut(items=store.favorites_for(user.username))


@router.put("/{item_id}", response_model=FavoritesOut)
def set_favorite(
    item_id: str,
    payload: SetFavoriteRequest,
    user: UserRecord = Depends(require_user),
    store: InMemoryStore = Depends(get_store),
):
    store.service.get_technology(item_id)
    return FavoritesOut(items=store.set_favorite(user.username, item_id, payload.enabled))

