import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import jwt, JWTError
from bson import ObjectId
from database.mongo import get_database
from models.schemas import GoogleAuthRequest, TokenResponse
from pymongo import ReturnDocument

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_SECRET       = os.getenv("JWT_SECRET")  # No validation if None
ALGORITHM        = "HS256"

def create_jwt(student_id: str, email: str) -> str:
    payload = {
        "sub": student_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=int(os.getenv("JWT_EXPIRY_HOURS", 24)))
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

async def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[ALGORITHM])
        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        db = await get_database()
        student = await db.students.find_one({"_id": ObjectId(student_id)})
        if not student:
            raise HTTPException(status_code=401, detail="Student not found")
        student["id"] = str(student["_id"])
        return student
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")

@router.post("/google", response_model=TokenResponse)
async def google_login(req: GoogleAuthRequest):
    try:
        id_info = id_token.verify_oauth2_token(
            req.token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")

    google_sub = id_info["sub"]
    email      = id_info.get("email", "")
    name       = id_info.get("name", "")

    db = await get_database()

    # Upsert — create if not exists, return existing if does
    result = await db.students.find_one_and_update(
        {"google_sub": google_sub},
        {"$setOnInsert": {
            "google_sub": google_sub,
            "email": email,
            "name": name,
            "created_at": datetime.utcnow(),
            "progress": []          # embedded progress array
        }},
        upsert=True,
        return_document=ReturnDocument.AFTER       # returns the document after operation
    )

    student_id = str(result["_id"])
    token = create_jwt(student_id, email)

    return TokenResponse(
        access_token=token,
        student_name=result.get("name", name),
        student_email=result.get("email", email)
    )