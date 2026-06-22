"""allow email-based login lookup across tenants

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-23
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Permissive SELECT policy: permits reads when no tenant context is set
    # (login happens before a tenant context exists). When app.tenant_id IS set,
    # the tenant_isolation policy governs. Postgres OR-combines permissive policies.
    op.execute("""
        CREATE POLICY login_lookup ON users
        FOR SELECT
        USING (current_setting('app.tenant_id', true) IS NULL
               OR current_setting('app.tenant_id', true) = '');
    """)

    # Patch tenant_isolation to use nullif() so an empty app.tenant_id (empty
    # string) does not cause "invalid input syntax for type uuid" at cast time.
    # Without this, Postgres evaluates ALL permissive policies even when another
    # is already true, and the ::uuid cast on '' raises an error.
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON users;")
    op.execute("""
        CREATE POLICY tenant_isolation ON users
        USING (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid);
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS login_lookup ON users;")
    # Restore original tenant_isolation (without nullif)
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON users;")
    op.execute("""
        CREATE POLICY tenant_isolation ON users
        USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
    """)
