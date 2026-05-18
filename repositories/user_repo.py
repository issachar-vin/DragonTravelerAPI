from datetime import UTC, datetime

from bson import ObjectId
from pymongo.database import Database


def find_by_email(db: Database, email: str) -> dict | None:
    return db.users.find_one({"email": email})


def find_by_id(db: Database, user_id: str) -> dict | None:
    return db.users.find_one({"_id": ObjectId(user_id)})


def create_user(db: Database, email: str, hashed_password: str) -> dict:
    doc = {
        "email": email,
        "hashed_password": hashed_password,
        "role": "user",
        "created_at": datetime.now(UTC),
    }
    result = db.users.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


def set_role(db: Database, email: str, role: str) -> bool:
    result = db.users.update_one({"email": email.lower()}, {"$set": {"role": role}})
    return result.matched_count > 0


def ensure_indexes(db: Database) -> None:
    db.users.create_index("email", unique=True)
