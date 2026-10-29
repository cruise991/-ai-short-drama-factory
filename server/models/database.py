from enum import Enum
from sqlmodel import Field, SQLModel, create_engine, Session, select
from typing import Optional
from datetime import datetime
import os

class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: Optional[str] = Field(default=None, index=True)
    hashed_password: str
    role: str = Field(default=UserRole.OPERATOR.value)
    tenant_id: str = Field(default="default", index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(SQLModel):
    username: str
    password: str
    email: Optional[str] = None
    role: Optional[str] = UserRole.OPERATOR.value
    tenant_id: Optional[str] = "default"

class UserRead(SQLModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str
    tenant_id: str = "default"
    is_active: bool
    created_at: datetime

class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str

class TokenData(SQLModel):
    username: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[str] = None

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_slug: str = Field(index=True)
    status: str = Field(default="Pending") # Pending, Draft_Completed, QA_Pending_Production, Completed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    goal: str
    format_type: str
    branch_type: str = Field(default="short_drama") # 'short_drama' or 'dance_video'
    selected_ip: Optional[str] = Field(default=None)
    vibe: Optional[str] = Field(default=None)
    trend_enabled: bool = Field(default=False)
    costume_id: Optional[str] = Field(default=None)
    scene_id: Optional[str] = Field(default=None)
    motion_id: Optional[str] = Field(default=None)
    hand_preset: Optional[str] = Field(default=None)
    caption_style: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    tenant_id: str = Field(default="default", index=True)
    
class Asset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    asset_type: str # 'image', 'video'
    shot_id: str
    s3_url: str
    tenant_id: str = Field(default="default", index=True)
    
class Feedback(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    feedback_text: str
    target_phase: str # e.g., 'Draft_Completed'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: str = Field(default="default", index=True)

# ----------------- Phase 1: Live Streaming & Digital Avatar Platform Models -----------------

class Tenant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    code: str = Field(unique=True, index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AvatarStatus(str, Enum):
    ACTIVE = "active"
    TRAINING = "training"
    ARCHIVED = "archived"

class Avatar(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(default="default", index=True)
    name: str = Field(index=True)
    avatar_type: str = Field(default="2d_nerf") # '2d_nerf', 'wav2lip', 'lingcast_live'
    preview_url: Optional[str] = None
    model_path: Optional[str] = None
    voice_id: str = Field(default="zh-CN-XiaoxiaoNeural")
    config_json: Optional[str] = Field(default="{}")
    status: str = Field(default=AvatarStatus.ACTIVE.value)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SceneVideo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(default="default", index=True)
    title: str = Field(index=True)
    video_url: str
    duration: float = Field(default=0.0)
    resolution: str = Field(default="1080x1920")
    is_loop: bool = Field(default=True)
    status: str = Field(default="ready")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(default="default", index=True)
    title: str = Field(index=True)
    description: Optional[str] = None
    price: float = Field(default=0.0)
    original_price: Optional[float] = None
    sku: Optional[str] = Field(default=None, index=True)
    cover_image: Optional[str] = None
    selling_points_json: Optional[str] = Field(default="[]") # JSON list of highlight points
    stock: int = Field(default=999)
    status: str = Field(default="active")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class KnowledgeBase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(default="default", index=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=64)
    status: str = Field(default="active")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class KnowledgeDocument(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kb_id: int = Field(foreign_key="knowledgebase.id", index=True)
    tenant_id: str = Field(default="default", index=True)
    doc_id: str = Field(index=True)
    title: Optional[str] = None
    content: str
    chunk_count: int = Field(default=1)
    metadata_json: Optional[str] = Field(default="{}")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LiveSessionStatus(str, Enum):
    IDLE = "idle"
    STREAMING = "streaming"
    PAUSED = "paused"
    FINISHED = "finished"

class LiveSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(default="default", index=True)
    title: str = Field(index=True)
    room_id: str = Field(index=True)
    avatar_id: Optional[int] = Field(default=None, foreign_key="avatar.id")
    scene_video_id: Optional[int] = Field(default=None, foreign_key="scenevideo.id")
    status: str = Field(default=LiveSessionStatus.IDLE.value, index=True)
    stream_key: str = Field(unique=True, index=True)
    rtmp_url: Optional[str] = None
    http_flv_url: Optional[str] = None
    hls_url: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    viewer_count: int = Field(default=0)
    peak_viewers: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LiveMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="livesession.id", index=True)
    tenant_id: str = Field(default="default", index=True)
    user_id: Optional[str] = Field(default=None, index=True)
    user_name: str = Field(default="观众")
    content: str
    message_type: str = Field(default="danmaku") # 'danmaku', 'gift', 'system', 'agent_reply'
    is_processed: bool = Field(default=False, index=True)
    reply_text: Optional[str] = None
    reply_audio_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LiveProduct(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="livesession.id", index=True)
    product_id: int = Field(foreign_key="product.id", index=True)
    sort_order: int = Field(default=0)
    is_current: bool = Field(default=False)
    flash_price: Optional[float] = None
    stock_limit: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LiveScript(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="livesession.id", index=True)
    tenant_id: str = Field(default="default", index=True)
    script_type: str = Field(default="product_pitch") # 'intro', 'product_pitch', 'faq', 'closing'
    content: str
    audio_cache_url: Optional[str] = None
    trigger_keywords_json: Optional[str] = Field(default="[]")
    order_num: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AnalyticsEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="livesession.id", index=True)
    tenant_id: str = Field(default="default", index=True)
    event_type: str = Field(index=True) # 'view', 'danmaku', 'click_product', 'buy', 'latency'
    payload_json: Optional[str] = Field(default="{}")
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(data_dir, exist_ok=True)
    sqlite_file_name = os.path.join(data_dir, "app.db")
    DATABASE_URL = f"sqlite:///{sqlite_file_name}"

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20, pool_pre_ping=True)

from sqlalchemy import text

def create_db_and_tables():
    # Only create tables if they do not exist; NEVER drop existing production/dev data
    SQLModel.metadata.create_all(engine)
    # Safe SQLite column upgrade for pre-existing tables
    if DATABASE_URL.startswith("sqlite"):
        with engine.begin() as conn:
            for tbl in ["project", "asset", "feedback", "user"]:
                try:
                    conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN tenant_id VARCHAR DEFAULT 'default'"))
                except Exception:
                    pass  # Column already exists
            for col in ["costume_id", "scene_id", "motion_id", "hand_preset", "caption_style", "error_message"]:
                try:
                    conn.execute(text(f"ALTER TABLE project ADD COLUMN {col} VARCHAR"))
                except Exception:
                    pass

    # Ensure default admin user (admin / admin123) is auto-seeded
    try:
        from core.security import get_password_hash
        with Session(engine) as session:
            admin_user = session.exec(select(User).where(User.username == "admin")).first()
            if not admin_user:
                admin_user = User(
                    username="admin",
                    email="admin@lingcast.ai",
                    hashed_password=get_password_hash("admin123"),
                    role="admin",
                    tenant_id="default",
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(admin_user)
                session.commit()
                print("[Lifespan] 👤 Default admin user seeded successfully (admin / admin123).")
            else:
                # Always ensure admin user is active and has correct password in dev/demo
                if not admin_user.is_active:
                    admin_user.is_active = True
                    session.add(admin_user)
                    session.commit()
    except Exception as e:
        print(f"[Lifespan] ⚠️ Admin user check notice: {e}")


def get_session():
    with Session(engine) as session:
        yield session

if __name__ == "__main__":
    create_db_and_tables()
    print("Database tables created successfully!")
