from datetime import datetime
from typing import Annotated

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PyObjectId = Annotated[str, Field(default_factory=lambda: str(ObjectId()))]


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def lower_email(cls, v: str) -> str:
        return v.lower()


class UserInDB(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="_id")
    email: str
    hashed_password: str
    created_at: datetime
    role: str = "user"


class UserResponse(BaseModel):
    id: str
    email: str
    role: str = "user"
