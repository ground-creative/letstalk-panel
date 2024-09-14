from apiflask import APIBlueprint
from flask import g
from models.Response import Response as ApiResponse
from utils.views import APIAuthenticatedMethodView
from services.chat_assistant_service import ChatAssistantService
from blueprints.api.v2.models.ChatAssistants import ChatAssistantModel
from blueprints.api.v2.schemas.ChatAssistants import (
    ChatAssistantCreate,
    ChatAssistantResponse,
)


api_v2_chat_bp = APIBlueprint("api_v2_chat_blueprint", __name__)


class ChatAssistants(APIAuthenticatedMethodView):

    @api_v2_chat_bp.doc(tags=["Chat Assistants"], security="ApiKeyAuth")
    @api_v2_chat_bp.output(ChatAssistantResponse)
    def get(self):
        """Get Chat Assistants"""

        records = ChatAssistantModel.get({"workspace_sid": g.api_key.workspace_sid})
        payload = ChatAssistantModel.to_dict(records) if len(records) > 0 else []
        payload_response = ApiResponse.payload_v2(
            200,
            "Records retrieved successfully!",
            ChatAssistantResponse(many=True).dump(payload),
        )
        return ApiResponse.output(payload_response)

    @api_v2_chat_bp.input(ChatAssistantCreate.Schema, arg_name="record")
    @api_v2_chat_bp.doc(tags=["Chat Assistants"], security="ApiKeyAuth")
    def post(self, record: ChatAssistantCreate):
        """Create Chat Assistant"""
        service = ChatAssistantService(g.api_key.workspace_sid, record)
        validation_error = service.validate_knowledge_base_files()

        if validation_error:
            return ApiResponse.output(validation_error)

        assistant_id = service.create_chat_assistant()

        if not assistant_id:
            payload_response = ApiResponse.payload_v2(500, "Internal server error")
            return ApiResponse.output(payload_response)

        if len(record.model.knowledge_base) > 0:
            try:
                service.process_embeddings(assistant_id)
            except Exception as e:
                payload_response = ApiResponse.payload_v2(500, str(e))
                return ApiResponse.output(payload_response)

        insert_id = service.insert_language_model(assistant_id)
        payload_response = ApiResponse.payload_v2(
            200, "Record created successfully!", {"sid": insert_id}
        )
        return ApiResponse.output(payload_response)


api_v2_chat_bp.add_url_rule("/", view_func=ChatAssistants.as_view("chat_assistants"))


class ChatAssistant(APIAuthenticatedMethodView):

    @api_v2_chat_bp.doc(tags=["Chat Assistants"], security="ApiKeyAuth")
    @api_v2_chat_bp.output(ChatAssistantResponse)
    def get(self, assistantID):
        """Get Chat Assistant"""
        record = ChatAssistantModel.get(assistantID)

        if not record:
            payload_response = ApiResponse.payload_v2(404, "Record not found!", {})
            return ApiResponse.output(payload_response)

        payload = ChatAssistantModel.toDict(record)
        payload_response = ApiResponse.payload_v2(
            200,
            "Record retrieved successfully!",
            ChatAssistantResponse().dump(payload),
        )
        return ApiResponse.output(payload_response)

    @api_v2_chat_bp.input(ChatAssistantCreate.Schema, arg_name="record")
    @api_v2_chat_bp.doc(tags=["Chat Assistants"], security="ApiKeyAuth")
    def patch(self, assistantID, record: ChatAssistantCreate):
        """Update Chat Assistant"""
        service = ChatAssistantService(g.api_key.workspace_sid, record)
        validation_error = service.validate_knowledge_base_files()

        if validation_error:
            return ApiResponse.output(validation_error)

        service.handle_knowledge_base_and_provider(assistantID)

        if len(record.model.knowledge_base) > 0:
            try:
                service.process_embeddings(assistantID)
            except Exception as e:
                payload_response = ApiResponse.payload_v2(500, "Internal server error")
                return ApiResponse.output(payload_response)

        service.update_chat_assistant(assistantID)
        payload_response = ApiResponse.payload_v2(200, "Record updated successfully!")
        return ApiResponse.output(payload_response)

    @api_v2_chat_bp.doc(tags=["Chat Assistants"], security="ApiKeyAuth")
    def delete(self, assistantID):
        """Delete Chat Assistant"""
        record = ChatAssistantModel.get(assistantID)

        if not record:
            payload_response = ApiResponse.payload_v2(404, "Record not found!")
            return ApiResponse.output(payload_response)

        service = ChatAssistantService(g.api_key.workspace_sid)
        service.delete_chat_assistant(assistantID)
        payload_response = ApiResponse.payload_v2(
            200, "Record deleted successfully!", {}
        )
        return ApiResponse.output(payload_response)


api_v2_chat_bp.add_url_rule(
    "/<assistantID>", view_func=ChatAssistant.as_view("chat_assistant")
)
