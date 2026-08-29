"""create initial schema

Revision ID: 656d40a01667
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "656d40a01667"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("ADMIN", "QA_ENGINEER", "VIEWER", name="userrole"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "INACTIVE", name="userstatus"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # --- projects ---
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "ARCHIVED", name="projectstatus"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_projects_key", "projects", ["key"])
    op.create_index("ix_projects_status", "projects", ["status"])

    # --- project_members ---
    op.create_table(
        "project_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_members"),
    )

    # --- test_suites ---
    op.create_table(
        "test_suites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- test_cases ---
    op.create_table(
        "test_cases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("suite_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("preconditions", sa.Text(), nullable=True),
        sa.Column("steps", sa.JSON(), nullable=True),
        sa.Column("expected_result", sa.Text(), nullable=False),
        sa.Column(
            "priority",
            sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="testcasepriority"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "READY", "DEPRECATED", name="testcasestatus"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["suite_id"], ["test_suites.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_test_cases_title", "test_cases", ["title"])
    op.create_index("ix_test_cases_priority", "test_cases", ["priority"])
    op.create_index("ix_test_cases_status", "test_cases", ["status"])

    # --- test_runs ---
    op.create_table(
        "test_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("environment", sa.String(100), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "NOT_STARTED", "IN_PROGRESS", "COMPLETED", "ABORTED",
                name="testrunstatus",
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_test_runs_status", "test_runs", ["status"])

    # --- test_results ---
    op.create_table(
        "test_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("test_run_id", sa.Integer(), nullable=False),
        sa.Column("test_case_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("NOT_RUN", "PASSED", "FAILED", "BLOCKED", name="testresultstatus"),
            nullable=False,
        ),
        sa.Column("actual_result", sa.Text(), nullable=True),
        sa.Column("executed_by", sa.Integer(), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["executed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["test_case_id"], ["test_cases.id"]),
        sa.ForeignKeyConstraint(["test_run_id"], ["test_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("test_run_id", "test_case_id", name="uq_result_run_case"),
    )

    # --- defects ---
    op.create_table(
        "defects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("test_case_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "severity",
            sa.Enum(
                "BLOCKER", "CRITICAL", "MAJOR", "MINOR", "TRIVIAL",
                name="defectseverity",
            ),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="defectpriority"),
            nullable=False,
        ),
        sa.Column("environment", sa.String(100), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED", "REJECTED",
                name="defectstatus",
            ),
            nullable=False,
        ),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["test_case_id"], ["test_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_defects_status", "defects", ["status"])
    op.create_index("ix_defects_severity", "defects", ["severity"])
    op.create_index("ix_defects_priority", "defects", ["priority"])


def downgrade() -> None:
    op.drop_table("defects")
    op.drop_table("test_results")
    op.drop_table("test_runs")
    op.drop_table("test_cases")
    op.drop_table("test_suites")
    op.drop_table("project_members")
    op.drop_table("projects")
    op.drop_table("users")
