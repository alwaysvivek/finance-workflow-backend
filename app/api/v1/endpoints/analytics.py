from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import Any, List, Dict

from app.db.session import get_session
from app.models.models import User, RoleEnum
from app.schemas.schemas import StandardResponse
from app.api.deps import get_role_checker
from app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/total-spend", response_model=StandardResponse[float])
def get_total_spend(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_role_checker([RoleEnum.ADMIN, RoleEnum.ANALYST]))
) -> Any:
    """
    Get the total spend (approved expenses) for the company.
    """
    res = AnalyticsService.get_total_spend(db, current_user)
    return {"data": res, "meta": {}}

@router.get("/category-breakdown", response_model=StandardResponse[List[Dict[str, Any]]])
def get_category_breakdown(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_role_checker([RoleEnum.ADMIN, RoleEnum.ANALYST]))
) -> Any:
    """
    Get a breakdown of expenses by category.
    """
    res = AnalyticsService.get_category_breakdown(db, current_user)
    return {"data": res, "meta": {}}

@router.get("/monthly-trend", response_model=StandardResponse[List[Dict[str, Any]]])
def get_monthly_trends(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_role_checker([RoleEnum.ADMIN, RoleEnum.ANALYST]))
) -> Any:
    """
    Get the monthly trends of expenses.
    """
    res = AnalyticsService.get_monthly_trends(db, current_user)
    return {"data": res, "meta": {}}

@router.get("/approval-rate", response_model=StandardResponse[Dict[str, int]])
def get_approval_rate(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_role_checker([RoleEnum.ADMIN, RoleEnum.ANALYST]))
) -> Any:
    """
    Get the approval rate counts.
    """
    res = AnalyticsService.get_approval_rate(db, current_user)
    return {"data": res, "meta": {}}
