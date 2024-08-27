from dataclasses import field
from apiflask.validators import Length, OneOf, URL
from marshmallow_dataclass import dataclass
from marshmallow import Schema, fields
from utils.fields import validate_pattern


@dataclass
class ProviderCreate:
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
    api_key: str = field(metadata={"required": True})
    address: str = field(metadata={"required": True, "validate": URL()})
    type: str = field(
        metadata={
            "required": True,
            "validate": OneOf(["transcriber", "model", "voice"]),
        }
    )
    source: str = field(metadata={"required": True})
    default_config: dict = field(
        default_factory={},
        # metadata={"example": {"key": "value"}},
    )


class ProviderResponse(Schema):
    sid = fields.Str(required=True)
    type = fields.Str(required=True)
    name = fields.Str(required=True)
    source = fields.Str(required=True)
    address = fields.Str(required=True)
    api_key = fields.Str(required=True)
    workspace_sid = fields.Str(required=True)
    default_config = fields.Dict(required=True)
    created = fields.DateTime(format="%Y-%m-%d %H:%M:%S", required=True)
    updated = fields.DateTime(format="%Y-%m-%d %H:%M:%S", required=True)
