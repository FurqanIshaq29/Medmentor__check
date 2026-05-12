from fastapi import APIRouter, Depends, HTTPException
from database.mongo import get_database
from routers.auth import get_current_student
from services.patient_loader import load_patient
from services.workflow_b import evaluate_submission
from models.schemas import DiagnosisSubmission, EvaluationResponse
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/evaluate", tags=["evaluate"])

@router.post("/submit", response_model=EvaluationResponse)
async def submit_diagnosis(
    req: DiagnosisSubmission,
    student: dict = Depends(get_current_student)
):
    db = await get_database()
    session = await db.sessions.find_one({
        "_id": ObjectId(req.session_id),
        "student_id": student["id"]
    })

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] == "completed":
        raise HTTPException(status_code=400, detail="Already submitted")

    turns = session.get("turns", [])
    if len(turns) < 3:
        raise HTTPException(status_code=400, detail="Ask at least 3 questions first")

    patient    = load_patient(session["case_id"])
    evaluation = await evaluate_submission(patient, turns, req.dict())
    total      = evaluation.get("total_score", 0)

    # Insert evaluation document
    eval_doc = {
        "student_id":           student["id"],
        "session_id":           req.session_id,
        "case_id":              session["case_id"],
        "submitted_disease":    req.suspected_disease,
        "submitted_reasoning":  req.reasoning,
        "submitted_treatment":  req.treatment,
        "evaluation":           evaluation,     # stored as native BSON document
        "total_score":          total,
        "created_at":           datetime.utcnow()
    }
    result = await db.evaluations.insert_one(eval_doc)
    report_id = str(result.inserted_id)

    # Mark session completed
    await db.sessions.update_one(
        {"_id": ObjectId(req.session_id)},
        {"$set": {"status": "completed", "completed_at": datetime.utcnow()}}
    )

    # Update progress — upsert into student's progress array
    await db.students.update_one(
        {"_id": ObjectId(student["id"]), "progress.case_id": session["case_id"]},
        {"$inc": {"progress.$.attempts": 1},
         "$max": {"progress.$.best_score": total},
         "$set": {"progress.$.last_attempt": datetime.utcnow()}}
    )
    # If case not yet in progress array, add it
    await db.students.update_one(
        {"_id": ObjectId(student["id"]),
         "progress.case_id": {"$ne": session["case_id"]}},
        {"$push": {"progress": {
            "case_id": session["case_id"],
            "attempts": 1,
            "best_score": total,
            "last_attempt": datetime.utcnow()
        }}}
    )

    return EvaluationResponse(
        report_id=report_id,
        total_score=total,
        evaluation=evaluation
    )

@router.get("/report/{report_id}")
async def get_report(
    report_id: str,
    student: dict = Depends(get_current_student)
):
    db = await get_database()
    report = await db.evaluations.find_one({
        "_id": ObjectId(report_id),
        "student_id": student["id"]
    })
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "report_id":   str(report["_id"]),
        "case_id":     report["case_id"],
        "total_score": report["total_score"],
        "created_at":  report["created_at"].isoformat(),
        "evaluation":  report["evaluation"]
    }