from dataclasses import field
from apiflask.validators import Length, OneOf, URL
from marshmallow_dataclass import dataclass
from marshmallow import Schema, fields
from utils.fields import validate_pattern


@dataclass
class ApiKeyCreate:
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
    type: str = field(
        metadata={
            "required": True,
            "validate": [
                OneOf(["public", "private"]),
                lambda value: validate_pattern(
                    value,
                    pattern="^[a-zA-Z0-9 _-]*$",
                    errorMsg="Only alphanumeric characters, spaces, underscores and hyphens are accepted",
                ),
            ],
        }
    )


@dataclass
class ApiKeyEdit:
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


class ApiKeyResponse(Schema):
    sid = fields.Str(required=True)
    name = fields.Str(required=True)
    type = fields.Str(required=True)
    api_key = fields.Str(required=True)
    workspace_sid = fields.Str(required=True)
    created = fields.DateTime(format="%Y-%m-%d %H:%M:%S", required=True)
    updated = fields.DateTime(format="%Y-%m-%d %H:%M:%S", required=True)
