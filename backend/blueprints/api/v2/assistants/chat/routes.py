from apiflask import APIBlueprint
from flask import g
from models.Response import Response as ApiResponse
from utils.views import APIAuthenticatedMethodView
from blueprints.api.v2.models.ChatAssistants import ChatAssistantModel
from blueprints.api.v2.models.LanguageModels import LanguageModel
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
        record.type = "chat"
        record.workspace_sid = g.api_key.workspace_sid
        assistant_id = ChatAssistantModel.insert(record)
        if assistant_id:

            record.model.assistant_sid = assistant_id
            insert_id = LanguageModel.insert(record.model)
            record.model_config_sid = insert_id
            ChatAssistantModel.update(assistant_id, record)
            payload_response = ApiResponse.payload_v2(
                200, "Record created successfully!", {"sid": insert_id}
            )
        else:
            payload_response = ApiResponse.payload_v2(500, "Internal server error")
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
        else:
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
        ChatAssistantModel.update(assistantID, record)
        assistant = ChatAssistantModel.get(assistantID)
        insert_id = LanguageModel.update(assistant.model_config_sid, record.model)
        payload_response = ApiResponse.payload_v2(
            200, "Record updated successfully!", {"sid": insert_id}
        )
        return ApiResponse.output(payload_response)

    @api_v2_chat_bp.doc(tags=["Chat Assistants"], security="ApiKeyAuth")
    def delete(self, assistantID):
        """Delete Chat Assistant"""
        ChatAssistantModel.delete({"sid": assistantID})
        payload_response = ApiResponse.payload_v2(
            200, "Record deleted successfully!", {}
        )
        return ApiResponse.output(payload_response)


api_v2_chat_bp.add_url_rule(
    "/<assistantID>", view_func=ChatAssistant.as_view("chat_assistant")
)
