"""add val_split to training_config

Revision ID: c1a2b3d4e5f6
Revises: 9d0e7ac8b98a
Create Date: 2025-03-08 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c1a2b3d4e5f6"
down_revision = "bd88966438e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("training_config") as batch_op:
        batch_op.add_column(sa.Column("val_split", sa.Float(), nullable=True, server_default="0.2"))


def downgrade() -> None:
    with op.batch_alter_table("training_config") as batch_op:
        batch_op.drop_column("val_split")
