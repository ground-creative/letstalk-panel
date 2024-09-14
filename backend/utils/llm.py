import requests, json
from typing import List, Dict, Any
from flask import current_app as app, g
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_cohere import ChatCohere, CohereEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.tools import StructuredTool
from pydantic import BaseModel, create_model
from typing import Optional
from utils.session_utils import save_session, get_session


def init_model(engine, **kwargs):

    try:

        if engine == "openai":
            return True, ChatOpenAI(**kwargs)
        elif engine == "anthropic":
            return True, ChatAnthropic(**kwargs)
        elif engine == "cohere":
            return True, ChatCohere(**kwargs)
        elif engine == "ollama":
            return True, ChatOllama(**kwargs)
        else:
            return False, f"Model Error: engine {engine} not supported!"

    except Exception as e:
        msg = f"Error initializing model: {str(e)}"
        app.logger.error(msg)
        return False, msg


def init_embeddings(engine, **kwargs):

    try:

        if engine == "openai":
            return True, OpenAIEmbeddings(**kwargs)
        elif engine == "anthropic":
            return True, OpenAIEmbeddings(**kwargs)
        elif engine == "cohere":
            return True, CohereEmbeddings(**kwargs)
        elif engine == "ollama":
            return True, OllamaEmbeddings(**kwargs)
        else:
            return False, f"Embeddings Error: engine {engine} not supported!"

    except Exception as e:
        msg = f"Error initializing model embeddings: {str(e)}"
        app.logger.error(msg)
        return False, msg


def get_template(template, type="standard"):

    if type == "tools":
        prompt_template = [
            ("system", template),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{query}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    else:
        prompt_template = [
            ("system", template),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{query}"),
        ]
    return ChatPromptTemplate.from_messages(prompt_template)


class EmptyArgsSchema(BaseModel):
    # No fields are required for this tool
    pass


def add_llm_tools(tools_array, assistant_tools):

    for item in assistant_tools:
        function_name = item["function"]["name"]
        server_url = item["server"]["url"]
        description = item["function"].get("description", "")

        if "parameters" in item["function"]:
            properties = item["function"]["parameters"]["properties"]
            required_fields = item["function"]["parameters"].get("required", [])
            fields = {}
            for field_name, field_info in properties.items():
                # if "enum" in field_info:
                #    field_enum = create_enum(
                #        f"{field_name.capitalize()}Enum", field_info["enum"]
                #    )
                #    field_type = field_enum
                # elif field_info["type"] == "string":
                if field_info["type"] == "string":
                    field_type = str
                if field_name in required_fields:
                    fields[field_name] = (field_type, ...)
                else:
                    fields[field_name] = (Optional[field_type], None)

            args_schema = create_model("DynamicArgsSchema", **fields)

        else:
            args_schema = EmptyArgsSchema

        messages = item.get("messages", [])

        tool = StructuredTool(
            name=function_name,
            func=lambda _FUNC_NAME=function_name, _SERVER=server_url, _MESSAGES=messages, **kwargs: call_tool(
                _FUNC_NAME=_FUNC_NAME, _SERVER=_SERVER, _MESSAGES=_MESSAGES, **kwargs
            ),
            description=description,
            args_schema=args_schema,
        )
        tools_array.append(tool)

    return tools_array


def call_tool(*args, **kwargs):
    # Print positional arguments
    if args:
        print("Positional arguments:", args)

    # Print keyword arguments
    if kwargs:
        print("Keyword arguments:", kwargs)

    server_url = kwargs.pop("_SERVER", None)

    if not server_url:
        print("Error: 'server' URL is required.")
        return

    messages = kwargs.pop("_MESSAGES", [])
    func_name = kwargs.pop("_FUNC_NAME", None)

    try:
        response = requests.get(server_url, params=kwargs)
        json_response = response.json()
        for message in messages:

            if message.get("type") == "request-complete":
                return {
                    **kwargs,
                    "result": json_response["result"],
                    "reply": True,
                    "message": message.get("content"),
                }

        return json.dumps({**kwargs, "result": json_response["result"]})

    except requests.RequestException as e:
        app.logger.error(f"Request failed: {str(e)}")
        for message in messages:

            if message.get("type") == "request-failed":
                return {
                    "error": message.get("content"),
                    "reply": True,
                    "arguments": kwargs,
                }

        return {
            "error": f"Function call failed for function {func_name}",
            "reply": False,
            "arguments": kwargs,
        }


def serialize_message(message) -> Dict[str, Any]:
    """Convert a single message object to a dictionary."""
    if isinstance(message, HumanMessage):
        return {"type": "HumanMessage", "content": message.content}
    elif isinstance(message, AIMessage):
        return {
            "type": "AIMessage",
            "content": message.content,
            "response_metadata": message.response_metadata,
            "id": message.id,
            "usage_metadata": message.usage_metadata,
        }
    else:
        raise ValueError("Unsupported message type")


def serialize_chat_history(messages: List) -> List[Dict[str, Any]]:
    """Convert a list of message objects to a list of dictionaries."""
    return [serialize_message(message) for message in messages]


def deserialize_chat_history(serialized_history: list) -> ChatMessageHistory:
    """Convert a list of dictionaries back into a ChatMessageHistory object."""
    history = ChatMessageHistory()
    for message in serialized_history:
        history.add_message(role=message["role"], content=message["content"])
    return history


def save_chat_history_to_db(session_id: str, history: ChatMessageHistory):
    """Save serialized chat history to the database."""
    serialized_history = serialize_chat_history(history)
    session_data = get_session(session_id)
    session_data["chat_history"] = serialized_history
    save_session(session_data)


def deserialize_message(data: Dict[str, Any]):
    """Convert a dictionary back into a message object."""
    if data["type"] == "HumanMessage":
        return HumanMessage(content=data["content"])
    elif data["type"] == "AIMessage":
        return AIMessage(
            content=data["content"],
            response_metadata=data.get("response_metadata"),
            id=data.get("id"),
            usage_metadata=data.get("usage_metadata"),
        )
    else:
        raise ValueError("Unsupported message type")


def deserialize_chat_history(data: List[Dict[str, Any]]) -> List:
    """Convert a list of dictionaries back into a list of message objects."""
    return [deserialize_message(message_data) for message_data in data]


def get_chat_history(session_id: str):
    """Retrieve chat history for the given session ID, or initialize it if not present."""
    if hasattr(g, "chat_history"):
        return g.chat_history

    session_data = get_session(session_id)

    if "chat_history" not in session_data:
        g.chat_history = ChatMessageHistory()
        # save_chat_history_to_db(session_id, g.chat_history)
        return g.chat_history

    chat_history = deserialize_chat_history(session_data["chat_history"])
    chat_object = ChatMessageHistory()
    chat_object.add_messages(chat_history)
    g.chat_history = chat_object
    return g.chat_history


def cut_chat_history(messages, max_size=10):

    if max_size > 0 and len(messages) > max_size:
        messages = messages[-max_size:]

    return messages


def format_error(source, e):

    if not hasattr(e, "body"):
        return 500, str(e)
    if source == "openai":
        return format_openai_error(e)
    if source == "anthropic":
        return format_anthropic_error(e)
    if source == "cohere":
        return format_cohere_error(e)
    else:
        return 500, str(e)


def format_openai_error(e):

    if e.body is not None:
        if "message" in e.body:
            response_message = e.body["message"]
        elif "result" in e.body:
            response_message = e.body["result"]["message"]
        else:
            response_message = "Unknown error"
    else:
        response_message = "Unknown error"

    if hasattr(e, "status_code"):
        status_code = e.status_code
    else:
        status_code = 500

    return status_code, response_message


def format_anthropic_error(e):

    if e.body is not None:
        if "error" in e.body and "message" in e.body["error"]:
            response_message = e.body["error"]["message"]
        else:
            response_message = "Unknown error"
    else:
        response_message = "Unknown error"

    if hasattr(e, "status_code"):
        status_code = e.status_code
    else:
        status_code = 500

    return status_code, response_message


def format_cohere_error(e):

    if e.body is not None:
        if "message" in e.body:
            response_message = e.body["message"]
        else:
            response_message = "Unknown error"
    else:
        response_message = "Unknown error"

    if hasattr(e, "status_code"):
        status_code = e.status_code
    else:
        status_code = 500

    return status_code, response_message
