"""Implement onboarding and streak mechanics

Revision ID: <your_revision_id>
Revises: <previous_revision_id>
Create Date: <your_create_date>

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '<your_revision_id>'
down_revision: Union[str, Sequence[str], None] = '<previous_revision_id>'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### Batch operations for the 'users' table ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('current_streak', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('longest_streak', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('last_streak_update', sa.DateTime(), nullable=True))
        batch_op.alter_column('hrga',
               existing_type=sa.TEXT(),
               nullable=True)

    # ### Batch operations for the 'daily_results' table ###
    with op.batch_alter_table('daily_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('xp_awarded', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('discipline_stat_gain', sa.Integer(), server_default='0', nullable=False))

    # ### Batch operations for the 'focus_blocks' table ###
    with op.batch_alter_table('focus_blocks', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # ### Downgrade operations for the 'focus_blocks' table ###
    with op.batch_alter_table('focus_blocks', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)

    # ### Downgrade operations for the 'daily_results' table ###
    with op.batch_alter_table('daily_results', schema=None) as batch_op:
        batch_op.drop_column('discipline_stat_gain')
        batch_op.drop_column('xp_awarded')

    # ### Downgrade operations for the 'users' table ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('hrga',
               existing_type=sa.TEXT(),
               nullable=False)
        batch_op.drop_column('last_streak_update')
        batch_op.drop_column('longest_streak')
        batch_op.drop_column('current_streak')