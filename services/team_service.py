from pymongo.database import Database

import repositories.team_repo as team_repo
from models.team import TeamCreate, TeamResponse, TeamUpdate


def get_user_teams(db: Database, user_id: str) -> list[TeamResponse]:
    return [TeamResponse.from_mongo(doc) for doc in team_repo.find_by_user(db, user_id)]


def create_team(db: Database, user_id: str, data: TeamCreate) -> TeamResponse:
    doc = team_repo.create_team(db, user_id, data.name, data.luminary_slugs)
    return TeamResponse.from_mongo(doc)


def get_team(db: Database, team_id: str, user_id: str) -> TeamResponse:
    doc = team_repo.find_by_id(db, team_id)
    if not doc:
        raise ValueError("Team not found")
    if str(doc["user_id"]) != user_id:
        raise PermissionError("Not your team")
    return TeamResponse.from_mongo(doc)


def update_team(db: Database, team_id: str, user_id: str, data: TeamUpdate) -> TeamResponse:
    doc = team_repo.find_by_id(db, team_id)
    if not doc:
        raise ValueError("Team not found")
    if str(doc["user_id"]) != user_id:
        raise PermissionError("Not your team")
    updates = data.model_dump(exclude_none=True)
    updated = team_repo.update_team(db, team_id, updates)
    return TeamResponse.from_mongo(updated)


def delete_team(db: Database, team_id: str, user_id: str) -> None:
    doc = team_repo.find_by_id(db, team_id)
    if not doc:
        raise ValueError("Team not found")
    if str(doc["user_id"]) != user_id:
        raise PermissionError("Not your team")
    team_repo.delete_team(db, team_id)
