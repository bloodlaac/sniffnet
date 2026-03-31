"""add experiment status and model weights path

Revision ID: d4e5f6a7b8c9
Revises: c1a2b3d4e5f6
Create Date: 2025-03-08 12:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d4e5f6a7b8c9"
down_revision = "c1a2b3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("models") as batch_op:
        batch_op.add_column(sa.Column("weights_path", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("training_time_seconds", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("available_for_inference", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("external_model_id", sa.Integer(), nullable=True))
        batch_op.create_unique_constraint("uq_models_external_model_id", ["external_model_id"])

    with op.batch_alter_table("experiments") as batch_op:
        batch_op.add_column(sa.Column("model_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("status", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("error_message", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("report_path", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("external_experiment_id", sa.Integer(), nullable=True))
        batch_op.create_unique_constraint("uq_experiments_external_experiment_id", ["external_experiment_id"])
        batch_op.create_foreign_key("experiment_model_id_fkey", "models", ["model_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("experiments") as batch_op:
        batch_op.drop_constraint("experiment_model_id_fkey", type_="foreignkey")
        batch_op.drop_constraint("uq_experiments_external_experiment_id", type_="unique")
        batch_op.drop_column("external_experiment_id")
        batch_op.drop_column("report_path")
        batch_op.drop_column("error_message")
        batch_op.drop_column("status")
        batch_op.drop_column("model_id")

    with op.batch_alter_table("models") as batch_op:
        batch_op.drop_constraint("uq_models_external_model_id", type_="unique")
        batch_op.drop_column("external_model_id")
        batch_op.drop_column("available_for_inference")
        batch_op.drop_column("training_time_seconds")
        batch_op.drop_column("created_at")
        batch_op.drop_column("weights_path")
