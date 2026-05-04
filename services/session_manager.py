import uuid
from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from models.db_models import Session as SessionModel

def create_session(db: DBSession, student_id: str, case_id: str) -> SessionModel:
    session = SessionModel(
        id=str(uuid.uuid4()),
        student_id=student_id,
        case_id=case_id,
        status="active"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_session(db: DBSession, session_id: str) -> SessionModel | None:
    return db.query(SessionModel).filter(SessionModel.id == session_id).first()

def complete_session(db: DBSession, session_id: str):
    session = get_session(db, session_id)
    if session:
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        db.commit()

def get_student_sessions(db: DBSession, student_id: str) -> list[SessionModel]:
    return (
        db.query(SessionModel)
        .filter(SessionModel.student_id == student_id)
        .order_by(SessionModel.started_at.desc())
        .all()
    )