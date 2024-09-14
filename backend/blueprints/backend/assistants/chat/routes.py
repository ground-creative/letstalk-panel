from apiflask import APIBlueprint
from models.Response import Response as ApiResponse
from utils.views import AuthenticatedMethodView
from services.chat_assistant_service import ChatAssistantService
from blueprints.api.v2.models.ChatAssistants import ChatAssistantModel
from blueprints.api.v2.schemas.ChatAssistants import (
    ChatAssistantCreate,
    ChatAssistantResponse,
)

backend_chat_assistants_bp = APIBlueprint(
    "backend_chat_assistants_blueprint",
    __name__,
)


class ChatAssistants(AuthenticatedMethodView):

    @backend_chat_assistants_bp.doc(tags=["Chat Assistants"], security="bearerAuth")
    @backend_chat_assistants_bp.output(ChatAssistantResponse)
    def get(self, workspaceID):
        """Get Chat Assistants"""

        records = ChatAssistantModel.get({"workspace_sid": workspaceID})
        payload = ChatAssistantModel.to_dict(records) if len(records) > 0 else []
        payload_response = ApiResponse.payload_v2(
            200,
            "Records retrieved successfully!",
            ChatAssistantResponse(many=True).dump(payload),
        )
        return ApiResponse.output(payload_response)

    @backend_chat_assistants_bp.input(ChatAssistantCreate.Schema, arg_name="record")
    @backend_chat_assistants_bp.doc(tags=["Chat Assistants"], security="bearerAuth")
    def post(self, workspaceID, record: ChatAssistantCreate):
        """Create Chat Assistant"""
        service = ChatAssistantService(workspaceID, record)
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


backend_chat_assistants_bp.add_url_rule(
    "/<string:workspaceID>/assistants/chat",
    view_func=ChatAssistants.as_view("chat_assistants"),
)


class ChatAssistant(AuthenticatedMethodView):

    @backend_chat_assistants_bp.doc(tags=["Chat Assistants"], security="bearerAuth")
    @backend_chat_assistants_bp.output(ChatAssistantResponse)
    def get(self, workspaceID, assistantID):
        """Get Chat Assistant"""
        record = ChatAssistantModel.get(assistantID)
        if not record:
            payload_response = ApiResponse.payload_v2(404, "Record not found!", {})
        else:
            payload = ChatAssistantModel.toDict(record)
            payload_response = ApiResponse.payload_v2(
                200,
                "Record retrieved successfully!",
                ChatAssistantResponse().dump(payload),
            )
        return ApiResponse.output(payload_response)

    @backend_chat_assistants_bp.input(ChatAssistantCreate.Schema, arg_name="record")
    @backend_chat_assistants_bp.doc(tags=["Chat Assistants"], security="bearerAuth")
    def patch(self, workspaceID, assistantID, record: ChatAssistantCreate):
        """Update Chat Assistant"""
        service = ChatAssistantService(workspaceID, record)
        validation_error = service.validate_knowledge_base_files()

        if validation_error:
            return ApiResponse.output(validation_error)

        rebuild_knowledge_base = service.handle_knowledge_base_and_provider(assistantID)

        if len(record.model.knowledge_base) > 0 and rebuild_knowledge_base:
            try:
                service.process_embeddings(assistantID)
            except Exception as e:
                payload_response = ApiResponse.payload_v2(500, "Internal server error")
                return ApiResponse.output(payload_response)

        service.update_chat_assistant(assistantID)
        payload_response = ApiResponse.payload_v2(200, "Record updated successfully!")
        return ApiResponse.output(payload_response)

    @backend_chat_assistants_bp.doc(tags=["Chat Assistants"], security="bearerAuth")
    def delete(self, workspaceID, assistantID):
        """Delete Chat Assistant"""
        record = ChatAssistantModel.get(assistantID)

        if not record:
            payload_response = ApiResponse.payload_v2(404, "Record not found!")
            return ApiResponse.output(payload_response)

        service = ChatAssistantService(workspaceID)
        service.delete_chat_assistant(assistantID)
        payload_response = ApiResponse.payload_v2(
            200, "Record deleted successfully!", {}
        )
        return ApiResponse.output(payload_response)


backend_chat_assistants_bp.add_url_rule(
    "/<string:workspaceID>/assistants/chat/<assistantID>",
    view_func=ChatAssistant.as_view("chat_assistant"),
)
