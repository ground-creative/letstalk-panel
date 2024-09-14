from dataclasses import field
from marshmallow_dataclass import dataclass
from marshmallow import validate, Schema
from typing import List, Dict, Any, Optional
from utils.fields import validate_pattern
from flask_marshmallow.fields import fields
from blueprints.api.v2.schemas.ChatAssistants import validate_tools


@dataclass
class CompletionCreateOverrides:

    system_prompt: str = field(default=None, metadata={"required": False})
    model: str = field(default=None, metadata={"required": False})
    # provider_sid: str = field(
    #    metadata={
    #        "required": True,
    #        "validate": validate_provider_sid,
    #        "description": "Provider ID",
    #    }
    # )
    # provider: ModelProvider = field(metadata={"required": True})
    temperature: float = field(
        default=None,
        metadata={"required": False, "validate": validate.Range(min=0.0, max=2.0)},
    )
    max_tokens: float = field(
        default=None,
        metadata={"required": False},
    )
    tools: List[Dict[str, Any]] = field(
        default_factory=list, metadata={"required": False, "validate": validate_tools}
    )
    # knowledge_base: str = field(default="", metadata={"required": False})
    # knowledge_base: List[str] = field(
    #    default_factory=list, metadata={"required": False}
    # )
    # extra_params: dict = field(default_factory={})


class CompletionCreateSession(Schema):
    X_Session_Id = fields.String(
        required=False,
        description="A custom session id to be used to keep track of the chat history.<br>Only alphanumeric characters, underscores, and hyphens are accepted. The minmum and maximum lengths 5 and 50 characters.",
        data_key="X-Session-Id",
        validate=[
            validate.Length(min=5, max=50),
            lambda value: validate_pattern(
                value,
                pattern="^[a-zA-Z0-9_-]*$",
                errorMsg="Only alphanumeric characters, underscores, and hyphens are accepted",
            ),
        ],
    )


@dataclass
class CompletionCreate:

    message: str = field(metadata={"required": True})
    max_history: int = field(
        default=20,
        metadata={
            "required": False,
            "description": "The maximum number of messages saved in the history for each sessions.<br> Use 0 to keep all messages in the history.",
        },
    )
    overrides: Optional[CompletionCreateOverrides] = None


class CompletionsResponse(Schema):
    message = fields.Str(required=True)
