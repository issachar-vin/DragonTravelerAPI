from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database

from database import get_db

router = APIRouter(prefix="/luminaries", tags=["luminaries"])


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    for k, v in list(doc.items()):
        if isinstance(v, ObjectId):
            doc[k] = str(v)
        elif isinstance(v, list):
            doc[k] = [_serialize_value(item) for item in v]
        elif isinstance(v, dict):
            doc[k] = _serialize_nested(v)
    return doc


def _serialize_value(value):
    if isinstance(value, ObjectId):
        return str(value)
    elif isinstance(value, dict):
        return _serialize_nested(value)
    elif isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


def _serialize_nested(d: dict) -> dict:
    return {k: _serialize_value(v) for k, v in d.items()}


def _embed_gear_images(docs: list[dict], db: Database) -> None:
    """Mutates docs in-place, embedding gear image paths into recommended_gear items."""
    piece_ids = list(
        {
            item["gear_piece_id"]
            for doc in docs
            for item in doc.get("recommended_gear", [])
            if item.get("gear_piece_id")
        }
    )
    if not piece_ids:
        return
    gear_by_id = {
        str(p["_id"]): p for p in db.gear_pieces.find({"_id": {"$in": piece_ids}}, {"images": 1})
    }
    for doc in docs:
        for item in doc.get("recommended_gear", []):
            piece = gear_by_id.get(str(item.get("gear_piece_id", "")))
            if piece:
                item["images"] = piece.get("images", {})


@router.get("")
def list_luminaries(
    db: Database = Depends(get_db),
    class_: str | None = Query(None, alias="class"),
    faction: str | None = None,
    tier: str | None = None,
):
    query: dict = {}
    if class_:
        query["class"] = class_
    if faction:
        query["factions"] = faction
    if tier:
        query["tiers.overall"] = tier
    docs = list(db.luminaries.find(query))
    _embed_gear_images(docs, db)
    return [_serialize(doc) for doc in docs]


@router.get("/{slug}")
def get_luminary(slug: str, db: Database = Depends(get_db)):
    doc = db.luminaries.find_one({"slug": slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Luminary not found")
    _embed_gear_images([doc], db)
    return _serialize(doc)
