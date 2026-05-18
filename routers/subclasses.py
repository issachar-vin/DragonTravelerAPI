from fastapi import APIRouter, Depends
from pymongo.database import Database

from database import get_db
from utils.serialization import serialize_doc

router = APIRouter(prefix="/subclasses", tags=["subclasses"])


@router.get("")
def list_subclasses(db: Database = Depends(get_db)):
    docs = list(db.subclasses.find({}))
    return [serialize_doc(doc) for doc in docs]
