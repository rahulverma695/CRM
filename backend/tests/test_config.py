from app.config import Settings


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h/db")
    monkeypatch.setenv("JWT_SECRET", "secret")
    s = Settings()
    assert s.database_url == "postgresql+asyncpg://u:p@h/db"
    assert s.jwt_secret == "secret"
    assert s.access_token_minutes == 30  # default
