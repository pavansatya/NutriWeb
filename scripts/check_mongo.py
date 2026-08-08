"""Verify a MongoDB connection string before wiring it into the app.

Catches the usual Atlas mistakes -- wrong password, IP not allowed, unescaped
special characters -- with a clear message instead of a Streamlit stack trace.

Usage:
    MONGODB_URI='mongodb+srv://user:pass@cluster.xxxxx.mongodb.net/...' \
        python scripts/check_mongo.py

Never paste the URI as a shell argument: it would land in your shell history.
"""

from __future__ import annotations

import os
import sys
from urllib.parse import quote_plus, urlparse


def redact(uri: str) -> str:
    """Show the URI without the password, safe to print or paste."""
    try:
        parsed = urlparse(uri)
        if parsed.password:
            return uri.replace(parsed.password, "***")
    except ValueError:
        pass
    return uri


def main() -> int:
    uri = os.environ.get("MONGODB_URI", "").strip()
    if not uri:
        print("MONGODB_URI is not set.\n")
        print("  MONGODB_URI='mongodb+srv://...' python scripts/check_mongo.py")
        return 2

    print(f"Testing: {redact(uri)}\n")

    if not uri.startswith(("mongodb://", "mongodb+srv://")):
        print("✗ Does not look like a MongoDB URI (expected mongodb+srv://...).")
        return 1

    # A raw '@' or '/' inside the password breaks URI parsing. Atlas passwords
    # frequently contain them, and this is the most common setup failure.
    # Split on the LAST '@': the host follows it, and an unescaped '@' in the
    # password would otherwise hide the very problem we are looking for.
    remainder = uri.split("://", 1)[1]
    creds = remainder.rsplit("@", 1)[0] if "@" in remainder else ""
    if ":" in creds:
        password = creds.split(":", 1)[1]
        if password != quote_plus(password):
            print("✗ The password contains characters that must be percent-encoded.")
            print(f"  Replace it in the URI with: {quote_plus(password)}")
            print("  (or regenerate a password with only letters and digits)")
            return 1

    try:
        from pymongo import MongoClient
    except ImportError:
        print("✗ pymongo is not installed. Run: pip install -r requirements.txt")
        return 1

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=8000)
        client.admin.command("ping")
        print("✓ Connected.")
    except Exception as exc:
        message = str(exc)
        print(f"✗ Could not connect.\n\n  {message[:300]}\n")
        lowered = message.lower()
        if "authentication failed" in lowered or "bad auth" in lowered:
            print("  → Wrong username or password. Check Atlas > Database Access.")
        elif "timed out" in lowered or "no replica set members" in lowered:
            print("  → Your IP is probably not allowed.")
            print("    Atlas > Network Access > Add IP Address.")
            print("    Hugging Face Spaces have no fixed IP, so a Space needs 0.0.0.0/0.")
        elif (
            "nodename nor servname" in lowered
            or "name or service not known" in lowered
            or "does not exist" in lowered
        ):
            print("  → The cluster hostname does not resolve. Check for a typo,")
            print("    and make sure you copied the whole string from Atlas.")
        return 1

    db_name = os.environ.get("MONGO_DB_NAME", "nutriweb_db")
    db = client[db_name]

    # Prove the credential can actually write, not merely connect. A read-only
    # user connects fine and then fails at registration time.
    try:
        db["_nutriweb_write_test"].insert_one({"ok": True})
        db["_nutriweb_write_test"].drop()
        print(f"✓ Read/write access confirmed on database '{db_name}'.")
    except Exception as exc:
        print(f"✗ Connected, but cannot write to '{db_name}':\n  {str(exc)[:200]}")
        print("  → In Atlas > Database Access, give the user 'Read and write to any database'.")
        return 1

    users = db["users"].estimated_document_count()
    print(f"\nExisting accounts in '{db_name}': {users}")
    print("\nAll good. Set this as a Space secret named MONGODB_URI (never in a file).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
