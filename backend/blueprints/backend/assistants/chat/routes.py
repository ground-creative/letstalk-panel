from apiflask import APIBlueprint
from flask import current_app as app, g
from models.Response import Response as ApiResponse
from utils.views import AuthenticatedMethodView
from utils.vector_store import build_vector_store, delete_vector_store
from utils.llm import init_embeddings, format_openai_error
from utils.files import check_files_in_folder
from blueprints.api.v2.models.ChatAssistants import ChatAssistantModel
from blueprints.api.v2.models.LanguageModels import LanguageModel
from blueprints.api.v2.models.Providers import ProviderModel
from blueprints.api.v2.schemas.ChatAssistants import (
    ChatAssistantCreate,
    ChatAssistantResponse,
)


backend_chat_assistants_bp = APIBlueprint(
    "backend_chat_assistants_blueprint",
    __name__,
    # tag={"name": "Workspaces", "description": "blah..."}, NOT WORKING
)


class ChatAssistants(AuthenticatedMethodView):

    @backend_chat_assistants_bp.doc(tags=["Chat Assistants"], security="bearerAuth")
    @backend_chat_assistants_bp.output(ChatAssistantResponse)
    def get(self, workspaceID):
        """Get Chat Assistants"""
        records = ChatAssistantModel.get({"workspace_sid": workspaceID})
        payload = ChatAssistantModel.to_dict(records) if len(records) > 0 else []
        # print(payload)
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

        if len(record.model.knowledge_base) > 0:
            knowledge_base_folder = (
                f"{app.config.get('KNOWLEDGE_BASE_PATH')}/{workspaceID}"
            )
            files_error = check_files_in_folder(
                knowledge_base_folder, record.model.knowledge_base
            )
            if files_error:
                payload_response = ApiResponse.payload_v2(
                    422, f"File {files_error} not found!"
                )
                return ApiResponse.output(payload_response)

        record.type = "chat"
        record.workspace_sid = workspaceID
        assistant_id = ChatAssistantModel.insert(record)

        if assistant_id:

            if len(record.model.knowledge_base) > 0:
                try:
                    provider = ProviderModel.get(record.model.provider_sid)
                    created_args = {}
                    created_args["api_key"] = provider.api_key
                    created_args["base_url"] = provider.address

                    if provider.source == "ollama":
                        created_args["model"] = record.model.model
                        del created_args["api_key"]

                    result, embeddings = init_embeddings(
                        provider.source, **created_args
                    )
                    if not result:
                        if provider.source == "openai":
                            error = format_openai_error(e)
                            error_code = 500
                        else:
                            error = str(e)
                            error_code = 500

                        app.logger.error(
                            f"Exception occured:  {error}",
                            exc_info=app.config.get("DEBUG_APP"),
                        )
                        payload_response = ApiResponse.payload_v2(
                            error_code,
                            error,
                        )
                        return ApiResponse.output(
                            payload_response, cookies=[{"session_id": g.session_id}]
                        )

                    build_vector_store(
                        workspaceID,
                        assistant_id,
                        record.model.knowledge_base,
                        embeddings,
                    )
                except Exception as e:
                    ChatAssistantModel.delete(assistant_id)
                    app.logger.error(f"Error: {str(e)}")
                    payload_response = ApiResponse.payload_v2(
                        500, "Internal server error"
                    )
                    return ApiResponse.output(payload_response)

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

        assistant = ChatAssistantModel.get(assistantID)
        model = LanguageModel.get(assistant.model_config_sid)
        provider = ProviderModel.get(record.model.provider_sid)

        if len(model.knowledge_base) > 0:
            if record.model.provider_sid != model.provider_sid:
                old_provider = ProviderModel.get(model.provider_sid)
                if provider.source != old_provider.source:
                    delete_vector_store(workspaceID, assistantID)
            elif (
                model.knowledge_base != record.model.knowledge_base
                and len(model.knowledge_base) > 0
            ):
                delete_vector_store(workspaceID, assistantID)
            elif provider.source == "ollama" and record.model.model != model.model:
                delete_vector_store(workspaceID, assistantID)

        if len(record.model.knowledge_base) > 0:
            try:
                created_args = {}
                created_args["api_key"] = provider.api_key
                created_args["base_url"] = provider.address

                if provider.source == "ollama":
                    created_args["model"] = record.model.model
                    del created_args["api_key"]

                result, embeddings = init_embeddings(provider.source, **created_args)
                if not result:
                    if provider.source == "openai":
                        error = format_openai_error(e)
                        error_code = 500
                    else:
                        error = str(e)
                        error_code = 500

                    app.logger.error(
                        f"Exception occured:  {error}",
                        exc_info=app.config.get("DEBUG_APP"),
                    )
                    payload_response = ApiResponse.payload_v2(
                        error_code,
                        error,
                    )
                    return ApiResponse.output(
                        payload_response, cookies=[{"session_id": g.session_id}]
                    )

                build_vector_store(
                    workspaceID,
                    assistantID,
                    record.model.knowledge_base,
                    embeddings,
                )
            except Exception as e:
                ChatAssistantModel.delete(assistantID)
                app.logger.error(f"Error: {str(e)}")
                payload_response = ApiResponse.payload_v2(500, "Internal server error")
                return ApiResponse.output(payload_response)

        ChatAssistantModel.update(assistantID, record)
        # assistant = ChatAssistantModel.get(assistantID)
        LanguageModel.update(assistant.model_config_sid, record.model)
        payload_response = ApiResponse.payload_v2(200, "Record updated successfully!")
        return ApiResponse.output(payload_response)

    @backend_chat_assistants_bp.doc(tags=["Chat Assistants"], security="bearerAuth")
    def delete(self, workspaceID, assistantID):
        """Delete Chat Assistant"""
        ChatAssistantModel.delete({"sid": assistantID})
        delete_vector_store(workspaceID, assistantID)
        LanguageModel.delete({"assistant_sid": assistantID})
        payload_response = ApiResponse.payload_v2(
            200, "Record deleted successfully!", {}
        )
        return ApiResponse.output(payload_response)


backend_chat_assistants_bp.add_url_rule(
    "/<string:workspaceID>/assistants/chat/<assistantID>",
    view_func=ChatAssistant.as_view("chat_assistant"),
)
