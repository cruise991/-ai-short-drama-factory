"""001_initial_schema

Revision ID: 64c17cfbd6b2
Revises: 
Create Date: 2026-09-11 16:59:22.356939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '64c17cfbd6b2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Project table
    op.create_table(
        'project',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_slug', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='Pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('goal', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('format_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('branch_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='short_drama'),
        sa.Column('selected_ip', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('vibe', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('trend_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='default'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_project_slug'), 'project', ['project_slug'], unique=False)
    op.create_index(op.f('ix_project_tenant_id'), 'project', ['tenant_id'], unique=False)

    # 2. Asset table
    op.create_table(
        'asset',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('asset_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('shot_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('s3_url', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='default'),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_asset_tenant_id'), 'asset', ['tenant_id'], unique=False)

    # 3. Feedback table
    op.create_table(
        'feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('feedback_text', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('target_phase', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='default'),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_tenant_id'), 'feedback', ['tenant_id'], unique=False)

    # 4. User table
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('role', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='operator'),
        sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='default'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=False)
    op.create_index(op.f('ix_user_tenant_id'), 'user', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_tenant_id'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_feedback_tenant_id'), table_name='feedback')
    op.drop_table('feedback')
    op.drop_index(op.f('ix_asset_tenant_id'), table_name='asset')
    op.drop_table('asset')
    op.drop_index(op.f('ix_project_tenant_id'), table_name='project')
    op.drop_index(op.f('ix_project_project_slug'), table_name='project')
    op.drop_table('project')
