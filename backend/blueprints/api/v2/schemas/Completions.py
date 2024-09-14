from dataclasses import field
from marshmallow_dataclass import dataclass
from marshmallow import validate
from apiflask.validators import Length
from typing import Optional
from utils.fields import validate_pattern
from typing import List


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
    # tools: dict = field(default_factory={})
    # knowledge_base: str = field(default="", metadata={"required": False})
    knowledge_base: List[str] = field(
        default_factory=list, metadata={"required": False}
    )
    extra_params: dict = field(default_factory={})


# @dataclass
# class CompletionCreateSession:

#    session: str = field(default=None, metadata={"required": False})


@dataclass
class CompletionCreateSession:
    id: str = field(
        metadata={
            "required": True,
            "description": "A custom session id for the completion history",
            "validate": [
                Length(min=5, max=30),
                lambda value: validate_pattern(
                    value,
                    pattern="^[a-zA-Z0-9 _-]*$",
                    errorMsg="Only alphanumeric characters, spaces, underscores, and hyphens are accepted",
                ),
            ],
        },
    )
    channel: str = field(
        metadata={
            "required": True,
            "description": "A custom session channel. Ex: telegram",
            "validate": [
                Length(min=5, max=30),
                lambda value: validate_pattern(
                    value,
                    pattern="^[a-zA-Z0-9 _-]*$",
                    errorMsg="Only alphanumeric characters, spaces, underscores, and hyphens are accepted",
                ),
            ],
        },
    )


@dataclass
class CompletionCreate:

    message: str = field(metadata={"required": True})
    session: Optional[CompletionCreateSession] = None
    overrides: Optional[CompletionCreateOverrides] = None
