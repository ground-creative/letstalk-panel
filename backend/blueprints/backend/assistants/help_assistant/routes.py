# blueprints/backend/assistants/help_assistant.py

from apiflask import APIBlueprint
from flask import g
from decorators.Session import check_session_param
from models.Response import Response as ApiResponse
from utils.views import AuthenticatedMethodView
from services.completion_service import CompletionService
from blueprints.api.v2.schemas.Completions import (
    CompletionCreateSession,
    CompletionsResponse,
)
from blueprints.backend.schemas.HelpAssistant import (
    HelpAssistant,
)
from blueprints.api.v2.models.ChatAssistants import ChatAssistantModel

backend_help_assistant_bp = APIBlueprint("backend_help_assistant_bp", __name__)


class HelpAssistant(AuthenticatedMethodView):

    @backend_help_assistant_bp.input(
        CompletionCreateSession, location="headers", arg_name="headers"
    )
    @backend_help_assistant_bp.input(HelpAssistant.Schema, arg_name="data")
    @backend_help_assistant_bp.doc(tags=["Help Assistant"], security="bearerAuth")
    @check_session_param
    @backend_help_assistant_bp.output(CompletionsResponse)
    def post(self, data: HelpAssistant, headers: CompletionCreateSession):
        """Help Assistant Completion

        Completion request for the help assistant"""

        assistant_id = "5pustl2E4p"

        record = ChatAssistantModel.get(assistant_id)

        service = CompletionService(
            workspace_sid=record.workspace_sid, session_id=g.session_id
        )
        status_code, response = service.process_completion(assistant_id, data)

        if status_code != 200:
            payload_response = ApiResponse.payload_v2(status_code, response)
        else:
            payload_response = ApiResponse.payload_v2(
                200, "Completion request was successful!", response
            )

        return ApiResponse.output(payload_response)


backend_help_assistant_bp.add_url_rule(
    "/", view_func=HelpAssistant.as_view("help_assistant")
)
