import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID

def get_utc_now():
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass
