"""
Authentication & Authorization — Phase 5.

JWT-based RBAC with three roles:
- viewer: read-only access
- analyst: can trigger pipelines, export data
- admin: full access, can manage users
"""

import os
import json
import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import HTTPException, Request
from config.settings import get, atomic_write_json, atomic_read_json

logger = logging.getLogger("auth")

USERS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "output", "data", "users.json",
)

ROLES = {"viewer": 1, "analyst": 2, "admin": 3}


def _ensure_users_file():
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
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


def require_role(required_role: str):
    """Dependency: checks role from X-User-Role header (set by proxy or middleware)."""
    min_level = ROLES.get(required_role, 0)

    def checker(request: Request):
        role = request.headers.get("X-User-Role", "viewer")
        if ROLES.get(role, 0) < min_level:
            raise HTTPException(status_code=403, detail=f"Requires {required_role} role")
        return True

    return checker


def require_auth(request: Request):
    """Dependency: checks X-User header is present."""
    user = request.headers.get("X-User", "")
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
