from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..core.database import Base


class NewsletterSubscriber(Base):
    __tablename__ = "newsletter"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {"id": str(self.id), "email": self.email, "created_at": self.created_at}