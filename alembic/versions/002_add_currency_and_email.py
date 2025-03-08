"""Add currency and recipient email to invoice

Revision ID: 002
Revises: 001
Create Date: 2024-03-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add the new columns
    op.add_column('invoices', sa.Column('recipient_email', sa.String(255), nullable=True))
    op.add_column('invoices', sa.Column('currency_code', sa.String(3), nullable=True, server_default='USD'))


def downgrade() -> None:
    # Remove the columns
    op.drop_column('invoices', 'recipient_email')
    op.drop_column('invoices', 'currency_code')