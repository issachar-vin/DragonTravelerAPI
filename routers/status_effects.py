from fastapi import APIRouter, Depends
from pymongo.database import Database

from database import get_db
from utils.serialization import serialize_doc

router = APIRouter(prefix="/status-effects", tags=["status-effects"])


@router.get("")
def list_status_effects(db: Database = Depends(get_db)):
    docs = list(db.status_effects.find({}))
    return [serialize_doc(doc) for doc in docs]
