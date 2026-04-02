from enum import Enum
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from decimal import Decimal
from app.db.mixins import TimestampMixin, TenantMixin

class RoleEnum(str, Enum):
    VIEWER = "Viewer"
    ANALYST = "Analyst"
    ADMIN = "Admin"

class TransactionTypeEnum(str, Enum):
    INCOME = "Income"
    EXPENSE = "Expense"

class StatusEnum(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class Company(TimestampMixin, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

class User(TimestampMixin, TenantMixin, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: RoleEnum = Field(default=RoleEnum.VIEWER)
    is_active: bool = Field(default=True)

class Transaction(TimestampMixin, TenantMixin, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    type: TransactionTypeEnum
    category: str
    date: datetime
    notes: Optional[str] = Field(default=None)
    status: StatusEnum = Field(default=StatusEnum.PENDING)
    deleted_at: Optional[datetime] = Field(default=None)
    created_by: int = Field(foreign_key="user.id", nullable=False)
    approved_by: Optional[int] = Field(default=None, foreign_key="user.id")

class AuditLog(TenantMixin, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    action: str
    entity_type: str
    entity_id: int
    user_id: int = Field(foreign_key="user.id", nullable=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
