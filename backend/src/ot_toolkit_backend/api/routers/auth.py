from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import get_store, hash_password, verify_password
from ..models import LoginRequest, RegisterRequest, TokenOut, UserOut
from ..store import InMemoryStore


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, store: InMemoryStore = Depends(get_store)) -> UserOut:
    user = store.add_user(payload.username, hash_password(payload.password))
    return UserOut(username=user.username)


@router.post("/token", response_model=TokenOut)
def login(payload: LoginRequest, store: InMemoryStore = Depends(get_store)) -> TokenOut:
    user = store.get_user(payload.username)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, expires_in = store.issue_token(user.username)
    return TokenOut(access_token=token, expires_in=expires_in)

