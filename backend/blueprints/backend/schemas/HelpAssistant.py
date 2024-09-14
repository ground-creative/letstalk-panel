from dataclasses import field
from marshmallow_dataclass import dataclass
from marshmallow import Schema, fields


@dataclass
class HelpAssistant:
    message: str = field(metadata={"required": True})


class HelpAssistantResponse(Schema):
    message = fields.Str(required=True)
