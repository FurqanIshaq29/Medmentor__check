from pydantic import BaseModel
from typing import Optional

class GoogleAuthRequest(BaseModel):
    token: str  # Google ID token from frontend

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student_name: str
    student_email: str

class StartSessionRequest(BaseModel):
    case_id: str

class StartSessionResponse(BaseModel):
    session_id: str
    case_id: str

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str

class ChatMessageResponse(BaseModel):
    reply: str
    session_id: str
    turn_number: int

class DiagnosisSubmission(BaseModel):
    session_id: str
    suspected_disease: str
    reasoning: str
    treatment: str

class EvaluationResponse(BaseModel):
    report_id: str
    total_score: int
    evaluation: dict

class CaseSummary(BaseModel):
    case_id: str
    age: int
    gender: str
    disease_category: str  # vague hint, not the diagnosis
    difficulty: str