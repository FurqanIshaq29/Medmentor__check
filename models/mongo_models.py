from datetime import datetime
from bson import ObjectId

from database.mongo import get_database
from models.mongo_models import SessionDoc


async def create_session(student_id: str, case_id: str):

    db = get_database()

    session = SessionDoc(
        student_id=student_id,
        case_id=case_id,
        status="active"
    )

    result = await db.sessions.insert_one(
        session.dict()
    )

    created_session = await db.sessions.find_one(
        {"_id": result.inserted_id}
    )

    created_session["id"] = str(created_session["_id"])

    return created_session


async def get_session(session_id: str):

    db = get_database()

    session = await db.sessions.find_one({
        "_id": ObjectId(session_id)
    })

    if not session:
        return None

    session["id"] = str(session["_id"])

    return session


async def complete_session(session_id: str):

    db = get_database()

    await db.sessions.update_one(
        {"_id": ObjectId(session_id)},
        {
            "$set": {
                "status": "completed",
                "completed_at": datetime.utcnow()
            }
        }
    )


async def get_student_sessions(student_id: str):

    db = get_database()

    sessions_cursor = db.sessions.find({
        "student_id": student_id
    }).sort("started_at", -1)

    sessions = await sessions_cursor.to_list(length=100)

    for session in sessions:
        session["id"] = str(session["_id"])

    return sessions