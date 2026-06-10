from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from database import get_db
from repositories import team_repo, user_repo
from routers import admin, auth, gear, luminaries, status_effects, subclasses, teams
from telemetry import setup_telemetry

IMAGES_DIR = Path(settings.images_dir)

app = FastAPI(title="Dragon Traveler Guide API", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

app.include_router(auth.router)
app.include_router(teams.router)
app.include_router(luminaries.router)
app.include_router(gear.router)
app.include_router(subclasses.router)
app.include_router(status_effects.router)
app.include_router(admin.router)

setup_telemetry(app)


@app.on_event("startup")
def startup():
    db = get_db()
    user_repo.ensure_indexes(db)
    team_repo.ensure_indexes(db)
    db.asset_images.create_index("path", unique=True)
    db.asset_images.create_index("type")


@app.get("/")
def root():
    return {"message": "Hello from Dragon Traveler Manager"}


@app.get("/health")
def health():
    return {"status": "ok"}
