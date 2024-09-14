from sqlalchemy import Column, String, SmallInteger, Integer, Text, Float, DateTime
from db.base import BaseModel
from utils.fields import generate_random_string, convert_properties, convert_list
from sqlalchemy.sql import func
import json


class LanguageModel(BaseModel):
    __tablename__ = "language_models"

    __insert_return_column__ = "sid"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sid = Column(
        String(50), unique=True, nullable=False, default=generate_random_string
    )
    assistant_sid = Column(String(50), nullable=False)
    provider_sid = Column(String(50), nullable=False)
    system_prompt = Column(Text, nullable=False)
    model = Column(String(100), nullable=False)
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Float, nullable=True)
    tools = Column(Text, nullable=True)
    knowledge_base = Column(Text, nullable=True)
    extra_params = Column(Text, nullable=True)
    status = Column(SmallInteger, nullable=False, default=1)
    created = Column(DateTime, default=func.now(), nullable=False)
    updated = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    # config = Column(Text, nullable=True)

    @classmethod
    def insert(cls, obj):

        if obj.knowledge_base is None:
            obj.knowledge_base = []

        if obj.tools is None:
            obj.tools = []

        obj.knowledge_base = json.dumps(obj.knowledge_base)
        obj.tools = json.dumps(obj.tools, indent=4)
        return super().insert(obj)

    @classmethod
    def update(cls, identifier, obj):

        if obj.knowledge_base is None:
            obj.knowledge_base = []

        if obj.tools is None:
            obj.tools = []

        obj.knowledge_base = json.dumps(obj.knowledge_base)
        obj.tools = json.dumps(obj.tools, indent=4)
        return super().update(identifier, obj)

    @classmethod
    def to_dict(cls, obj):
        obj = super().to_dict(obj)

        if isinstance(obj, list) and len(obj) > 0:
            for item in obj:
                item = convert_properties({"knowledge_base", "tools"}, item)
        elif obj is not None:
            obj = convert_properties({"knowledge_base", "tools"}, obj)

        return obj
