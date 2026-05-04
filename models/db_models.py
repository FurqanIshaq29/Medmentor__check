import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from database.db import Base

def new_uuid():
    return str(uuid.uuid4())

class Student(Base):
    __tablename__ = "students"
    id = Column(String, primary_key=True, default=new_uuid)
    google_sub = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, nullable=False)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=new_uuid)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    case_id = Column(String, nullable=False)
    status = Column(String, default="active")  # active | completed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class ChatTurn(Base):
    __tablename__ = "chat_turns"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    student_message = Column(Text, nullable=False)
    patient_response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"
    id = Column(String, primary_key=True, default=new_uuid)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    case_id = Column(String, nullable=False)
    submitted_disease = Column(Text)
    submitted_reasoning = Column(Text)
    submitted_treatment = Column(Text)
    evaluation_json = Column(Text, nullable=False)  # full JSON stored as string
    total_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class StudentProgress(Base):
    __tablename__ = "student_progress"
    student_id = Column(String, ForeignKey("students.id"), primary_key=True)
    case_id = Column(String, primary_key=True)
    attempts = Column(Integer, default=0)
    best_score = Column(Integer, default=0)
    last_attempt = Column(DateTime, nullable=True)