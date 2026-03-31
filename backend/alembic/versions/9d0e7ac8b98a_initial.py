"""initial

Revision ID: 9d0e7ac8b98a
Revises:
Create Date: 2025-02-09 20:48:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "9d0e7ac8b98a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=20), nullable=True),
        sa.Column("password", sa.String(length=128), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "datasets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=20), nullable=False),
        sa.Column("classes_num", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "training_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("epochs_num", sa.Integer(), nullable=True),
        sa.Column("batch_size", sa.Integer(), nullable=True),
        sa.Column("loss_function", sa.String(length=20), nullable=True),
        sa.Column("learning_rate", sa.Float(), nullable=True),
        sa.Column("optimizer", sa.String(length=20), nullable=True),
        sa.Column("layers_num", sa.Integer(), nullable=True),
        sa.Column("neurons_num", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=True),
        sa.Column("config_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["config_id"], ["training_configs.id"]),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=True),
        sa.Column("config_id", sa.Integer(), nullable=True),
        sa.Column("train_accuracy", sa.Float(), nullable=True),
        sa.Column("train_loss", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["config_id"], ["training_configs.id"]),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "models",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=True),
        sa.Column("config_id", sa.Integer(), nullable=True),
        sa.Column("experiment_id", sa.Integer(), nullable=True),
        sa.Column("params_num", sa.Integer(), nullable=True),
        sa.Column("weights", sa.LargeBinary(), nullable=True),
        sa.Column("name", sa.String(length=20), nullable=True),
        sa.Column("training_time", sa.Interval(), nullable=True),
        sa.ForeignKeyConstraint(["config_id"], ["training_configs.id"]),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"]),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.bulk_insert(
        sa.table(
            "roles",
            sa.column("code", sa.String),
            sa.column("name", sa.String),
        ),
        [
            {"code": "ROLE_USER", "name": "User"},
            {"code": "ROLE_ADMIN", "name": "Administrator"},
        ],
    )


def downgrade() -> None:
    op.drop_table("models")
    op.drop_table("metrics")
    op.drop_table("experiments")
    op.drop_table("training_configs")
    op.drop_table("datasets")
    op.drop_table("users")
    op.drop_table("roles")
