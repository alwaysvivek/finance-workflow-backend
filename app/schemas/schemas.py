from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, Generic, TypeVar, Dict
from decimal import Decimal
from datetime import datetime
from app.models.models import RoleEnum, TransactionTypeEnum, StatusEnum

T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    data: T
    meta: Dict[str, Any] = {}

# Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[int] = None

# User
class UserCreate(BaseModel):
    email: str
    password: str
    role: RoleEnum = RoleEnum.VIEWER
    company_id: int

class UserResponse(BaseModel):
    id: int
    email: str
    role: RoleEnum
    is_active: bool
    company_id: int

# Transaction
class TransactionCreate(BaseModel):
    amount: Decimal
    type: TransactionTypeEnum
    category: str
    date: datetime
    notes: Optional[str] = None
    
    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("amount must be greater than 0")
        return v
        
    @field_validator("date")
    @classmethod
    def date_not_in_future(cls, v):
        # Allow naive timezones matching standard datetime.utcnow()
        if v.replace(tzinfo=None) > datetime.utcnow():
            raise ValueError("date cannot be in the future")
        return v

class TransactionResponse(BaseModel):
    id: int
    amount: Decimal
    type: TransactionTypeEnum
    category: str
    date: datetime
    notes: Optional[str] = None
    status: StatusEnum
    company_id: int
    created_by: int
    approved_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
