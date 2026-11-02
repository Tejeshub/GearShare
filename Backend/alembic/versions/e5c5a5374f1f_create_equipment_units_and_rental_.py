"""create equipment units and rental allocations

Revision ID: e5c5a5374f1f
Revises: b4c60415402c
Create Date: 2026-11-02 20:01:30.191631

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5c5a5374f1f'
down_revision: Union[str, Sequence[str], None] = 'b4c60415402c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Enable btree_gist extension on PostgreSQL if not already present
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

    op.create_table(
        'equipment_units',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('equipment_id', sa.Uuid(), nullable=False),
        sa.Column('asset_code', sa.String(length=50), nullable=False),
        sa.Column('serial_number', sa.String(length=100), nullable=True),
        sa.Column('condition', sa.Enum('EXCELLENT', 'GOOD', 'FAIR', 'DAMAGED', name='unitcondition', native_enum=False, length=50), nullable=False),
        sa.Column('operational_status', sa.Enum('ACTIVE', 'MAINTENANCE', 'RETIRED', name='unitoperationalstatus', native_enum=False, length=50), nullable=False),
        sa.Column('purchase_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_equipment_units_asset_code'), 'equipment_units', ['asset_code'], unique=True)
    op.create_index(op.f('ix_equipment_units_equipment_id'), 'equipment_units', ['equipment_id'], unique=False)
    op.create_index('ix_equipment_units_equipment_status', 'equipment_units', ['equipment_id', 'operational_status'], unique=False)
    op.create_index(op.f('ix_equipment_units_operational_status'), 'equipment_units', ['operational_status'], unique=False)
    op.create_index(op.f('ix_equipment_units_serial_number'), 'equipment_units', ['serial_number'], unique=True)

    op.create_table(
        'rental_allocations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('unit_id', sa.Uuid(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', sa.Enum('RESERVED', 'CONFIRMED', 'CANCELLED', 'COMPLETED', name='allocationstatus', native_enum=False, length=50), nullable=False),
        sa.Column('enquiry_reference', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['unit_id'], ['equipment_units.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rental_allocations_dates_status', 'rental_allocations', ['unit_id', 'start_date', 'end_date', 'status'], unique=False)
    op.create_index(op.f('ix_rental_allocations_end_date'), 'rental_allocations', ['end_date'], unique=False)
    op.create_index(op.f('ix_rental_allocations_enquiry_reference'), 'rental_allocations', ['enquiry_reference'], unique=False)
    op.create_index(op.f('ix_rental_allocations_start_date'), 'rental_allocations', ['start_date'], unique=False)
    op.create_index(op.f('ix_rental_allocations_status'), 'rental_allocations', ['status'], unique=False)
    op.create_index(op.f('ix_rental_allocations_unit_id'), 'rental_allocations', ['unit_id'], unique=False)

    # 2. Add PostgreSQL Exclusion Constraint to prevent double-booking active allocations
    # Uses daterange(start_date, end_date, '[]') for inclusive dates
    if bind.dialect.name == "postgresql":
        op.execute("""
            ALTER TABLE rental_allocations
            ADD CONSTRAINT no_overlapping_active_allocations
            EXCLUDE USING gist (
                unit_id WITH =,
                daterange(start_date, end_date, '[]') WITH &&
            )
            WHERE (status IN ('RESERVED', 'CONFIRMED'));
        """)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE rental_allocations DROP CONSTRAINT IF EXISTS no_overlapping_active_allocations;")

    op.drop_index(op.f('ix_rental_allocations_unit_id'), table_name='rental_allocations')
    op.drop_index(op.f('ix_rental_allocations_status'), table_name='rental_allocations')
    op.drop_index(op.f('ix_rental_allocations_start_date'), table_name='rental_allocations')
    op.drop_index(op.f('ix_rental_allocations_enquiry_reference'), table_name='rental_allocations')
    op.drop_index(op.f('ix_rental_allocations_end_date'), table_name='rental_allocations')
    op.drop_index('ix_rental_allocations_dates_status', table_name='rental_allocations')
    op.drop_table('rental_allocations')
    op.drop_index(op.f('ix_equipment_units_serial_number'), table_name='equipment_units')
    op.drop_index(op.f('ix_equipment_units_operational_status'), table_name='equipment_units')
    op.drop_index('ix_equipment_units_equipment_status', table_name='equipment_units')
    op.drop_index(op.f('ix_equipment_units_equipment_id'), table_name='equipment_units')
    op.drop_index(op.f('ix_equipment_units_asset_code'), table_name='equipment_units')
    op.drop_table('equipment_units')
