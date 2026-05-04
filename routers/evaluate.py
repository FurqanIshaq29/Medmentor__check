import uuid, json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from models.db_models import Student, EvaluationReport, StudentProgress
from models.schemas import DiagnosisSubmission, EvaluationResponse
from routers.auth import get_current_student
from services.session_manager import get_session, complete_session
from services.patient_loader import load_patient
from services.chat_history import get_turns
from services.workflow_b import evaluate_submission
from datetime import datetime

router = APIRouter(prefix="/evaluate", tags=["evaluate"])

@router.post("/submit", response_model=EvaluationResponse)
async def submit_diagnosis(
    req: DiagnosisSubmission,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    session = get_session(db, req.session_id)
    if not session or session.student_id != student.id:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Already submitted")

    turns = get_turns(db, req.session_id)
    if len(turns) < 3:
        raise HTTPException(
            status_code=400,
            detail="You must ask at least 3 questions before submitting"
        )

    patient = load_patient(session.case_id)
    evaluation = await evaluate_submission(patient, turns, req.dict())

    report = EvaluationReport(
        id=str(uuid.uuid4()),
        student_id=student.id,
        session_id=req.session_id,
        case_id=session.case_id,
        submitted_disease=req.suspected_disease,
        submitted_reasoning=req.reasoning,
        submitted_treatment=req.treatment,
        evaluation_json=json.dumps(evaluation),
        total_score=evaluation.get("total_score", 0)
    )
    db.add(report)

    # Update student progress
    progress = db.query(StudentProgress).filter(
        StudentProgress.student_id == student.id,
        StudentProgress.case_id == session.case_id
    ).first()

    if progress:
        progress.attempts += 1
        progress.best_score = max(progress.best_score, report.total_score)
        progress.last_attempt = datetime.utcnow()
    else:
        db.add(StudentProgress(
            student_id=student.id,
            case_id=session.case_id,
            attempts=1,
            best_score=report.total_score,
            last_attempt=datetime.utcnow()
        ))

    complete_session(db, req.session_id)
    db.commit()

    return EvaluationResponse(
        report_id=report.id,
        total_score=report.total_score,
        evaluation=evaluation
    )

@router.get("/report/{report_id}")
async def get_report(
    report_id: str,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    report = db.query(EvaluationReport).filter(
        EvaluationReport.id == report_id,
        EvaluationReport.student_id == student.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "report_id": report.id,
        "case_id": report.case_id,
        "total_score": report.total_score,
        "created_at": report.created_at,
        "evaluation": json.loads(report.evaluation_json)
    }


"""# /evaluate/submit (Workflow B)
# routers/evaluate.py

@router.post("/evaluate/submit")
async def submit_diagnosis(req: DiagnosisSubmission, user=Depends(get_current_user)):
    session = session_manager.get(req.session_id)
    patient = patient_loader.load(session.case_id)
    transcript = chat_history.get_turns(session.id)

    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=EVALUATOR_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": build_evaluator_user_message(
                patient, transcript, req.dict()
            )
        }]
    )

    raw = response.content[0].text
    evaluation = json.loads(
        raw.strip().removeprefix("```json").removesuffix("```")
    )

    # Store the report
    report_id = evaluation_store.save(
        student_id=user.id,
        session_id=req.session_id,
        case_id=session.case_id,
        submission=req.dict(),
        evaluation=evaluation,
        total_score=evaluation["overall_score"]["total"]
    )

    # Mark session as completed
    session_manager.complete(req.session_id)

    return {"report_id": report_id, "evaluation": evaluation}"""