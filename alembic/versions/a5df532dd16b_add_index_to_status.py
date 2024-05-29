"""Add index to status

Revision ID: a5df532dd16b
Revises: 784d7016604c
Create Date: 2024-05-28 16:37:45.836354

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5df532dd16b'
down_revision: Union[str, None] = '784d7016604c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('places_feedback', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'places_feedback', 'users', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'places_feedback', type_='foreignkey')
    op.drop_column('places_feedback', 'user_id')
    # ### end Alembic commands ###
