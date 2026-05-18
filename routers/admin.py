import asyncio
import logging
import os
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pymongo.database import Database

from database import get_db
from models.user import UserResponse
from routers.auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

IMAGES_DIR = Path(os.getenv("IMAGES_DIR", Path(__file__).parent.parent / "images"))
DOWNLOAD_CONCURRENCY = 12
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_download_running = False
_download_failures: list[dict] = []


def _dest(url_path: str) -> Path:
    # url_path is a URL-rooted path like "/images/luminaries/xxx.png".
    # Strip the "/images/" mount prefix to get the path relative to IMAGES_DIR.
    return IMAGES_DIR / url_path.removeprefix("/images/").lstrip("/")


@router.get("/images/status")
def images_status(
    db: Database = Depends(get_db),
    _: UserResponse = Depends(require_admin),
):
    total = db.asset_images.count_documents({})
    if total == 0:
        return {
            "total": 0,
            "downloaded": 0,
            "missing": 0,
            "running": _download_running,
            "failures": [],
        }
    assets = list(db.asset_images.find({}, {"url": 1, "path": 1, "_id": 0}))
    missing = [a for a in assets if not _dest(a["path"]).exists()]
    return {
        "total": total,
        "downloaded": total - len(missing),
        "missing": len(missing),
        "running": _download_running,
        "failures": _download_failures,
        "missing_paths": [a["path"] for a in missing],
    }


@router.post("/images/download")
async def start_download(
    override: bool = Query(False, description="Re-download images that already exist"),
    db: Database = Depends(get_db),
    _: UserResponse = Depends(require_admin),
):
    global _download_running, _download_failures
    if _download_running:
        return JSONResponse({"status": "already_running"}, status_code=409)

    assets = list(db.asset_images.find({}, {"url": 1, "path": 1, "_id": 0}))
    if not assets:
        return JSONResponse({"status": "no_assets", "detail": "Run seed.py first"}, status_code=404)

    _download_running = True
    _download_failures = []
    asyncio.create_task(_run_downloads(assets, override))
    return {"status": "started", "total": len(assets)}


async def _run_downloads(assets: list[dict], override: bool) -> None:
    global _download_running, _download_failures
    try:
        sem = asyncio.Semaphore(DOWNLOAD_CONCURRENCY)

        async def fetch(client: httpx.AsyncClient, url: str, dest: Path, path: str) -> None:
            if not override and dest.exists():
                return
            async with sem:
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(resp.content)
                except Exception as exc:
                    logger.error("Failed to download %s → %s: %s", url, path, exc)
                    _download_failures.append({"url": url, "path": path, "error": str(exc)})

        async with httpx.AsyncClient(
            follow_redirects=True, timeout=30, headers={"User-Agent": UA}
        ) as client:
            await asyncio.gather(
                *[fetch(client, a["url"], _dest(a["path"]), a["path"]) for a in assets]
            )
    finally:
        _download_running = False
