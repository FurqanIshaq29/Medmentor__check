import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.mongo import init_mongo

from routers import auth, cases, chat, evaluate

load_dotenv()

app = FastAPI(
    title="MedMentor API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://med-mentor-orcin.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_mongo()          # replaces init_db()

# Routers
app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(chat.router)
app.include_router(evaluate.router)

# Health check
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "1.0.0"
    }

# Root route
@app.get("/")
async def root():
    return {
        "message": "MedMentor Backend Running Successfully"
    }


