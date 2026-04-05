from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Any, Optional

from app.db.session import get_session
from app.models.models import User, RoleEnum, Transaction, StatusEnum, TransactionTypeEnum
from app.schemas.schemas import TransactionCreate, TransactionUpdate, TransactionResponse, StandardResponse
from app.api.deps import get_current_active_user, get_role_checker
from app.services.transaction_service import TransactionService

router = APIRouter()

@router.post("/", response_model=StandardResponse[TransactionResponse])
def create_transaction(
    *,
    db: Session = Depends(get_session),
    transaction_in: TransactionCreate,
    current_user: User = Depends(get_role_checker([RoleEnum.ADMIN, RoleEnum.ANALYST]))
) -> Any:
    """
    Create a new transaction. (Admin, Analyst)
    """
    tx = TransactionService.create_transaction(db, transaction_in, current_user)
    return {"data": tx, "meta": {}}

@router.get("/", response_model=StandardResponse[List[TransactionResponse]])
def get_transactions(
    db: Session = Depends(get_session),
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
    statement = select(Transaction).where(
        Transaction.company_id == current_user.company_id,
        Transaction.deleted_at == None
    )
    
    if type:
        statement = statement.where(Transaction.type == type)
    if category:
        statement = statement.where(Transaction.category == category)
    if status:
        statement = statement.where(Transaction.status == status)
        
    statement = statement.offset(skip).limit(limit)
    results = db.exec(statement).all()
    
    return {"data": results, "meta": {"count": len(results)}}

@router.get("/{transaction_id}", response_model=StandardResponse[TransactionResponse])
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get specific transaction by ID.
    """
    tx = db.get(Transaction, transaction_id)
    if not tx or tx.company_id != current_user.company_id or tx.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"data": tx, "meta": {}}

@router.put("/{transaction_id}", response_model=StandardResponse[TransactionResponse])
def update_transaction(
    transaction_id: int,
    *,
    db: Session = Depends(get_session),
    transaction_in: TransactionUpdate,
    current_user: User = Depends(get_role_checker([RoleEnum.ADMIN, RoleEnum.ANALYST]))
) -> Any:
    """
    Update a pending transaction. (Admin, Analyst)
    """
    tx = TransactionService.update_transaction(db, transaction_id, transaction_in, current_user)
    return {"data": tx, "meta": {}}

@router.put("/{transaction_id}/approve", response_model=StandardResponse[TransactionResponse])
def approve_transaction(
    transaction_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_role_checker([RoleEnum.ADMIN]))
) -> Any:
    """
    Approve a pending transaction. (Admin Only)
    """
    tx = TransactionService.approve_transaction(db, transaction_id, current_user)
    return {"data": tx, "meta": {}}

@router.put("/{transaction_id}/reject", response_model=StandardResponse[TransactionResponse])
def reject_transaction(
    transaction_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_role_checker([RoleEnum.ADMIN]))
) -> Any:
    """
    Reject a pending transaction. (Admin Only)
    """
    tx = TransactionService.reject_transaction(db, transaction_id, current_user)
    return {"data": tx, "meta": {}}

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_role_checker([RoleEnum.ADMIN]))
) -> Any:
    """
    Soft delete a transaction. (Admin Only)
    """
    res = TransactionService.delete_transaction(db, transaction_id, current_user)
    return {"data": res, "meta": {}}
