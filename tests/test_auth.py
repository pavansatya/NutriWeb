"""Password hashing tests.

These exist because of a real failure: the first implementation used passlib,
which is unmaintained and raises on bcrypt 5.x when it probes its backend with
an over-long password. Hashing failed outright, so registration would have been
broken on the deployed Space. Nothing tested hashing, so nothing caught it.
"""

from __future__ import annotations

from nutriweb.profile import auth
from nutriweb.profile.model import UserProfile


class TestHashing:
    def test_hash_then_verify(self):
        hashed = auth._hash("correct-horse-battery-staple")
        assert auth._verify("correct-horse-battery-staple", hashed)

    def test_wrong_password_rejected(self):
        assert not auth._verify("wrong", auth._hash("right-password-here"))

    def test_hash_is_bcrypt_format(self):
        assert auth._hash("whatever").startswith("$2")

    def test_hash_is_salted(self):
        """Two hashes of the same password must differ."""
        assert auth._hash("same-password") != auth._hash("same-password")

    def test_plaintext_never_appears_in_hash(self):
        secret = "supersecretvalue"
        assert secret not in auth._hash(secret)

    def test_long_passphrase_does_not_raise(self):
        """bcrypt rejects >72 bytes; we truncate rather than crash."""
        long_password = "a" * 200
        assert auth._verify(long_password, auth._hash(long_password))

    def test_multibyte_password(self):
        password = "pÃ¡ssw0rd-Ã±-ð¤-Ð¿ÑÐ¾Ð²ÐµÑÐºÐ°"
        assert auth._verify(password, auth._hash(password))

    def test_verify_survives_corrupt_hash(self):
        """A malformed record must fail the login, not crash the app."""
        for bad in ("", "not-a-hash", "$2b$broken", None):
            assert not auth._verify("anything", bad or "")


class TestUriPrecedence:
    """The environment must win over any secrets file.

    A stale `.streamlit/secrets.toml` once silently overrode an explicitly-set
    MONGODB_URI and redirected connections to an entirely different cluster.
    The run looked successful, which is what made it dangerous.
    """

    def test_environment_is_used(self, monkeypatch):
        monkeypatch.setenv("MONGODB_URI", "mongodb+srv://u:p@from-env.mongodb.net/")
        assert "from-env" in auth._uri()

    def test_environment_beats_secrets_file(self, monkeypatch):
        monkeypatch.setenv("MONGODB_URI", "mongodb+srv://u:p@from-env.mongodb.net/")
        monkeypatch.setattr(
            auth.st, "secrets", {"MONGODB_URI": "mongodb+srv://u:p@from-file.mongodb.net/"}
        )
        assert "from-env" in auth._uri()
        assert "from-file" not in auth._uri()

    def test_secrets_file_used_only_as_fallback(self, monkeypatch):
        monkeypatch.delenv("MONGODB_URI", raising=False)
        monkeypatch.setattr(
            auth.st, "secrets", {"MONGODB_URI": "mongodb+srv://u:p@from-file.mongodb.net/"}
        )
        assert "from-file" in auth._uri()

    def test_blank_environment_does_not_mask_fallback(self, monkeypatch):
        monkeypatch.setenv("MONGODB_URI", "   ")
        monkeypatch.setattr(
            auth.st, "secrets", {"MONGODB_URI": "mongodb+srv://u:p@from-file.mongodb.net/"}
        )
        assert "from-file" in auth._uri()

    def test_no_configuration_means_demo_mode(self, monkeypatch):
        monkeypatch.delenv("MONGODB_URI", raising=False)
        monkeypatch.setattr(auth.st, "secrets", {})
        assert auth._uri() == ""


class TestDemoMode:
    """Without a database the app must still work, session-scoped."""

    def test_register_and_login_round_trip(self, monkeypatch):
        monkeypatch.setattr(auth, "_collections", lambda: (None, None))
        store: dict = {}
        monkeypatch.setattr(auth, "_demo_store", lambda: store)

        profile = UserProfile(allergens=["en:peanuts"], diets=["Vegan"])
        assert auth.register("tester", "password123", profile).ok

        good = auth.login("tester", "password123")
        assert good.ok
        assert good.profile.allergens == ["en:peanuts"]
        assert good.profile.diets == ["Vegan"]

        assert not auth.login("tester", "wrong-password").ok
        assert not auth.login("nobody", "password123").ok

    def test_duplicate_username_rejected(self, monkeypatch):
        monkeypatch.setattr(auth, "_collections", lambda: (None, None))
        store: dict = {}
        monkeypatch.setattr(auth, "_demo_store", lambda: store)

        assert auth.register("dup", "password123", UserProfile()).ok
        assert not auth.register("dup", "password123", UserProfile()).ok

    def test_short_password_rejected(self, monkeypatch):
        monkeypatch.setattr(auth, "_collections", lambda: (None, None))
        monkeypatch.setattr(auth, "_demo_store", dict)
        assert not auth.register("u", "short", UserProfile()).ok

    def test_stored_record_holds_no_plaintext(self, monkeypatch):
        monkeypatch.setattr(auth, "_collections", lambda: (None, None))
        store: dict = {}
        monkeypatch.setattr(auth, "_demo_store", lambda: store)

        auth.register("tester", "myplaintextpw", UserProfile())
        assert "myplaintextpw" not in str(store)

    def test_failure_message_does_not_reveal_account_existence(self, monkeypatch):
        monkeypatch.setattr(auth, "_collections", lambda: (None, None))
        store: dict = {}
        monkeypatch.setattr(auth, "_demo_store", lambda: store)
        auth.register("real", "password123", UserProfile())

        wrong_password = auth.login("real", "nope-wrong").message
        unknown_user = auth.login("ghost", "nope-wrong").message
        assert wrong_password == unknown_user
