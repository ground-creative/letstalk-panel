from dataclasses import field
from apiflask.validators import Length
from marshmallow_dataclass import dataclass
from marshmallow import Schema, fields, validate, ValidationError
from blueprints.backend.models.Providers import ProviderModel
from flask import g
from utils.fields import validate_pattern


def validate_provider_sid(value):
    provider = ProviderModel.get(value)
    if not provider:
        raise ValidationError(f"Provider id {value} not found")
    g.provider = provider


@dataclass
class ChatAssistantCreate:
    provider: str = field(
        metadata={
            "required": True,
            "validate": validate_provider_sid,
            "description": "Provider ID",
        }
    )
    name: str = field(
        metadata={
            "required": True,
            "validate": [
                Length(min=5, max=30),
                lambda value: validate_pattern(
                    value,
                    pattern="^[a-zA-Z0-9 _-]*$",
                    errorMsg="Only alphanumeric characters, spaces, underscores and hyphens are accepted",
                ),
            ],
        }
    )
    system_prompt: str = field(metadata={"required": True})
    model: str = field(metadata={"required": True})
    temperature: float = field(
        metadata={"required": True, "validate": validate.Range(min=0.0, max=1.0)}
    )
    tools: dict = field(default_factory={})
    knowledge_base: str = field(default="", metadata={"required": False})
    extra_params: dict = field(default_factory={})


class ChatAssistantResponse(Schema):
    sid = fields.Str(required=True)
    name = fields.Str(required=True)
    model = fields.Str(required=True)
    provider_sid = fields.Str(required=True)
    workspace_sid = fields.Str(required=True)
    temperature = fields.Float(required=True)
    knowledge_base = fields.Str(required=True)
    tools = fields.Dict(required=True)
    extra_params = fields.Dict(required=True)
    created = fields.DateTime(format="%Y-%m-%d %H:%M:%S", required=True)
    updated = fields.DateTime(format="%Y-%m-%d %H:%M:%S", required=True)
