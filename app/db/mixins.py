from sqlmodel import Field
from datetime import datetime, timezone
from typing import Optional

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class TimestampMixin:
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)

class TenantMixin:
    company_id: int = Field(foreign_key="company.id", nullable=False)
