"""add CASCADE delete to questionnaire_drafts foreign keys

Revision ID: 88a3d026a671
Revises: 03fe9a42403e
Create Date: 2025-07-30 21:54:05.109694

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '88a3d026a671'
down_revision = '03fe9a42403e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing foreign key constraints
    op.drop_constraint('questionnaire_drafts_client_id_fkey', 'questionnaire_drafts', type_='foreignkey')
    op.drop_constraint('questionnaire_drafts_user_id_fkey', 'questionnaire_drafts', type_='foreignkey')

    # Recreate with CASCADE delete
    op.create_foreign_key('questionnaire_drafts_client_id_fkey', 'questionnaire_drafts', 'clients', ['client_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('questionnaire_drafts_user_id_fkey', 'questionnaire_drafts', 'users', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # Drop CASCADE foreign key constraints
    op.drop_constraint('questionnaire_drafts_client_id_fkey', 'questionnaire_drafts', type_='foreignkey')
    op.drop_constraint('questionnaire_drafts_user_id_fkey', 'questionnaire_drafts', type_='foreignkey')

    # Recreate without CASCADE
    op.create_foreign_key('questionnaire_drafts_client_id_fkey', 'questionnaire_drafts', 'clients', ['client_id'], ['id'])
    op.create_foreign_key('questionnaire_drafts_user_id_fkey', 'questionnaire_drafts', 'users', ['user_id'], ['id'])
