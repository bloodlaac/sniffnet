"""make experiment times timezone-aware

Revision ID: e7f8a9b0c1d2
Revises: d4e5f6a7b8c9
Create Date: 2025-03-08 13:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e7f8a9b0c1d2"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("experiment") as batch_op:
        batch_op.alter_column("start_time", type_=sa.DateTime(timezone=True))
        batch_op.alter_column("end_time", type_=sa.DateTime(timezone=True))


def downgrade() -> None:
    with op.batch_alter_table("experiment") as batch_op:
        batch_op.alter_column("start_time", type_=sa.DateTime(timezone=False))
        batch_op.alter_column("end_time", type_=sa.DateTime(timezone=False))
