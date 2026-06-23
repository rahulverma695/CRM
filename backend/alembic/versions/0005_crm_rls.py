# backend/alembic/versions/0005_crm_rls.py
"""crm rls policies

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-23
"""
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

CRM_TABLES = [
    "pipeline_stages",
    "leads",
    "deals",
    "activities",
    "crm_tasks",
    "custom_views",
]

POLICY_EXPR = "tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid"


def upgrade() -> None:
    for table in CRM_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            f"USING ({POLICY_EXPR}) "
            f"WITH CHECK ({POLICY_EXPR})"
        )


def downgrade() -> None:
    for table in reversed(CRM_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
