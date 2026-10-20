"""002_live_platform_schema

Revision ID: 7a8e9f123456
Revises: 64c17cfbd6b2
Create Date: 2026-09-11 18:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '7a8e9f123456'
down_revision: Union[str, None] = '64c17cfbd6b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Tenant
    op.create_table(
        'tenant',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('code', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_tenant_name', 'tenant', ['name'])
    op.create_index('ix_tenant_code', 'tenant', ['code'], unique=True)

    # 2. Avatar
    op.create_table(
        'avatar',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='default'),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('avatar_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='2d_nerf'),
        sa.Column('preview_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('model_path', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('voice_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='zh-CN-XiaoxiaoNeural'),
        sa.Column('config_json', sqlmodel.sql.sqltypes.AutoString(), nullable=True, server_default='{}'),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_avatar_tenant_id', 'avatar', ['tenant_id'])
    op.create_index('ix_avatar_name', 'avatar', ['name'])

    # 3. SceneVideo
    op.create_table(
        'scenevideo',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='default'),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('video_url', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('duration', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('resolution', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='1080x1920'),
        sa.Column('is_loop', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='ready'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_scenevideo_tenant_id', 'scenevideo', ['tenant_id'])
    op.create_index('ix_scenevideo_title', 'scenevideo', ['title'])

    # 4. Product
    op.create_table(
        'product',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='default'),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('original_price', sa.Float(), nullable=True),
        sa.Column('sku', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('cover_image', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('selling_points_json', sqlmodel.sql.sqltypes.AutoString(), nullable=True, server_default='[]'),
        sa.Column('stock', sa.Integer(), nullable=False, server_default='999'),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_product_tenant_id', 'product', ['tenant_id'])
    op.create_index('ix_product_title', 'product', ['title'])
    op.create_index('ix_product_sku', 'product', ['sku'])

    # 5. KnowledgeBase
    op.create_table(
        'knowledgebase',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='default'),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('chunk_size', sa.Integer(), nullable=False, server_default='512'),
        sa.Column('chunk_overlap', sa.Integer(), nullable=False, server_default='64'),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_knowledgebase_tenant_id', 'knowledgebase', ['tenant_id'])
    op.create_index('ix_knowledgebase_name', 'knowledgebase', ['name'])

    # 6. KnowledgeDocument
    op.create_table(
        'knowledgedocument',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('kb_id', sa.Integer(), sa.ForeignKey('knowledgebase.id'), nullable=False),
        sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='default'),
        sa.Column('doc_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('metadata_json', sqlmodel.sql.sqltypes.AutoString(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_knowledgedocument_kb_id', 'knowledgedocument', ['kb_id'])
    op.create_index('ix_knowledgedocument_tenant_id', 'knowledgedocument', ['tenant_id'])
    op.create_index('ix_knowledgedocument_doc_id', 'knowledgedocument', ['doc_id'])

    # 7. LiveSession
    op.create_table(
        'livesession',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='default'),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('room_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('avatar_id', sa.Integer(), sa.ForeignKey('avatar.id'), nullable=True),
        sa.Column('scene_video_id', sa.Integer(), sa.ForeignKey('scenevideo.id'), nullable=True),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='idle'),
        sa.Column('stream_key', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('rtmp_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('http_flv_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('hls_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('viewer_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('peak_viewers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_livesession_tenant_id', 'livesession', ['tenant_id'])
    op.create_index('ix_livesession_title', 'livesession', ['title'])
    op.create_index('ix_livesession_room_id', 'livesession', ['room_id'], unique=True)
    op.create_index('ix_livesession_status', 'livesession', ['status'])
    op.create_index('ix_livesession_stream_key', 'livesession', ['stream_key'], unique=True)

    # 8. LiveMessage
    op.create_table(
        'livemessage',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('livesession.id'), nullable=False),
        sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='default'),
        sa.Column('user_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('user_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='观众'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='danmaku'),
        sa.Column('is_processed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('reply_text', sa.Text(), nullable=True),
        sa.Column('reply_audio_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_livemessage_session_id', 'livemessage', ['session_id'])
    op.create_index('ix_livemessage_tenant_id', 'livemessage', ['tenant_id'])
    op.create_index('ix_livemessage_is_processed', 'livemessage', ['is_processed'])

    # 9. LiveProduct
    op.create_table(
        'liveproduct',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('livesession.id'), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('product.id'), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('flash_price', sa.Float(), nullable=True),
        sa.Column('stock_limit', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_liveproduct_session_id', 'liveproduct', ['session_id'])
    op.create_index('ix_liveproduct_product_id', 'liveproduct', ['product_id'])

    # 10. LiveScript
    op.create_table(
        'livescript',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('livesession.id'), nullable=False),
        sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='default'),
        sa.Column('script_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='product_pitch'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('audio_cache_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('trigger_keywords_json', sqlmodel.sql.sqltypes.AutoString(), nullable=True, server_default='[]'),
        sa.Column('order_num', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_livescript_session_id', 'livescript', ['session_id'])
    op.create_index('ix_livescript_tenant_id', 'livescript', ['tenant_id'])

    # 11. AnalyticsEvent
    op.create_table(
        'analyticsevent',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('livesession.id'), nullable=False),
        sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='default'),
        sa.Column('event_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('payload_json', sqlmodel.sql.sqltypes.AutoString(), nullable=True, server_default='{}'),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_analyticsevent_session_id', 'analyticsevent', ['session_id'])
    op.create_index('ix_analyticsevent_tenant_id', 'analyticsevent', ['tenant_id'])
    op.create_index('ix_analyticsevent_event_type', 'analyticsevent', ['event_type'])
    op.create_index('ix_analyticsevent_timestamp', 'analyticsevent', ['timestamp'])

def downgrade() -> None:
    op.drop_table('analyticsevent')
    op.drop_table('livescript')
    op.drop_table('liveproduct')
    op.drop_table('livemessage')
    op.drop_table('livesession')
    op.drop_table('knowledgedocument')
    op.drop_table('knowledgebase')
    op.drop_table('product')
    op.drop_table('scenevideo')
    op.drop_table('avatar')
    op.drop_table('tenant')
