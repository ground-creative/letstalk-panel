# blueprints/api/v2/completions.py

from apiflask import APIBlueprint
from flask import g
from decorators.Session import check_session_param
from models.Response import Response as ApiResponse
from utils.views import APIAuthenticatedMethodView
from services.completion_service import CompletionService
from blueprints.api.v2.schemas.Completions import (
    CompletionCreate,
    CompletionCreateSession,
    CompletionsResponse,
)


api_v2_completions_bp = APIBlueprint("api_v2_completions_bp", __name__)


class Completion(APIAuthenticatedMethodView):

    @api_v2_completions_bp.doc(tags=["Completions"], security="ApiKeyAuth")
    @api_v2_completions_bp.input(CompletionCreate.Schema, arg_name="data")
    @api_v2_completions_bp.input(
        CompletionCreateSession, location="headers", arg_name="headers"
    )
    @check_session_param
    @api_v2_completions_bp.output(CompletionsResponse)
    def post(
        self, assistantID, data: CompletionCreate, headers: CompletionCreateSession
    ):
        service = CompletionService(
            workspace_sid=g.api_key.workspace_sid, session_id=g.session_id
        )
        status_code, response = service.process_completion(assistantID, data)

        if status_code != 200:
            payload_response = ApiResponse.payload_v2(status_code, response)
        else:
            payload_response = ApiResponse.payload_v2(
                200, "Completion request was successful!", response
            )

        return ApiResponse.output(payload_response)


api_v2_completions_bp.add_url_rule(
    "/completions/<assistantID>", view_func=Completion.as_view("completion")
)
