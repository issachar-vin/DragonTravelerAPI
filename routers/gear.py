from fastapi import APIRouter, Depends
from pymongo.database import Database

from database import get_db

router = APIRouter(prefix="/gear-sets", tags=["gear"])


@router.get("")
def list_gear_sets(db: Database = Depends(get_db)):
    gear_sets = list(db.gear_sets.find({}))

    all_piece_ids = [
        p["gear_piece_id"]
        for gs in gear_sets
        for p in gs.get("pieces", [])
        if p.get("gear_piece_id")
    ]

    pieces_by_id = {str(p["_id"]): p for p in db.gear_pieces.find({"_id": {"$in": all_piece_ids}})}

    result = []
    for gs in gear_sets:
        enriched_pieces = []
        for piece_ref in gs.get("pieces", []):
            pid = str(piece_ref.get("gear_piece_id", ""))
            piece = pieces_by_id.get(pid)
            if piece:
                enriched_pieces.append(
                    {
                        "name": piece["name"],
                        "slug": piece["slug"],
                        "slot": piece.get("slot"),
                        "piece_effect": piece.get("piece_effect"),
                        "images": piece.get("images", {}),
                    }
                )

        result.append(
            {
                "id": str(gs["_id"]),
                "name": gs["name"],
                "slug": gs["slug"],
                "bonus_type": gs.get("bonus_type"),
                "bonus_effect": gs.get("bonus_effect"),
                "pieces": enriched_pieces,
            }
        )

    return result
