from sqlalchemy import Column, String, Text, SmallInteger, Integer, DateTime
from db.base import BaseModel
import json
from utils.fields import convert_properties, generate_random_string
from sqlalchemy.sql import func


class ProviderModel(BaseModel):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sid = Column(String(50), unique=True, nullable=False)
    workspace_sid = Column(String(50), nullable=False)
    name = Column(String(30), nullable=False)
    api_key = Column(String(100), nullable=False)
    address = Column(String(100), nullable=False)
    type = Column(String(30), nullable=False)
    source = Column(String(50), nullable=False)
    default_config = Column(Text, nullable=True)
    status = Column(SmallInteger, nullable=False, default=0)
    created = Column(DateTime, default=func.now(), nullable=False)
    updated = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ProviderModel(name={self.name}, type={self.type})>"

    @classmethod
    def toDict(cls, obj):
        obj = super().toDict(obj)
        return convert_properties({"default_config"}, obj)

    @classmethod
    def insert(cls, obj):
        obj.sid = generate_random_string()
        obj.status = 1
        if obj.default_config is not None:
            obj.default_config = json.dumps(obj.default_config)

        super().insert(obj)
        return obj.sid
