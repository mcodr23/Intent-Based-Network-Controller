from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_db
from app.models import User
from app.schemas.schemas import LoginRequest, MessageOut, RegisterRequest, TokenResponse
from app.services.audit_service import log_action
from app.services.auth_service import authenticate_user, create_user, ensure_roles


router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=user.username, user_id=user.id, role=user.role.name)
    log_action(
        db,
        action="login",
        resource="auth",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"username": user.username},
        status_code=200,
    )

    return TokenResponse(access_token=token, user=user)


@router.post("/register", response_model=MessageOut)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    ensure_roles(db)

    existing_user = db.query(User).filter(User.username == payload.username).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    existing_email = db.query(User).filter(User.email == payload.email).first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    allowed_roles = {"viewer", "network engineer"}
    selected_role = payload.role if payload.role.lower() in allowed_roles else "Viewer"
    user = create_user(db, payload.username, payload.email, payload.password, selected_role.title())

    log_action(
        db,
        action="register",
        resource="auth",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"role": user.role.name},
        status_code=201,
    )

    return MessageOut(message=f"User {user.username} registered successfully")
