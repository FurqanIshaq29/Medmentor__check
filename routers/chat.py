from fastapi import APIRouter, Depends, HTTPException
from database.mongo import get_database
from routers.auth import get_current_student
from services.patient_loader import load_patient
from services.workflow_a import get_patient_response
from models.schemas import ChatMessageRequest, ChatMessageResponse
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    req: ChatMessageRequest,
    student: dict = Depends(get_current_student)
):
    db = await get_database()

    # Fetch ONLY required fields
    session = await db.sessions.find_one(
        {
            "_id": ObjectId(req.session_id),
            "student_id": student["id"]
        },
        {
            "turns": {"$slice": -20},   # last 20 only
            "turn_count": 1,
            "status": 1,
            "case_id": 1
        }
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["status"] == "completed":
        raise HTTPException(status_code=400, detail="Session already submitted")

    patient = load_patient(session["case_id"])

    # Last 20 turns already returned from MongoDB
    context_turns = session.get("turns", [])

    # Generate AI response
    reply = await get_patient_response(
        patient,
        context_turns,
        req.message
    )

    turn_number = session["turn_count"] + 1

    new_turn = {
        "turn_number": turn_number,
        "student_message": req.message,
        "patient_response": reply,
        "created_at": datetime.utcnow()
    }

    # Atomic update
    await db.sessions.update_one(
        {"_id": ObjectId(req.session_id)},
        {
            "$push": {"turns": new_turn},
            "$inc": {"turn_count": 1}
        }
    )

    return ChatMessageResponse(
        reply=reply,
        session_id=req.session_id,
        turn_number=turn_number
    )


@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    student: dict = Depends(get_current_student)
):
    db = await get_database()
    # Use projection to return only turns — avoids pulling entire doc
    session = await db.sessions.find_one(
        {"_id": ObjectId(session_id), "student_id": student["id"]},
        {"turns": 1}        
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"turns": [
        {"student_message": t["student_message"], "patient_response": t["patient_response"]}
        for t in session.get("turns", [])
    ]}