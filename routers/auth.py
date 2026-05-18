from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo.database import Database

import services.auth_service as auth_service
from database import get_db
from models.user import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Database = Depends(get_db)
) -> UserResponse:
    try:
        return auth_service.get_current_user(db, token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


def require_admin(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: UserCreate, db: Database = Depends(get_db)):
    try:
        return auth_service.register(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Database = Depends(get_db)):
    try:
        token = auth_service.authenticate(db, form.username, form.password)
        return {"access_token": token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserResponse)
def me(current_user: UserResponse = Depends(get_current_user)):
    return current_user
