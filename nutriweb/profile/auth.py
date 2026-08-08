"""Accounts and profile persistence.

Two changes from the app this replaces:

  * Passwords are hashed with bcrypt. The previous version stored them in
    plaintext and compared with `user["password"] == login_pw`.
  * MongoDB is optional. If no connection string is configured the app runs in
    a session-only demo mode instead of crashing on import, so it can be
    developed and reviewed without a database.

Set MONGODB_URI as a Hugging Face Space repository secret -- never in a file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import streamlit as st
from passlib.context import CryptContext

from nutriweb.profile.model import UserProfile

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass
class AuthResult:
    ok: bool
    message: str = ""
    profile: UserProfile | None = None


def _uri() -> str:
    """Read the connection string from Space secrets or the environment."""
    try:
        if "MONGODB_URI" in st.secrets:
            return str(st.secrets["MONGODB_URI"])
    except Exception:
        pass  # no secrets.toml at all is a normal local state
    return os.environ.get("MONGODB_URI", "")


@st.cache_resource(show_spinner=False)
def _collections():
    """Return (users, history) collections, or (None, None) in demo mode."""
    uri = _uri()
    if not uri:
        return None, None
    try:
        from pymongo import MongoClient

        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db_name = os.environ.get("MONGO_DB_NAME", "nutriweb_db")
        try:
            db_name = str(st.secrets.get("MONGO_DB_NAME", db_name))
        except Exception:
            pass
        db = client[db_name]
        return db["users"], db["history"]
    except Exception as exc:  # unreachable database must not break the app
        st.warning(f"Could not reach the account database ({exc}). Running in demo mode.")
        return None, None


def _verify(password: str, hashed: str) -> bool:
    """Check a password without raising on a missing or malformed hash.

    passlib raises on an empty or unrecognised hash string, which would turn a
    corrupted record into a 500 rather than a failed login.
    """
    if not hashed:
        return False
    try:
        return _pwd.verify(password, hashed)
    except (ValueError, TypeError):
        return False


def demo_mode() -> bool:
    users, _ = _collections()
    return users is None


def _demo_store() -> dict:
    return st.session_state.setdefault("_demo_users", {})


def register(user_id: str, password: str, profile: UserProfile) -> AuthResult:
    user_id = (user_id or "").strip()
    if not user_id or not password:
        return AuthResult(False, "Pick a username and a password.")
    if len(password) < 8:
        return AuthResult(False, "Use at least 8 characters for the password.")

    record = {"_id": user_id, "password_hash": _pwd.hash(password), **profile.to_dict()}
    users, _ = _collections()

    if users is None:
        store = _demo_store()
        if user_id in store:
            return AuthResult(False, "That username is taken.")
        store[user_id] = record
    else:
        from pymongo.errors import DuplicateKeyError

        try:
            users.insert_one(record)
        except DuplicateKeyError:
            return AuthResult(False, "That username is taken.")

    profile.user_id = user_id
    return AuthResult(True, "Account created.", profile)


def login(user_id: str, password: str) -> AuthResult:
    users, _ = _collections()
    record = _demo_store().get(user_id) if users is None else users.find_one({"_id": user_id})

    if not record or not _verify(password, record.get("password_hash", "")):
        # Deliberately vague: distinguishing the two leaks which accounts exist.
        return AuthResult(False, "Incorrect username or password.")

    return AuthResult(True, "", UserProfile.from_dict(record))


def save_profile(profile: UserProfile) -> None:
    users, _ = _collections()
    if users is None:
        store = _demo_store()
        if profile.user_id in store:
            store[profile.user_id].update(profile.to_dict())
    else:
        users.update_one({"_id": profile.user_id}, {"$set": profile.to_dict()})


def log_view(user_id: str, product: dict, verdict_summary: str) -> None:
    """Record that a user looked at a product, for the history panel."""
    _, history = _collections()
    entry = {
        "user_id": user_id,
        "code": product.get("code"),
        "product_name": product.get("product_name"),
        "brands": product.get("brands"),
        "health_score": product.get("health_score"),
        "verdict": verdict_summary,
    }
    if history is None:
        st.session_state.setdefault("_demo_history", []).insert(0, entry)
    else:
        from datetime import datetime, timezone

        history.insert_one({**entry, "timestamp": datetime.now(timezone.utc)})


def recent_views(user_id: str, limit: int = 25) -> list[dict]:
    _, history = _collections()
    if history is None:
        return st.session_state.get("_demo_history", [])[:limit]
    return list(
        history.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
    )
