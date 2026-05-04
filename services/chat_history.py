from sqlalchemy.orm import Session as DBSession
from models.db_models import ChatTurn

def save_turn(
    db: DBSession,
    session_id: str,
    student_message: str,
    patient_response: str
) -> ChatTurn:
    turn_number = get_turn_count(db, session_id) + 1
    turn = ChatTurn(
        session_id=session_id,
        turn_number=turn_number,
        student_message=student_message,
        patient_response=patient_response
    )
    db.add(turn)
    db.commit()
    db.refresh(turn)
    return turn

def get_turns(db: DBSession, session_id: str) -> list[ChatTurn]:
    return (
        db.query(ChatTurn)
        .filter(ChatTurn.session_id == session_id)
        .order_by(ChatTurn.turn_number.asc())
        .all()
    )

def get_turn_count(db: DBSession, session_id: str) -> int:
    return db.query(ChatTurn).filter(ChatTurn.session_id == session_id).count()