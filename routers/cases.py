from fastapi import APIRouter, Depends, HTTPException
from database.mongo import get_database
from services.patient_loader import list_all_cases, load_patient
from routers.auth import get_current_student
from datetime import datetime
import uuid

router = APIRouter(prefix="/cases", tags=["cases"])

@router.get("/list")
async def get_cases(student: dict = Depends(get_current_student)):
    return list_all_cases()

@router.post("/start")
async def start_case(req: dict, student: dict = Depends(get_current_student)):
    case_id = req.get("case_id")
    load_patient(case_id)  # validates existence

    db = await get_database()
    session_doc = {
        "student_id": student["id"],
        "case_id": case_id,
        "status": "active",
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "turns": [],            # embedded chat turns array
        "turn_count": 0
    }
    result = await db.sessions.insert_one(session_doc)
    session_id = str(result.inserted_id)

    return {"session_id": session_id, "case_id": case_id}