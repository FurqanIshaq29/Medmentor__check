from fastapi import APIRouter, Depends
from models.db_models import Student
from models.schemas import StartSessionRequest, StartSessionResponse
from routers.auth import get_current_student
from services.patient_loader import list_all_cases, load_patient
from services.session_manager import create_session
from database.db import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/cases", tags=["cases"])

@router.get("/list")
async def get_cases(student: Student = Depends(get_current_student)):
    return list_all_cases()

@router.post("/start", response_model=StartSessionResponse)
async def start_case(
    req: StartSessionRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    load_patient(req.case_id)  # validates case exists — raises 404 if not
    session = create_session(db, student.id, req.case_id)
    return StartSessionResponse(session_id=session.id, case_id=req.case_id)