from sqlalchemy import Column, String, Text
from app.database import Base

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(50), primary_key=True, index=True)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
