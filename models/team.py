from datetime import datetime

from pydantic import BaseModel


class TeamCreate(BaseModel):
    name: str
    luminary_slugs: list[str]


class TeamUpdate(BaseModel):
    name: str | None = None
    luminary_slugs: list[str] | None = None


class TeamResponse(BaseModel):
    id: str
    user_id: str
    name: str
    luminary_slugs: list[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_mongo(cls, doc: dict) -> "TeamResponse":
        return cls(
            id=str(doc["_id"]),
            user_id=str(doc["user_id"]),
            name=doc["name"],
            luminary_slugs=doc["luminary_slugs"],
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
        )
