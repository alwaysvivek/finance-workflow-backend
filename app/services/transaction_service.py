from typing import List, Optional
from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.models import Transaction, AuditLog, StatusEnum, TransactionTypeEnum, User
from app.schemas.schemas import TransactionCreate, TransactionUpdate
from decimal import Decimal
from datetime import datetime

class TransactionService:
    def __init__(self, db: Session):
        self.db = db

    def list_transactions(
        self, 
        current_user: User, 
        type: Optional[TransactionTypeEnum] = None,
        category: Optional[str] = None,
        status: Optional[StatusEnum] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        statement = select(Transaction).where(
            Transaction.company_id == current_user.company_id,
            Transaction.deleted_at.is_(None)
        )
        
        if type:
            statement = statement.where(Transaction.type == type)
        if category:
            statement = statement.where(Transaction.category == category)
        if status:
            statement = statement.where(Transaction.status == status)
            
        statement = statement.offset(skip).limit(limit)
        return self.db.exec(statement).all()

    def get_transaction(self, transaction_id: int, current_user: User) -> Transaction:
        tx = self.db.get(Transaction, transaction_id)
        if not tx or tx.company_id != current_user.company_id or tx.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return tx

    def create_transaction(self, transaction_in: TransactionCreate, current_user: User) -> Transaction:
        if transaction_in.amount <= Decimal(0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction amount must be greater than 0"
            )
        
        new_tx = Transaction(
            **transaction_in.model_dump(),
            status=StatusEnum.PENDING,
            company_id=current_user.company_id,
            created_by=current_user.id
        )
        self.db.add(new_tx)
        
        # Log action
        audit_log = AuditLog(
            action="CREATE_TRANSACTION",
            entity_type="transaction",
            entity_id=0, # Temporary, handles post commit or we just flush
            user_id=current_user.id,
            company_id=current_user.company_id
        )
        self.db.add(audit_log)
        
        # Atomic commit
        self.db.commit()
        self.db.refresh(new_tx)
        
        # Update audit log with the actual ID
        audit_log.entity_id = new_tx.id
        self.db.add(audit_log)
        self.db.commit()
        
        return new_tx

    def update_transaction(self, transaction_id: int, transaction_in: TransactionUpdate, current_user: User) -> Transaction:
        tx = self.db.get(Transaction, transaction_id)
        if not tx or tx.company_id != current_user.company_id or tx.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Transaction not found")

        if tx.status != StatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending transactions can be updated"
            )

        update_data = transaction_in.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        for field, value in update_data.items():
            setattr(tx, field, value)
        tx.updated_at = datetime.utcnow()

        audit_log = AuditLog(
            action="UPDATE_TRANSACTION",
            entity_type="transaction",
            entity_id=tx.id,
            user_id=current_user.id,
            company_id=current_user.company_id
        )
        self.db.add(audit_log)
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    def approve_transaction(self, transaction_id: int, current_user: User) -> Transaction:
        tx = self.db.get(Transaction, transaction_id)
        if not tx or tx.company_id != current_user.company_id or tx.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if tx.status != StatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending transactions can be approved"
            )
            
        if tx.created_by == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Self-approval of transactions is not allowed"
            )
            
        try:
            tx.status = StatusEnum.APPROVED
            tx.approved_by = current_user.id
            tx.updated_at = datetime.utcnow()
            
            audit_log = AuditLog(
                action="APPROVE_TRANSACTION",
                entity_type="transaction",
                entity_id=tx.id,
                user_id=current_user.id,
                company_id=current_user.company_id
            )
            self.db.add(audit_log)
            self.db.add(tx)
            
            # Atomic transaction commit
            self.db.commit()
            self.db.refresh(tx)
            return tx
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to approve transaction: {str(e)}"
            )

    def reject_transaction(self, transaction_id: int, current_user: User) -> Transaction:
        tx = self.db.get(Transaction, transaction_id)
        if not tx or tx.company_id != current_user.company_id or tx.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if tx.status != StatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending transactions can be rejected"
            )
            
        try:
            tx.status = StatusEnum.REJECTED
            tx.updated_at = datetime.utcnow()
            
            audit_log = AuditLog(
                action="REJECT_TRANSACTION",
                entity_type="transaction",
                entity_id=tx.id,
                user_id=current_user.id,
                company_id=current_user.company_id
            )
            self.db.add(audit_log)
            self.db.add(tx)
            
            self.db.commit()
            self.db.refresh(tx)
            return tx
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to reject transaction: {str(e)}"
            )

    def delete_transaction(self, transaction_id: int, current_user: User) -> dict:
        tx = self.db.get(Transaction, transaction_id)
        if not tx or tx.company_id != current_user.company_id or tx.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Transaction not found")
            
        tx.deleted_at = datetime.utcnow()
        tx.updated_at = datetime.utcnow()
        
        audit_log = AuditLog(
            action="SOFT_DELETE_TRANSACTION",
            entity_type="transaction",
            entity_id=tx.id,
            user_id=current_user.id,
            company_id=current_user.company_id
        )
        self.db.add(audit_log)
        self.db.add(tx)
        
        self.db.commit()
        return {"detail": "Transaction successfully deleted."}
