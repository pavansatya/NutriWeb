"""End-to-end check of the account path against a real MongoDB cluster.

Verifies what the login form actually depends on: that a user can be created,
that the password is stored hashed rather than in plaintext, that the right
password authenticates, that the wrong one does not, and that profile edits
persist. Creates a temporary account and removes it afterwards.

Run it before trusting the UI -- it fails with a clear message instead of a
Streamlit stack trace.

Usage:
    MONGODB_URI='mongodb+srv://...' python scripts/check_auth.py
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nutriweb.profile import auth  # noqa: E402
from nutriweb.profile.model import UserProfile  # noqa: E402

PASSWORD = "correct-horse-battery-staple"


def main() -> int:
    if not os.environ.get("MONGODB_URI"):
        print("MONGODB_URI is not set — the app would run in session-only demo mode.")
        print("\n  MONGODB_URI='mongodb+srv://...' python scripts/check_auth.py")
        return 2

    # Always state which cluster we are about to write to. A stale
    # .streamlit/secrets.toml once silently redirected this to a different
    # cluster, and the run looked entirely successful.
    host = auth._uri().rsplit("@", 1)[-1].split("/")[0]
    print(f"cluster: {host}\n")

    stale = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"
    if stale.exists():
        print(f"! {stale} exists and may contain another connection string.")
        print("  The environment takes priority, but delete the file to be safe.\n")

    if auth.demo_mode():
        print("✗ Could not reach the database; the app would fall back to demo mode.")
        print("  Run scripts/check_mongo.py to diagnose.")
        return 1

    users, _ = auth._collections()
    user_id = f"_selftest_{uuid.uuid4().hex[:8]}"
    failures = 0

    def check(label: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        print(f"{'✓' if ok else '✗'} {label}" + (f"  — {detail}" if detail and not ok else ""))
        if not ok:
            failures += 1

    try:
        profile = UserProfile(
            allergens=["en:peanuts"], diets=["Vegan"], high_blood_pressure=True
        )
        result = auth.register(user_id, PASSWORD, profile)
        check("register a new account", result.ok, result.message)

        duplicate = auth.register(user_id, PASSWORD, profile)
        check("reject a duplicate username", not duplicate.ok)

        check("reject a too-short password",
              not auth.register(f"{user_id}_x", "short", profile).ok)

        record = users.find_one({"_id": user_id}) or {}
        stored = record.get("password_hash", "")
        check("password stored as a bcrypt hash", stored.startswith("$2"))
        check("plaintext password NOT stored",
              PASSWORD not in str(record))

        good = auth.login(user_id, PASSWORD)
        check("log in with the correct password", good.ok, good.message)
        if good.ok:
            check("allergens survive the round trip",
                  good.profile.allergens == ["en:peanuts"])
            check("diet survives the round trip", good.profile.diets == ["Vegan"])
            check("health flags survive the round trip",
                  good.profile.high_blood_pressure is True)

        check("reject the wrong password", not auth.login(user_id, "wrong-password").ok)
        check("reject an unknown user", not auth.login("_no_such_user_", PASSWORD).ok)

        if good.ok:
            edited = good.profile
            edited.diets = ["Vegetarian"]
            auth.save_profile(edited)
            check("profile edits persist",
                  auth.login(user_id, PASSWORD).profile.diets == ["Vegetarian"])

    finally:
        users.delete_one({"_id": user_id})
        users.delete_one({"_id": f"{user_id}_x"})
        print(f"\ncleaned up test account {user_id}")

    print(
        "\nAll checks passed. Accounts will persist."
        if not failures else f"\n{failures} check(s) FAILED."
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
