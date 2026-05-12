import os
from typing import Optional

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase
)

from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("MONGODB_DB_NAME")

if not MONGO_URL:
    raise ValueError("MONGODB_URL is missing")

if not DB_NAME:
    raise ValueError("MONGODB_DB_NAME is missing")

# Reused globally across Vercel invocations
_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:

    global _client

    if _client is None:

        _client = AsyncIOMotorClient(
            MONGO_URL,
            maxPoolSize=5,
            minPoolSize=1,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )

    return _client


async def get_database() -> AsyncIOMotorDatabase:
    return get_client()[DB_NAME]


async def init_mongo():

    db = await get_database()

    # students
    await db.students.create_index(
        "google_sub",
        unique=True
    )

    # sessions
    await db.sessions.create_index("student_id")

    await db.sessions.create_index([
        ("student_id", 1),
        ("status", 1)
    ])

    # evaluations
    await db.evaluations.create_index("student_id")

    await db.evaluations.create_index(
        "session_id",
        unique=True
    )

    # auto cleanup abandoned sessions
    await db.sessions.create_index(
        "started_at",
        expireAfterSeconds=604800,
        partialFilterExpression={
            "status": "active"
        }
    )