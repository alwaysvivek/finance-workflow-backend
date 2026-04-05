from sqlmodel import Session, select
from sqlalchemy import func
from app.models.models import Transaction, StatusEnum, TransactionTypeEnum, User
from typing import List, Dict, Any

class AnalyticsService:
    @staticmethod
    def get_total_spend(db: Session, current_user: User) -> float:
        # Sum of all APPROVED EXPENSE transactions for the company
        statement = select(func.sum(Transaction.amount)).where(
            Transaction.company_id == current_user.company_id,
            Transaction.status == StatusEnum.APPROVED,
            Transaction.type == TransactionTypeEnum.EXPENSE,
            Transaction.deleted_at == None
        )
        result = db.exec(statement).first()
        return float(result) if result else 0.0

    @staticmethod
    def get_category_breakdown(db: Session, current_user: User) -> List[Dict[str, Any]]:
        # Group by category and sum amounts
        statement = select(Transaction.category, func.sum(Transaction.amount).label("total")).where(
            Transaction.company_id == current_user.company_id,
            Transaction.status == StatusEnum.APPROVED,
            Transaction.type == TransactionTypeEnum.EXPENSE,
            Transaction.deleted_at == None
        ).group_by(Transaction.category)
        
        results = db.exec(statement).all()
        return [{"category": row[0], "total": float(row[1])} for row in results]

    @staticmethod
    def get_monthly_trends(db: Session, current_user: User) -> List[Dict[str, Any]]:
        # This implementation uses `strftime` for sqlite compatibility which we are currently using.
        # In a strict postgres setup, we would use func.date_trunc('month', Transaction.date)
        statement = select(
            func.strftime('%Y-%m', Transaction.date).label('month'), 
            func.sum(Transaction.amount).label('total')
        ).where(
            Transaction.company_id == current_user.company_id,
            Transaction.status == StatusEnum.APPROVED,
            Transaction.type == TransactionTypeEnum.EXPENSE,
            Transaction.deleted_at == None
        ).group_by('month').order_by('month')
        
        results = db.exec(statement).all()
        return [{"month": row[0], "total": float(row[1])} for row in results]

    @staticmethod
    def get_approval_rate(db: Session, current_user: User) -> Dict[str, int]:
        statement = select(Transaction.status, func.count(Transaction.id)).where(
            Transaction.company_id == current_user.company_id,
            Transaction.deleted_at == None
        ).group_by(Transaction.status)
        
        results = db.exec(statement).all()
        
        rate = {
            "approved": 0,
            "rejected": 0,
            "pending": 0,
        }
        for status, count in results:
            rate[status.lower()] = count
        return rate
