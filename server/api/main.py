from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.database import create_db_and_tables

app = FastAPI(title="AI Short Drama API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes import config, projects, ws
from fastapi.staticfiles import StaticFiles
import os

app.include_router(config.router)
app.include_router(projects.router)
app.include_router(ws.router)

# Ensure dirs exist to avoid startup crash
os.makedirs("/workspace/out", exist_ok=True)
os.makedirs("/workspace/projects", exist_ok=True)

app.mount("/media/out", StaticFiles(directory="/workspace/out"), name="media_out")
app.mount("/media/projects", StaticFiles(directory="/workspace/projects"), name="media_projects")

import asyncio
from worker.task_runner import worker_loop

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    print("Database initialized.")
    # Start the SQLite queue polling loop
    asyncio.create_task(worker_loop())

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Backend is running"}
