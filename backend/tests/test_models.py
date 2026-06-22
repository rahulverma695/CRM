from app.core.models import Tenant, User


def test_tenant_columns():
    cols = set(Tenant.__table__.columns.keys())
    assert {"id", "name", "slug", "plan", "settings", "created_at", "updated_at"} <= cols


def test_user_columns():
    cols = set(User.__table__.columns.keys())
    assert {"id", "tenant_id", "email", "name", "role", "google_id",
            "password_hash", "is_active"} <= cols


def test_user_has_tenant_fk():
    fk = list(User.__table__.c.tenant_id.foreign_keys)[0]
    assert fk.column.table.name == "tenants"
