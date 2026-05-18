from bson import ObjectId
from fastapi import APIRouter, Depends
from pymongo.database import Database

from database import get_db

router = APIRouter(prefix="/status-effects", tags=["status-effects"])


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    for k, v in list(doc.items()):
        if isinstance(v, ObjectId):
            doc[k] = str(v)
    return doc


@router.get("")
def list_status_effects(db: Database = Depends(get_db)):
    docs = list(db.status_effects.find({}))
    return [_serialize(doc) for doc in docs]
