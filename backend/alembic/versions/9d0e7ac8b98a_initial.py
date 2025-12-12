"""initial

Revision ID: 9d0e7ac8b98a
Revises: 
Create Date: 2025-02-09 20:48:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9d0e7ac8b98a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=20), nullable=True),
        sa.Column("password", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "dataset",
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=20), nullable=False),
        sa.Column("classes_num", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("dataset_id"),
    )
    op.create_table(
        "training_config",
        sa.Column("config_id", sa.Integer(), nullable=False),
        sa.Column("epochs_num", sa.Integer(), nullable=True),
        sa.Column("batch_size", sa.Integer(), nullable=True),
        sa.Column("loss_function", sa.String(length=20), nullable=True),
        sa.Column("learning_rate", sa.Float(), nullable=True),
        sa.Column("optimizer", sa.String(length=20), nullable=True),
        sa.Column("layers_num", sa.Integer(), nullable=True),
        sa.Column("neurons_num", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("config_id"),
    )
    op.create_table(
        "experiment",
        sa.Column("experiment_id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=True),
        sa.Column("config_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["config_id"],
            ["training_config.config_id"],
        ),
        sa.ForeignKeyConstraint(["dataset_id"], ["dataset.dataset_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.user_id"]),
        sa.PrimaryKeyConstraint("experiment_id"),
    )
    op.create_table(
        "metric",
        sa.Column("metric_id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=True),
        sa.Column("config_id", sa.Integer(), nullable=True),
        sa.Column("train_accuracy", sa.Float(), nullable=True),
        sa.Column("train_loss", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["config_id"],
            ["training_config.config_id"],
        ),
        sa.ForeignKeyConstraint(["dataset_id"], ["dataset.dataset_id"]),
        sa.PrimaryKeyConstraint("metric_id"),
    )
    op.create_table(
        "model",
        sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=True),
        sa.Column("config_id", sa.Integer(), nullable=True),
        sa.Column("params_num", sa.Integer(), nullable=True),
        sa.Column("weights", sa.LargeBinary(), nullable=True),
        sa.Column("name", sa.String(length=20), nullable=True),
        sa.Column("training_time", sa.Interval(), nullable=True),
        sa.ForeignKeyConstraint(
            ["config_id"],
            ["training_config.config_id"],
        ),
        sa.ForeignKeyConstraint(["dataset_id"], ["dataset.dataset_id"]),
        sa.PrimaryKeyConstraint("model_id"),
    )


def downgrade() -> None:
    op.drop_table("model")
    op.drop_table("metric")
    op.drop_table("experiment")
    op.drop_table("training_config")
    op.drop_table("dataset")
    op.drop_table("user")
