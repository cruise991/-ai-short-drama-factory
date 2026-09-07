from sqlmodel import Field, SQLModel, create_engine, Session
from typing import Optional
from datetime import datetime
import os

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
    
class Asset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    asset_type: str # 'image', 'video'
    shot_id: str
    s3_url: str
    
class Feedback(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    feedback_text: str
    target_phase: str # e.g., 'Draft_Completed'
    created_at: datetime = Field(default_factory=datetime.utcnow)

data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(data_dir, exist_ok=True)
sqlite_file_name = os.path.join(data_dir, "app.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    # Only create tables if they do not exist; NEVER drop existing production/dev data
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

if __name__ == "__main__":
    create_db_and_tables()
    print("Database tables created successfully!")
