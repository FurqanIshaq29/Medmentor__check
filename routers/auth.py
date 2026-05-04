import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from database.db import get_db
from models.db_models import Student
from models.schemas import GoogleAuthRequest, TokenResponse
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_SECRET = os.getenv("JWT_SECRET", "change-this")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", 24))
ALGORITHM = "HS256"

def create_jwt(student_id: str, email: str) -> str:
    payload = {
        "sub": student_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

"""def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> Student:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=401, detail="Student not found")
        return student
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")

@router.post("/google", response_model=TokenResponse)"""


######################################################################
######################################################################
def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> Student:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        print("🔍 JWT payload:", payload)

        student_id = payload.get("sub")
        print("🔍 Looking for student_id:", student_id)

        student = db.query(Student).filter(Student.id == student_id).first()
        print("🔍 DB result:", student)

        if not student:
            raise HTTPException(status_code=401, detail="Student not found")

        return student

    except JWTError as e:
        print("❌ JWT Error:", e)
        raise HTTPException(status_code=401, detail="Token expired or invalid")


######################################################################
@router.post("/google", response_model=TokenResponse)
async def google_login(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        id_info = id_token.verify_oauth2_token(
            req.token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
        print("✅ TOKEN VERIFIED")

    except Exception as e:
        print("❌ GOOGLE TOKEN ERROR TYPE:", type(e))
        print("❌ GOOGLE TOKEN ERROR:", repr(e))
        raise HTTPException(status_code=403, detail=str(e))

    google_sub = id_info["sub"]
    email = id_info.get("email", "")
    name = id_info.get("name", "")

    student = db.query(Student).filter(Student.google_sub == google_sub).first()
    if not student:
        student = Student(google_sub=google_sub, email=email, name=name)
        db.add(student)
        db.commit()
        db.refresh(student)

    token = create_jwt(student.id, student.email)

    return TokenResponse(
        access_token=token,
        student_name=student.name,
        student_email=student.email
    )