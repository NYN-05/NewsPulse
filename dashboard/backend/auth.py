import os
import json
import bcrypt
import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import HTTPException, Request, WebSocket
from pydantic import BaseModel, Field
from config.settings import get, atomic_write_json, atomic_read_json

logger = logging.getLogger("auth")

USERS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "config",
)
USERS_FILE = os.path.join(USERS_DIR, "users.json")

ROLES = {"viewer": 1, "analyst": 2, "admin": 3}


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="viewer", pattern=r"^(viewer|analyst|admin)$")


def _ensure_users_file():
    os.makedirs(USERS_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        default_users = {
            "admin": {
                "password_hash": bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode(),
                "role": "admin",
                "created_at": datetime.now().isoformat(),
            }
        }
        atomic_write_json(USERS_FILE, default_users)


def _load_users() -> Dict:
    _ensure_users_file()
    return atomic_read_json(USERS_FILE) or {}


def _save_users(users: Dict):
    atomic_write_json(USERS_FILE, users)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _get_jwt_secret() -> str:
    secret = get("auth.jwt_secret", "")
    if not secret or secret == "change-me-in-production":
        logger.error(
            "JWT secret is not configured or is still the default! "
            "Set NEWSPULSE_AUTH_JWT_SECRET environment variable."
        )
        raise RuntimeError("JWT secret not configured")
    return secret


def create_token(username: str, role: str) -> str:
    secret = _get_jwt_secret()
    expiry = datetime.now() + timedelta(hours=get("auth.jwt_expiry_hours", 24))
    payload = {
        "sub": username,
        "role": role,
        "iat": datetime.now(),
        "exp": expiry,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_token(token: str) -> Optional[Dict]:
    try:
        secret = _get_jwt_secret()
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, RuntimeError):
        return None


def authenticate(username: str, password: str) -> Optional[Dict]:
    users = _load_users()
    user = users.get(username)
    if not user:
        return None
    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return None
    return {"username": username, "role": user["role"]}


def create_user(username: str, password: str, role: str = "viewer"):
    if role not in ROLES:
        raise ValueError(f"Invalid role: {role}. Must be one of {list(ROLES.keys())}")
    if len(username) < 3 or len(username) > 32:
        raise ValueError("Username must be 3-32 characters")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    users = _load_users()
    if username in users:
        raise ValueError(f"User '{username}' already exists")
    users[username] = {
        "password_hash": hash_password(password),
        "role": role,
        "created_at": datetime.now().isoformat(),
    }
    _save_users(users)
    logger.info("User '%s' created with role '%s'", username, role)


def delete_user(username: str):
    if username == "admin":
        raise ValueError("Cannot delete admin user")
    users = _load_users()
    if username not in users:
        raise ValueError(f"User '{username}' not found")
    del users[username]
    _save_users(users)


async def get_current_user(request: Request) -> Dict:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header[7:]
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


def require_role(required_role: str):
    min_level = ROLES.get(required_role, 0)
    async def checker(request: Request):
        if not get("auth.enabled", True):
            return {"username": "anonymous", "role": "admin", "sub": "anonymous"}
        payload = await get_current_user(request)
        role = payload.get("role", "viewer")
        if ROLES.get(role, 0) < min_level:
            raise HTTPException(
                status_code=403,
                detail=f"Requires {required_role} role",
            )
        return payload
    return checker


async def optional_auth(request: Request) -> Dict:
    if not get("auth.enabled", True):
        return {"username": "anonymous", "role": "admin", "sub": "anonymous"}
    return await get_current_user(request)


async def verify_ws_token(websocket: WebSocket) -> Optional[Dict]:
    token = websocket.query_params.get("token", "")
    if not token:
        auth_header = websocket.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        return None
    if not get("auth.enabled", True):
        return {"username": "anonymous", "role": "admin", "sub": "anonymous"}
    return verify_token(token)
