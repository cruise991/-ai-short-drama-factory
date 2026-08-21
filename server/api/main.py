from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.database import create_db_and_tables
from fastapi.staticfiles import StaticFiles
import os
import asyncio

app = FastAPI(title="AI Short Drama & Dance API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists("/workspace/out"):
    BASE_DIR = "/workspace"
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT_DIR = os.path.join(BASE_DIR, "out")
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)

from api.routes import config, projects, ws, dance
app.include_router(config.router)
app.include_router(projects.router)
app.include_router(ws.router)
app.include_router(dance.router)

app.mount("/media/out", StaticFiles(directory=OUT_DIR), name="media_out")
app.mount("/media/projects", StaticFiles(directory=PROJECTS_DIR), name="media_projects")

from worker.task_runner import worker_loop

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    print("Database initialized.")
    asyncio.create_task(worker_loop())

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Backend is running"}
