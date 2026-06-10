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

CF_ZONE_ID = os.getenv("CF_ZONE_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
PUBLIC_URL = os.getenv("PUBLIC_URL", "").rstrip("/")
API_PATH_PREFIX = os.getenv("API_PATH_PREFIX", "/api")
CF_PURGE_BATCH = 30

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


_ASSET_TYPES = (
    "portrait",
    "icon",
    "class",
    "faction",
    "skill",
    "talent",
    "subclass",
    "status_effect",
)


@router.post("/images/purge-cache")
async def purge_cache(
    db: Database = Depends(get_db),
    _: UserResponse = Depends(require_admin),
):
    if not CF_ZONE_ID or not CF_API_TOKEN or not PUBLIC_URL:
        return JSONResponse(
            {"status": "skipped", "detail": "Cloudflare env vars not configured"},
            status_code=200,
        )

    total = 0
    for type_ in _ASSET_TYPES:
        paths = [d["path"] for d in db.asset_images.find({"type": type_}, {"path": 1, "_id": 0})]
        await _purge_cloudflare_cache(paths)
        total += len(paths)

    return {"status": "purged", "total": total}


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


async def _purge_cloudflare_cache(paths: list[str]) -> None:
    if not CF_ZONE_ID or not CF_API_TOKEN or not PUBLIC_URL or not paths:
        return
    urls = [f"{PUBLIC_URL}{API_PATH_PREFIX}{p}" for p in paths]
    async with httpx.AsyncClient(timeout=30) as client:
        for i in range(0, len(urls), CF_PURGE_BATCH):
            batch = urls[i : i + CF_PURGE_BATCH]
            try:
                resp = await client.post(
                    f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/purge_cache",
                    headers={"Authorization": f"Bearer {CF_API_TOKEN}"},
                    json={"files": batch},
                )
                resp.raise_for_status()
                logger.info("Purged %d Cloudflare cache entries", len(batch))
            except Exception as exc:
                logger.error("Cloudflare cache purge failed: %s", exc)


async def _run_downloads(assets: list[dict], override: bool) -> None:
    global _download_running, _download_failures
    try:
        sem = asyncio.Semaphore(DOWNLOAD_CONCURRENCY)
        downloaded_paths: list[str] = []

        async def fetch(client: httpx.AsyncClient, url: str, dest: Path, path: str) -> None:
            if not override and dest.exists():
                return
            async with sem:
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(resp.content)
                    downloaded_paths.append(path)
                except Exception as exc:
                    logger.error("Failed to download %s → %s: %s", url, path, exc)
                    _download_failures.append({"url": url, "path": path, "error": str(exc)})

        async with httpx.AsyncClient(
            follow_redirects=True, timeout=30, headers={"User-Agent": UA}
        ) as client:
            await asyncio.gather(
                *[fetch(client, a["url"], _dest(a["path"]), a["path"]) for a in assets]
            )

        await _purge_cloudflare_cache(downloaded_paths)
    finally:
        _download_running = False
