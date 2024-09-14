from sqlalchemy import Column, String, SmallInteger, Integer, DateTime
from db.base import BaseModel
from utils.fields import generate_random_string, convert_properties, convert_list
from sqlalchemy.sql import func
from blueprints.api.v2.models.Providers import ProviderModel
from blueprints.api.v2.models.LanguageModels import LanguageModel


def generate_random_embed_sid():

    return generate_random_string(50)


class ChatAssistantModel(BaseModel):
    __tablename__ = "assistants"

    __insert_return_column__ = "sid"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sid = Column(
        String(50), unique=True, nullable=False, default=generate_random_string
    )
    workspace_sid = Column(String(50), nullable=False)
    name = Column(String(30), nullable=False)
    type = Column(String(50), nullable=False)
    model_config_sid = Column(String(50), nullable=True)
    transcriber_config_sid = Column(String(50), nullable=True)
    voice_config_sid = Column(String(50), nullable=True)
    embed_sid = Column(String(50), nullable=True, default=generate_random_embed_sid)
    status = Column(SmallInteger, nullable=False, default=1)
    created = Column(DateTime, default=func.now(), nullable=False)
    updated = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    @classmethod
    def to_dict(cls, obj):
        obj = super().to_dict(obj)

        if isinstance(obj, list) and len(obj) > 0:
            for item in obj:
                model = LanguageModel.get(item["model_config_sid"])
                model_config = LanguageModel.to_dict(model)
                item["model"] = convert_properties(
                    {"extra_params", "tools"}, model_config
                )
                item["model"] = convert_list({"knowledge_base"}, item["model"])
                provider = ProviderModel.get(item["model"].get("provider_sid"))
                item["model"]["provider"] = ProviderModel.to_dict(provider)
        elif obj is not None:
            model = LanguageModel.get(obj["model_config_sid"])
            model_config = LanguageModel.to_dict(model)
            obj["model"] = convert_properties({"extra_params", "tools"}, model_config)
            obj["model"] = convert_list({"knowledge_base"}, obj["model"])
            provider = ProviderModel.get(obj["model"].get("provider_sid"))
            obj["model"]["provider"] = ProviderModel.to_dict(provider)

        return obj
