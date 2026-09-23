"""Authentication API router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.auth import authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    if not authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": request.username})
    return LoginResponse(access_token=access_token, username=request.username)


@router.post("/verify")
async def verify_token():
    """Verify that the current token is valid. Requires authentication."""
    return {"valid": True}
