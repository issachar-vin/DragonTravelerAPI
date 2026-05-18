from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

import services.team_service as team_service
from database import get_db
from models.team import TeamCreate, TeamResponse, TeamUpdate
from models.user import UserResponse
from routers.auth import get_current_user

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[TeamResponse])
def list_teams(
    current_user: UserResponse = Depends(get_current_user), db: Database = Depends(get_db)
):
    return team_service.get_user_teams(db, current_user.id)


@router.post("/", response_model=TeamResponse, status_code=201)
def create_team(
    data: TeamCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return team_service.create_team(db, current_user.id, data)


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    try:
        return team_service.get_team(db, team_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: str,
    data: TeamUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    try:
        return team_service.update_team(db, team_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{team_id}", status_code=204)
def delete_team(
    team_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    try:
        team_service.delete_team(db, team_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
