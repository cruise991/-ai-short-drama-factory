import os
import sys
import pytest
import json
from datetime import datetime
from sqlmodel import Session, SQLModel, create_engine, select

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(BASE_DIR, "server")
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from models.database import (
    Tenant,
    User,
    UserRole,
    Avatar,
    AvatarStatus,
    SceneVideo,
    Product,
    KnowledgeBase,
    KnowledgeDocument,
    LiveSession,
    LiveSessionStatus,
    LiveMessage,
    LiveProduct,
    LiveScript,
    AnalyticsEvent,
    Project,
    Asset,
    Feedback
)

@pytest.fixture(name="db_session")
def fixture_db_session():
    # In-memory SQLite for high-speed isolated test execution
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_tenant_and_user_creation(db_session: Session):
    tenant = Tenant(name="星云短剧科技有限公司", code="corp_xingyun")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    assert tenant.id is not None
    assert tenant.code == "corp_xingyun"
    assert tenant.is_active is True

    user = User(
        username="anchor_01",
        hashed_password="hashed_pw_dummy",
        role=UserRole.OPERATOR.value,
        tenant_id=tenant.code
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    assert user.id is not None
    assert user.tenant_id == "corp_xingyun"

def test_avatar_and_scene_video(db_session: Session):
    avatar = Avatar(
        tenant_id="corp_xingyun",
        name="AI主播小婉",
        avatar_type="lingcast_live",
        voice_id="zh-CN-XiaoxiaoNeural",
        config_json=json.dumps({"pitch": "+2Hz", "speed": 1.05}),
        status=AvatarStatus.ACTIVE.value
    )
    db_session.add(avatar)
    
    scene = SceneVideo(
        tenant_id="corp_xingyun",
        title="温馨科技感带货直播间背景",
        video_url="https://cdn.example.com/videos/bg_studio_01.mp4",
        duration=60.0,
        resolution="1080x1920",
        is_loop=True
    )
    db_session.add(scene)
    db_session.commit()
    db_session.refresh(avatar)
    db_session.refresh(scene)

    assert avatar.id is not None
    assert avatar.name == "AI主播小婉"
    cfg = json.loads(avatar.config_json)
    assert cfg["pitch"] == "+2Hz"

    assert scene.id is not None
    assert scene.is_loop is True

def test_product_and_knowledge_base(db_session: Session):
    product = Product(
        tenant_id="corp_xingyun",
        title="超感重低音降噪耳机",
        price=299.0,
        original_price=599.0,
        sku="SKU-HEADPHONE-001",
        selling_points_json=json.dumps(["主动降噪40dB", "超长续航35小时", "极速快充"]),
        stock=500
    )
    db_session.add(product)

    kb = KnowledgeBase(
        tenant_id="corp_xingyun",
        name="耳机数码商品带货知识库",
        chunk_size=256,
        chunk_overlap=32
    )
    db_session.add(kb)
    db_session.commit()
    db_session.refresh(product)
    db_session.refresh(kb)

    doc = KnowledgeDocument(
        kb_id=kb.id,
        tenant_id="corp_xingyun",
        doc_id="doc_headphone_qa",
        title="常见问答FAQ",
        content="问：支持退换货吗？答：支持7天无理由退货，保修期1年。"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    assert product.id is not None
    assert doc.id is not None
    assert doc.kb_id == kb.id

def test_live_session_lifecycle_and_interactions(db_session: Session):
    # 1. Create room
    session = LiveSession(
        tenant_id="corp_xingyun",
        title="双十一超级好物狂欢夜",
        room_id="room_1001",
        stream_key="live_key_abcdef123456",
        rtmp_url="rtmp://localhost:1935/live/room_1001",
        http_flv_url="http://localhost:8085/live/room_1001.flv",
        status=LiveSessionStatus.STREAMING.value,
        started_at=datetime.utcnow()
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    assert session.id is not None

    # 2. Add product link
    prod = Product(tenant_id="corp_xingyun", title="保温杯", price=59.0)
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    live_prod = LiveProduct(
        session_id=session.id,
        product_id=prod.id,
        sort_order=1,
        is_current=True,
        flash_price=39.9
    )
    db_session.add(live_prod)

    # 3. Add script
    script = LiveScript(
        session_id=session.id,
        tenant_id="corp_xingyun",
        script_type="product_pitch",
        content="这款保温杯24小时强效保温，大家扣1上车！",
        order_num=1
    )
    db_session.add(script)

    # 4. Add Danmaku message
    msg = LiveMessage(
        session_id=session.id,
        tenant_id="corp_xingyun",
        user_name="小美粉",
        content="还有现货吗？能发顺丰吗？",
        message_type="danmaku"
    )
    db_session.add(msg)

    # 5. Add Analytics Event
    event = AnalyticsEvent(
        session_id=session.id,
        tenant_id="corp_xingyun",
        event_type="click_product",
        payload_json=json.dumps({"product_id": prod.id, "position": "top_banner"})
    )
    db_session.add(event)

    db_session.commit()
    db_session.refresh(live_prod)
    db_session.refresh(script)
    db_session.refresh(msg)
    db_session.refresh(event)

    assert live_prod.id is not None
    assert live_prod.session_id == session.id
    assert live_prod.is_current is True

    assert script.id is not None
    assert msg.is_processed is False

    # Mark danmaku processed
    msg.is_processed = True
    msg.reply_text = "支持顺丰包邮，拍下立即发货！"
    db_session.add(msg)
    db_session.commit()
    db_session.refresh(msg)
    assert msg.is_processed is True
    assert "顺丰包邮" in msg.reply_text

    assert event.id is not None
    assert event.event_type == "click_product"
