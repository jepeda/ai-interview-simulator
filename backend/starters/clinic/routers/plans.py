from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from clinic import repository
from clinic.db import get_db
from clinic.schemas import PlanOut

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("", response_model=list[PlanOut])
def list_plans(db: Annotated[Session, Depends(get_db)]) -> list[PlanOut]:
    return [PlanOut.model_validate(plan) for plan in repository.list_plans(db)]
