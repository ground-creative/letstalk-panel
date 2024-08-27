from sqlalchemy import Column, String, SmallInteger, Integer, Text, Float, DateTime
from db.base import BaseModel
from utils.fields import generate_random_string
from sqlalchemy.sql import func


class ChatAssistantModel(BaseModel):
    __tablename__ = "assistants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sid = Column(String(50), unique=True, nullable=False)
    workspace_sid = Column(String(50), nullable=False)
    provider_sid = Column(String(50), nullable=False)
    name = Column(String(30), nullable=False)
    system_prompt = Column(Text, nullable=False)
    model = Column(String(100), nullable=False)
    temperature = Column(Float, nullable=False)
    tools = Column(Text, nullable=True)
    knowledge_base = Column(Text, nullable=True)
    extra_params = Column(Text, nullable=True)
    status = Column(SmallInteger, nullable=False, default=0)
    created = Column(DateTime, default=func.now(), nullable=False)
    updated = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ProviderModel(name={self.name}, type={self.type})>"

    @classmethod
    def insert(cls, obj):
        obj.sid = generate_random_string()
        obj.status = 1
        super().insert(obj)
        return obj.sid
