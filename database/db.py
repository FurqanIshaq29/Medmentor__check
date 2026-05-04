import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database/medmentor.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # required for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Creates all tables if they don't exist
    Base.metadata.create_all(bind=engine)
    print("Database initialized at:", DATABASE_URL)

# SQLite connection + table creation
# db.py creates these on startup
"""
CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,          -- Google sub (unique user ID)
    email TEXT NOT NULL,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,          -- UUID
    student_id TEXT NOT NULL,
    case_id TEXT NOT NULL,        -- e.g. "DIA_001"
    status TEXT DEFAULT 'active', -- active | completed | abandoned
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id)
);

CREATE TABLE IF NOT EXISTS chat_turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,   
    turn_number INTEGER NOT NULL,
    student_message TEXT NOT NULL,
    patient_response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS evaluation_reports (
    id TEXT PRIMARY KEY,          -- UUID
    student_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    submitted_disease TEXT,
    submitted_reasoning TEXT,
    submitted_treatment TEXT,
    evaluation_json TEXT NOT NULL, -- full JSON blob
    total_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS student_progress (
    student_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    attempts INTEGER DEFAULT 0,
    best_score INTEGER DEFAULT 0,
    last_attempt TIMESTAMP,
    PRIMARY KEY (student_id, case_id)
);"""