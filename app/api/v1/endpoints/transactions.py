from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Any, Optional

from app.db.session import get_session
from app.models.models import User, RoleEnum, Transaction, StatusEnum, TransactionTypeEnum
from app.schemas.schemas import TransactionCreate, TransactionUpdate, TransactionResponse, StandardResponse
from app.api.deps import get_current_active_user, get_role_checker
from app.services.transaction_service import TransactionService

def get_transaction_service(db: Session = Depends(get_session)) -> TransactionService:
    return TransactionService(db)

router = APIRouter()

@router.post("/", response_model=StandardResponse[TransactionResponse])
def create_transaction(
    *,
    service: TransactionService = Depends(get_transaction_service),
    transaction_in: TransactionCreate,
    current_user: User = Depends(get_role_checker([RoleEnum.ADMIN, RoleEnum.ANALYST]))
) -> Any:
    """
    Create a new transaction. (Admin, Analyst)
    """
    tx = service.create_transaction(transaction_in, current_user)
    return {"data": tx, "meta": {}}

@router.get("/", response_model=StandardResponse[List[TransactionResponse]])
def get_transactions(
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_active_user),
    type: Optional[TransactionTypeEnum] = None,
    category: Optional[str] = None,
    status: Optional[StatusEnum] = None,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve transactions for the current user's company with optional filtering.
    """
    # Moving query logic to service's internal helper for full OOP
    results = service.list_transactions(
        current_user=current_user,
        type=type,
        category=category,
        status=status,
        skip=skip,
        limit=limit
    )
    
    return {"data": results, "meta": {"count": len(results)}}

@router.get("/{transaction_id}", response_model=StandardResponse[TransactionResponse])
def get_transaction(
    transaction_id: int,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get specific transaction by ID.
    """
    tx = service.get_transaction(transaction_id, current_user)
    return {"data": tx, "meta": {}}

@router.put("/{transaction_id}", response_model=StandardResponse[TransactionResponse])
def update_transaction(
    transaction_id: int,
    *,
    service: TransactionService = Depends(get_transaction_service),
    transaction_in: TransactionUpdate,
    current_user: User = Depends(get_role_checker([RoleEnum.ADMIN, RoleEnum.ANALYST]))
) -> Any:
    """
    Update a pending transaction. (Admin, Analyst)
    """
    tx = service.update_transaction(transaction_id, transaction_in, current_user)
    return {"data": tx, "meta": {}}

@router.put("/{transaction_id}/approve", response_model=StandardResponse[TransactionResponse])
def approve_transaction(
    transaction_id: int,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_role_checker([RoleEnum.ADMIN]))
) -> Any:
    """
    Approve a pending transaction. (Admin Only)
    """
    tx = service.approve_transaction(transaction_id, current_user)
    return {"data": tx, "meta": {}}

@router.put("/{transaction_id}/reject", response_model=StandardResponse[TransactionResponse])
def reject_transaction(
    transaction_id: int,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_role_checker([RoleEnum.ADMIN]))
) -> Any:
    """
    Reject a pending transaction. (Admin Only)
    """
    tx = service.reject_transaction(transaction_id, current_user)
    return {"data": tx, "meta": {}}

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_role_checker([RoleEnum.ADMIN]))
) -> Any:
    """
    Soft delete a transaction. (Admin Only)
    """
    res = service.delete_transaction(transaction_id, current_user)
    return {"data": res, "meta": {}}
