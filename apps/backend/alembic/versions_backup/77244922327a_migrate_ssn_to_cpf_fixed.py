"""migrate_ssn_to_cpf_fixed

Revision ID: 77244922327a
Revises: 0ae9658a2a5f
Create Date: 2025-08-08 06:49:36.594748

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "77244922327a"
down_revision: str | Sequence[str] | None = "0ae9658a2a5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Transform SSN column to CPF in development environment."""
    # Step 1: Rename the ssn column to cpf (preserves all data)
    op.alter_column(
        "agent1_clients", "ssn", new_column_name="cpf", existing_type=sa.String(), nullable=False
    )

    # Step 2: Create unique index on the cpf column
    op.create_index("ix_agent1_clients_cpf_unique", "agent1_clients", ["cpf"], unique=True)


def downgrade() -> None:
    """Rollback CPF column to SSN."""
    # Step 1: Drop the unique index on cpf column
    op.drop_index("ix_agent1_clients_cpf_unique", table_name="agent1_clients")

    # Step 2: Rename the cpf column back to ssn
    op.alter_column(
        "agent1_clients", "cpf", new_column_name="ssn", existing_type=sa.String(), nullable=False
    )
