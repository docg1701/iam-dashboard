"""add indexes to questionnaire_drafts for performance

Revision ID: 35e370fcce94
Revises: 88a3d026a671
Create Date: 2025-07-30 21:54:39.810303

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '35e370fcce94'
down_revision = '88a3d026a671'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create indexes for performance as specified in story requirements
    op.create_index('idx_questionnaire_drafts_client_id', 'questionnaire_drafts', ['client_id'])
    op.create_index('idx_questionnaire_drafts_user_id', 'questionnaire_drafts', ['user_id'])


def downgrade() -> None:
    # Drop performance indexes
    op.drop_index('idx_questionnaire_drafts_client_id', 'questionnaire_drafts')
    op.drop_index('idx_questionnaire_drafts_user_id', 'questionnaire_drafts')
