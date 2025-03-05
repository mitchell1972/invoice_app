"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-03-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing indexes if they exist
    op.execute('DROP INDEX IF EXISTS ix_customers_email')
    op.execute('DROP INDEX IF EXISTS ix_customers_name')
    op.execute('DROP INDEX IF EXISTS ix_invoices_number')
    
    # Drop existing tables if they exist
    op.execute('DROP TABLE IF EXISTS invoice_items CASCADE')
    op.execute('DROP TABLE IF EXISTS invoices CASCADE')
    op.execute('DROP TABLE IF EXISTS customers CASCADE')
    
    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('company', sa.String(100)),
        sa.Column('phone', sa.String(20)),
        sa.Column('address', sa.String(255)),
        sa.Column('city', sa.String(100)),
        sa.Column('state', sa.String(100)),
        sa.Column('postal_code', sa.String(20)),
        sa.Column('country', sa.String(100)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('customer_id', sa.String(36), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('issue_date', sa.DateTime(), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False),
        sa.Column('tax', sa.Numeric(10, 2), default=0),
        sa.Column('total', sa.Numeric(10, 2), nullable=False),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create invoice_items table
    op.create_table(
        'invoice_items',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('invoice_id', sa.String(36), sa.ForeignKey('invoices.id'), nullable=False),
        sa.Column('description', sa.String(255), nullable=False),
        sa.Column('quantity', sa.Numeric(10, 2), nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('total', sa.Numeric(10, 2), nullable=False)
    )
    
    # Create indexes after tables are created
    op.create_index('ix_customers_name', 'customers', ['name'])
    op.create_index('ix_customers_email', 'customers', ['email'], unique=True)
    op.create_index('ix_invoices_number', 'invoices', ['invoice_number'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('invoice_items')
    op.drop_table('invoices')
    op.drop_table('customers') 