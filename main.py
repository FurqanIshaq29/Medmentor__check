import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import init_db

# Import all models so SQLAlchemy registers them before init_db
import models.db_models  # noqa: F401

from routers import auth, cases, chat, evaluate

load_dotenv()

app = FastAPI(title="MedMentor API", version="1.0.0")

# CORS — allows your React frontend to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",          # local Vite dev server
        "https://your-app.vercel.app",    # replace with your real Vercel URL later
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(chat.router)
app.include_router(evaluate.router)

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/")
def root():
    return {"message": "MedMentor Backend Running Successfully"}
