# blueprints/api/v2/completions.py

from apiflask import APIBlueprint
from flask import g, request, render_template
from decorators.Session import check_session_param
from models.Response import Response as ApiResponse
from services.completion_service import CompletionService
from blueprints.api.v2.models.ChatAssistants import ChatAssistantModel
from blueprints.api.v2.schemas.Completions import (
    CompletionCreate,
    CompletionCreateSession,
    CompletionsResponse,
)


embed_chat_bp = APIBlueprint("embed_chat_bp", __name__)


@embed_chat_bp.route("/dante-embed")
def embed_page():

    return render_template("chat/dante_test_bubble.html")


@embed_chat_bp.route("/dante-iframe")
def embed_iframe_page():

    return render_template("chat/dante_test_iframe.html")


@embed_chat_bp.route("/chat/<embed_sid>", methods=["GET"])
@embed_chat_bp.route("/chat/<embed_sid>/", methods=["GET"])
def chat(embed_sid):

    records = ChatAssistantModel.get({"embed_sid": embed_sid})
    if len(records) == 0:
        return render_template("404.html")

    embed_sid = records[0].embed_sid
    theme = request.args.get("theme", "light")
    placeholder_text = request.args.get("placeholder_text", "Type a message")
    start_message = request.args.get("start_message", "Hi, how can I help you?")
    error_message = request.args.get(
        "error_message",
        "I am very sorry, but the network seems to be having problems at the moment.",
    )
    return render_template(
        "chat/main.html",
        theme=theme,
        placeholder_text=placeholder_text,
        start_message=start_message,
        embed_sid=embed_sid,
        error_message=error_message,
    )


@embed_chat_bp.route("/embed/iframe/<embed_sid>", methods=["GET"])
@embed_chat_bp.route("/embed/iframe/<embed_sid>/", methods=["GET"])
def embedded_chat(embed_sid):

    records = ChatAssistantModel.get({"embed_sid": embed_sid})
    if len(records) == 0:
        return render_template("404.html")

    embed_sid = records[0].embed_sid
    theme = request.args.get("theme", "light")
    placeholder_text = request.args.get("placeholder_text", "Type a message")
    start_message = request.args.get("start_message", "Hi, how can I help you?")
    error_message = request.args.get(
        "error_message",
        "I am very sorry, but the network seems to be having problems at the moment.",
    )
    colors = "dark-colors.css" if theme == "dark" else "light-colors.css"
    return render_template(
        "chat/chat.html",
        colors=colors,
        placeholder_text=placeholder_text,
        start_message=start_message,
        embed_sid=embed_sid,
        error_message=error_message,
    )


@embed_chat_bp.route("/embed/completions/<embed_sid>", methods=["POST"])
@embed_chat_bp.route("/embed/completions/<embed_sid>/", methods=["POST"])
@embed_chat_bp.input(CompletionCreate.Schema, arg_name="data")
@embed_chat_bp.input(CompletionCreateSession, location="headers", arg_name="headers")
@check_session_param
@embed_chat_bp.output(CompletionsResponse)  # not realy used here
def completion(embed_sid, data: CompletionCreate, headers: CompletionCreateSession):

    records = ChatAssistantModel.get({"embed_sid": embed_sid})
    if len(records) == 0:
        payload_response = ApiResponse.payload_v2(404, "Record not found!")

        return ApiResponse.output(payload_response)

    service = CompletionService(
        workspace_sid=records[0].workspace_sid, session_id=g.session_id
    )
    status_code, response = service.process_completion(records[0].sid, data)

    if status_code != 200:
        payload_response = ApiResponse.payload_v2(status_code, response)
    else:
        payload_response = ApiResponse.payload_v2(
            200, "Completion request was successful!", response
        )

    return ApiResponse.output(payload_response)
