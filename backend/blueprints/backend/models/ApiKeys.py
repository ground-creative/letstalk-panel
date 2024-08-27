from sqlalchemy import Column, String, SmallInteger, Integer, DateTime
from db.base import BaseModel
from utils.fields import generate_random_string, generate_api_key
from sqlalchemy.sql import func


class ApiKeyModel(BaseModel):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sid = Column(String(50), unique=True, nullable=False)
    workspace_sid = Column(String(50), nullable=False)
    name = Column(String(30), nullable=False)
    type = Column(String(30), nullable=False)
    api_key = Column(String(100), nullable=False)
    status = Column(SmallInteger, nullable=False, default=0)
    created = Column(DateTime, default=func.now(), nullable=False)
    updated = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ProviderModel(name={self.name}, type={self.type})>"

    @classmethod
    def insert(cls, obj):
        obj.sid = generate_random_string()
        prefix = f"{obj.type[:3]}-" if obj.type else ""
        obj.api_key = generate_api_key(prefix)
        obj.status = 1
        super().insert(obj)
        return obj.sid
