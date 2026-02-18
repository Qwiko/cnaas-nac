"""initial_schema

Revision ID: 54c12ecbea91
Revises:
Create Date: 2026-02-16 14:33:55.042603

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "54c12ecbea91"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with open("alembic/schemas/freeradius.sql") as f:
        content = f.read()
        op.execute(content)


def downgrade():
    op.drop_table("nas")
    op.drop_table("nasreload")
    op.drop_table("radacct")
    op.drop_table("radcheck")
    op.drop_table("radgroupcheck")
    op.drop_table("radgroupreply")
    op.drop_table("radpostauth")
    op.drop_table("radreply")
    op.drop_table("radusergroup")
    pass
