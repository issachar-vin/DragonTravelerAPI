from datetime import UTC, datetime

from bson import ObjectId
from pymongo.database import Database


def find_by_user(db: Database, user_id: str) -> list[dict]:
    return list(db.teams.find({"user_id": ObjectId(user_id)}))


def find_by_id(db: Database, team_id: str) -> dict | None:
    return db.teams.find_one({"_id": ObjectId(team_id)})


def create_team(db: Database, user_id: str, name: str, luminary_slugs: list[str]) -> dict:
    now = datetime.now(UTC)
    doc = {
        "user_id": ObjectId(user_id),
        "name": name,
        "luminary_slugs": luminary_slugs,
        "created_at": now,
        "updated_at": now,
    }
    result = db.teams.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def update_team(db: Database, team_id: str, updates: dict) -> dict | None:
    updates["updated_at"] = datetime.now(UTC)
    db.teams.update_one({"_id": ObjectId(team_id)}, {"$set": updates})
    return find_by_id(db, team_id)


def delete_team(db: Database, team_id: str) -> bool:
    result = db.teams.delete_one({"_id": ObjectId(team_id)})
    return result.deleted_count > 0


def ensure_indexes(db: Database) -> None:
    db.teams.create_index("user_id")
