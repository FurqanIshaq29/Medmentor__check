from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from models.db_models import Student
from models.schemas import ChatMessageRequest, ChatMessageResponse
from routers.auth import get_current_student
from services.session_manager import get_session
from services.patient_loader import load_patient
from services.chat_history import save_turn, get_turns
from services.workflow_a import get_patient_response

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    req: ChatMessageRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    session = get_session(db, req.session_id)
    if not session or session.student_id != student.id:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="This session is already submitted")

    patient = load_patient(session.case_id)
    history = get_turns(db, req.session_id)

    reply = await get_patient_response(patient, history, req.message)

    turn = save_turn(db, req.session_id, req.message, reply)
    return ChatMessageResponse(
        reply=reply,
        session_id=req.session_id,
        turn_number=turn.turn_number
    )

"""# /chat/message (Workflow A
# routers/chat.py

@router.post("/chat/message")
async def send_message(req: ChatMessageRequest, user=Depends(get_current_user)):
    session = session_manager.get_or_create(user.id, req.case_id)
    patient = patient_loader.load(req.case_id)

    # Load full conversation history from SQLite
    history = chat_history.get_turns(session.id)

    # Build messages array — this is the patient memory system
    messages = []
    for turn in history:
        messages.append({"role": "user", "content": turn.student_message})
        messages.append({"role": "assistant", "content": turn.patient_response})

    # Append the new student message
    messages.append({"role": "user", "content": req.message})

    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,           # patients give short answers
        system=build_patient_system_prompt(patient),
        messages=messages         # full history = patient remembers everything
    )

    patient_reply = response.content[0].text

    # Persist both sides of the conversation
    chat_history.save_turn(
        session_id=session.id,
        student_message=req.message,
        patient_response=patient_reply
    )

    return {"reply": patient_reply, "session_id": session.id}"""