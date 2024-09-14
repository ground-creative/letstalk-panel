from dataclasses import field
from marshmallow_dataclass import dataclass
from marshmallow import Schema, fields


@dataclass
class HelpAssistant:
    message: str = field(metadata={"required": True})
    max_history: int = field(
        default=20,
        metadata={
            "required": False,
            "description": "The maximum number of messages saved in the history for each sessions.<br> Use 0 to keep all messages in the history.",
        },
    )
