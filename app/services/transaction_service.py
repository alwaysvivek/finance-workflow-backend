from sqlmodel import Session
from fastapi import HTTPException, status
from app.models.models import Transaction, AuditLog, StatusEnum, User
from app.schemas.schemas import TransactionCreate, TransactionUpdate
from decimal import Decimal
from datetime import datetime

class TransactionService:
    @staticmethod
    def create_transaction(db: Session, transaction_in: TransactionCreate, current_user: User) -> Transaction:
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
        db.add(new_tx)
        
        # Log action
        audit_log = AuditLog(
            action="CREATE_TRANSACTION",
            entity_type="transaction",
            entity_id=0, # Temporary, handles post commit or we just flush
            user_id=current_user.id,
            company_id=current_user.company_id
        )
        db.add(audit_log)
        
        # Atomic commit
        db.commit()
        db.refresh(new_tx)
        
        # Update audit log with the actual ID
        audit_log.entity_id = new_tx.id
        db.add(audit_log)
        db.commit()
        
        return new_tx

    @staticmethod
    def update_transaction(db: Session, transaction_id: int, transaction_in: TransactionUpdate, current_user: User) -> Transaction:
        tx = db.get(Transaction, transaction_id)
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
        db.add(audit_log)
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx

    @staticmethod
    def approve_transaction(db: Session, transaction_id: int, current_user: User) -> Transaction:
        tx = db.get(Transaction, transaction_id)
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
            db.add(audit_log)
            db.add(tx)
            
            # Atomic transaction commit
            db.commit()
            db.refresh(tx)
            return tx
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to approve transaction: {str(e)}"
            )

    @staticmethod
    def reject_transaction(db: Session, transaction_id: int, current_user: User) -> Transaction:
        tx = db.get(Transaction, transaction_id)
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
            db.add(audit_log)
            db.add(tx)
            
            db.commit()
            db.refresh(tx)
            return tx
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to reject transaction: {str(e)}"
            )

    @staticmethod
    def delete_transaction(db: Session, transaction_id: int, current_user: User) -> dict:
        tx = db.get(Transaction, transaction_id)
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
        db.add(audit_log)
        db.add(tx)
        
        db.commit()
        return {"detail": "Transaction successfully deleted."}
