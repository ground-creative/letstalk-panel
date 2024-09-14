from dataclasses import field, fields
from apiflask.validators import Length
from marshmallow_dataclass import dataclass
from marshmallow import Schema, fields, validate
from flask import g
from utils.fields import validate_pattern, validate_provider_sid
from typing import List
from marshmallow import ValidationError
from typing import List, Dict, Any, Optional
import re
from urllib.parse import urlparse


@dataclass
class ToolMessages:
    type: str
    content: str

    def validate(self):
        if self.type not in ["request-failed", "request-complete"]:
            raise ValidationError(f"Invalid message.type: {self.type}.")
        if not self.content:
            raise ValidationError("Property message.content cannot be empty.")


@dataclass
class ToolFunctionParameters:
    type: str
    properties: Dict[str, Dict[str, str]]
    required: Optional[List] = None

    def validate(self):
        # Check that 'type' is 'object'
        if self.type != "object":
            raise ValidationError(
                f"Invalid function property type: {self.type}. Expected 'object'."
            )

        # Check that 'properties' is a dictionary
        if not isinstance(self.properties, dict):
            raise ValidationError(
                f"Invalid value for 'properties': {self.properties}. It should be a dictionary."
            )
        for prop_name, prop_details in self.properties.items():
            if not isinstance(prop_details, dict):
                raise ValidationError(
                    f"Invalid value for property '{prop_name}': {prop_details}. Each property should be a dictionary."
                )
            if "type" not in prop_details or "description" not in prop_details:
                raise ValidationError(
                    f"Property '{prop_name}' must contain 'type' and 'description'."
                )
            if not isinstance(prop_details["type"], str) or not isinstance(
                prop_details["description"], str
            ):
                raise ValidationError(
                    f"Property '{prop_name}' must have 'type' and 'description' as strings."
                )

            prop_types = ["numeric", "string"]

            if prop_details["type"] not in prop_types:
                allowed_types = ", ".join(prop_types)
                raise ValidationError(
                    f"Property '{prop_name}' has an invalid 'type': {prop_details['type']}. Allowed types are: {allowed_types}."
                )

        # Check that 'required' is either a list or None
        if self.required:
            if not isinstance(self.required, list):
                raise ValidationError(
                    f"Invalid value for 'required': {self.required}. It should be a list."
                )
            if any(not isinstance(item, str) for item in self.required):
                raise ValidationError(f"All items in 'required' must be strings.")


@dataclass
class ToolFunction:
    name: str
    description: str
    parameters: Optional[ToolFunctionParameters] = None

    def validate(self):
        if not self.name:
            raise ValidationError("Property function.name cannot be empty.")
        # Ensure the name only contains alphabetic characters and underscores
        if not re.match(r"^[a-zA-Z_]+$", self.name):
            raise ValidationError(
                f"Invalid function name: '{self.name}'. It should only contain alphabetic characters and underscores."
            )
        if not self.description:
            raise ValidationError("Property function.description cannot be empty.")

        if self.parameters:
            tool = ToolFunctionParameters(**self.parameters)
            tool.validate()


@dataclass
class ToolServer:
    url: str

    def validate(self):
        # Check if URL is empty
        if not self.url:
            raise ValueError("Property server.url is required")

        # Basic URL validation using urlparse
        parsed_url = urlparse(self.url)
        if not (parsed_url.scheme and parsed_url.netloc):
            raise ValueError(
                "Invalid  server.url format. A valid URL must include a scheme and network location."
            )


@dataclass
class Tool:
    type: str
    function: ToolFunction
    server: ToolServer
    messages: List[ToolMessages] = field(default_factory=list)

    def validate(self):
        if self.type != "function":
            raise ValidationError(f"Invalid type: {self.type}. Expected 'function'.")

        if self.function:
            try:
                self.function.validate()
            except ValidationError as e:
                raise ValidationError(f"Property function validation error: {e}")
        else:
            raise ValidationError(
                "Property function is required when type is 'function'."
            )

        if self.server:
            try:
                self.server.validate()
            except ValidationError as e:
                raise ValidationError(f"Property server validation error: {e}")
        else:
            raise ValidationError(
                "Property server is required when type is 'function'."
            )

        for message in self.messages:
            message.validate()


def validate_tools(tools: List[Dict[str, Any]]):
    # Hardcoded set of allowed fields
    allowed_fields = {"type", "function", "messages", "server"}
    for tool_data in tools:
        try:
            extra_fields = set(tool_data.keys()) - allowed_fields
            if extra_fields:
                raise ValidationError(f"Unknown fields: {', '.join(extra_fields)}")

            messages_data = tool_data.get("messages", [])
            messages = [ToolMessages(**msg) for msg in messages_data]
            function_data = tool_data.get("function")

            if function_data is None:
                raise ValidationError(
                    "Property function is required when type is 'function'."
                )
            if not isinstance(function_data, dict):
                raise ValidationError("Property function must be a dictionary.")

            function_instance = ToolFunction(**function_data)
            server = tool_data.get("server")

            if server is None:
                raise ValidationError(
                    "Property server is required when type is 'function'."
                )
            if not isinstance(server, dict):
                raise ValidationError("Property server must be a dictionary.")

            server_instance = ToolServer(**server)
            tool = Tool(
                type=tool_data["type"],
                messages=messages,
                function=function_instance,
                server=server_instance,
            )
            tool.validate()
        except Exception as e:
            raise ValidationError(f"Invalid tool format: {e}")


@dataclass
class ModelConfig:
    system_prompt: str = field(metadata={"required": True})
    model: str = field(metadata={"required": True})
    provider_sid: str = field(
        metadata={
            "required": True,
            "validate": validate_provider_sid,
            "description": "Provider ID",
        }
    )
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
    knowledge_base: List[str] = field(
        default_factory=list, metadata={"required": False}
    )
    extra_params: dict = field(default_factory={})


@dataclass
class ChatAssistantCreate:
    name: str = field(
        metadata={
            "required": True,
            "validate": [
                Length(min=5, max=30),
                lambda value: validate_pattern(
                    value,
                    pattern="^[a-zA-Z0-9 _-]*$",
                    errorMsg="Only alphanumeric characters, spaces, underscores, and hyphens are accepted",
                ),
            ],
        }
    )
    model: ModelConfig = field(metadata={"required": True})


class ModelConfigProviderResponse(Schema):
    sid = fields.Str()
    name = fields.Str()


class ModelConfigToolsMessagesResponse(Schema):
    type = fields.Str()
    content = fields.Str()


class ModelConfigToolsParametersPropertiesResponse(Schema):
    type = fields.Str()
    description = fields.Str()


class ModelConfigToolsParametersResponse(Schema):
    type = fields.Str()
    properties = fields.Dict(
        keys=fields.Str(),
        values=fields.Nested(ModelConfigToolsParametersPropertiesResponse),
    )
    required = fields.List(fields.Str())


class ModelConfigToolsFunctionResponse(Schema):
    name = fields.Str()
    description = fields.Str()
    parameters = fields.Nested(ModelConfigToolsParametersResponse)


class ModelConfigToolsServerResponse(Schema):
    url = fields.Str()


class ModelConfigToolsResponse(Schema):
    type = fields.Str()
    messages = fields.List(fields.Nested(ModelConfigToolsMessagesResponse))
    function = fields.Nested(ModelConfigToolsFunctionResponse)
    server = fields.Nested(ModelConfigToolsServerResponse)


class ModelConfigResponse(Schema):
    sid = fields.Str()
    model = fields.Str()
    system_prompt = fields.Str()
    temperature = fields.Float()
    max_tokens = fields.Float()
    knowledge_base = fields.List(fields.Str(), missing=[])
    tools = fields.List(fields.Nested(ModelConfigToolsResponse))
    extra_params = fields.Dict()
    provider = fields.Nested(ModelConfigProviderResponse)


class ChatAssistantResponse(Schema):
    sid = fields.Str()
    name = fields.Str()
    model = fields.Nested(ModelConfigResponse)
    created = fields.DateTime(format="%Y-%m-%d %H:%M:%S")
    updated = fields.DateTime(format="%Y-%m-%d %H:%M:%S")
