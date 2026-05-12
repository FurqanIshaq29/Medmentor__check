from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

# ── ObjectId serialisation helper ───────────────────────────────────
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

# ── Students collection ──────────────────────────────────────────────
class StudentDoc(BaseModel):
    """Stored in 'students' collection"""
    google_sub: str          # unique index
    email: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ── Sessions collection ──────────────────────────────────────────────
class SessionDoc(BaseModel):
    """Stored in 'sessions' collection"""
    student_id: str          # students._id as string
    case_id: str             # e.g. "DIA_001"
    status: str = "active"  # active | completed
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

# ── Chat turns — embedded in session document ────────────────────────
class ChatTurn(BaseModel):
    """Embedded array inside sessions document"""
    turn_number: int
    student_message: str
    patient_response: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ── Evaluations collection ───────────────────────────────────────────
class EvaluationDoc(BaseModel):
    """Stored in 'evaluations' collection"""
    student_id: str
    session_id: str
    case_id: str
    submitted_disease: str
    submitted_reasoning: str
    submitted_treatment: str
    evaluation: dict         # full JSON from Workflow B — stored natively
    total_score: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ── Progress — embedded in student document or separate collection ────
class ProgressEntry(BaseModel):
    case_id: str
    attempts: int = 0
    best_score: int = 0
    last_attempt: Optional[datetime] = None