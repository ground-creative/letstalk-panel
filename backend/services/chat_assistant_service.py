# services/chat_assistant_service.py
import os
from flask import current_app as app
from models.Response import Response as ApiResponse
from utils.vector_store import build_vector_store, delete_vector_store
from utils.llm import init_embeddings, format_openai_error
from utils.files import check_files_in_folder
from blueprints.api.v2.models.ChatAssistants import ChatAssistantModel
from blueprints.api.v2.models.LanguageModels import LanguageModel
from blueprints.api.v2.models.Providers import ProviderModel


class ChatAssistantService:
    def __init__(self, workspace_id, record=None):
        self.workspace_id = workspace_id
        self.record = record

    def validate_knowledge_base_files(self):
        """Validate if knowledge base files exist in the folder"""
        if len(self.record.model.knowledge_base) > 0:
            knowledge_base_folder = os.path.join(
                app.config.get("KNOWLEDGE_BASE_PATH"), self.workspace_id
            )
            files_error = check_files_in_folder(
                knowledge_base_folder, self.record.model.knowledge_base
            )
            if files_error:
                return ApiResponse.payload_v2(422, f"File {files_error} not found!")

        return None

    def create_chat_assistant(self):
        """Insert chat assistant into the database"""
        self.record.type = "chat"
        self.record.workspace_sid = self.workspace_id
        assistant_id = ChatAssistantModel.insert(self.record)
        return assistant_id

    def update_chat_assistant(self, assistant_id):
        """Update chat assistant in the database"""
        ChatAssistantModel.update(assistant_id, self.record)
        assistant = ChatAssistantModel.get(assistant_id)
        LanguageModel.update(assistant.model_config_sid, self.record.model)

    def delete_chat_assistant(self, assistant_id):
        """Delete chat assistant from the database"""
        delete_vector_store(self.workspace_id, assistant_id)
        ChatAssistantModel.delete(assistant_id)
        LanguageModel.delete({"assistant_sid": assistant_id})

    def process_embeddings(self, assistant_id):
        """Initialize and process embeddings based on the provider"""
        try:
            provider = ProviderModel.get(self.record.model.provider_sid)
            created_args = {"api_key": provider.api_key, "base_url": provider.address}

            if provider.source == "ollama":
                created_args["model"] = self.record.model.model
                del created_args["api_key"]
            elif provider.source == "cohere":
                created_args["model"] = "embed-english-v3.0"
                created_args["cohere_api_key"] = created_args["api_key"]
                del created_args["api_key"]

            result, embeddings = init_embeddings(provider.source, **created_args)

            if not result:
                if provider.source == "openai":
                    error = format_openai_error(e)
                else:
                    error = str(e)
                raise Exception(error)

            build_vector_store(
                self.workspace_id,
                assistant_id,
                self.record.model.knowledge_base,
                embeddings,
            )
            return True

        except Exception as e:
            ChatAssistantModel.delete(assistant_id)
            if provider.source == "openai":
                error = format_openai_error(e)
            else:
                error = str(e)
            raise Exception(error)

    def insert_language_model(self, assistant_id):
        """Insert the language model and update the assistant"""
        self.record.model.assistant_sid = assistant_id
        insert_id = LanguageModel.insert(self.record.model)
        self.record.model_config_sid = insert_id
        ChatAssistantModel.update(assistant_id, self.record)
        return insert_id

    def handle_knowledge_base_and_provider(self, assistant_id):
        """Handle updates related to knowledge base and provider"""
        assistant = ChatAssistantModel.get(assistant_id)
        model = LanguageModel.get(assistant.model_config_sid)
        model_dict = model.to_dict(model)
        provider = ProviderModel.get(self.record.model.provider_sid)

        if len(model_dict["knowledge_base"]) > 0:
            if self.record.model.provider_sid != model.provider_sid:
                old_provider = ProviderModel.get(model.provider_sid)
                if provider.source != old_provider.source:
                    delete_vector_store(self.workspace_id, assistant_id)
                    return True
            elif (
                model_dict["knowledge_base"] != self.record.model.knowledge_base
                and len(model_dict["knowledge_base"]) > 0
            ):
                delete_vector_store(self.workspace_id, assistant_id)
                return True
            elif provider.source == "ollama" and self.record.model.model != model.model:
                delete_vector_store(self.workspace_id, assistant_id)
                return True

        return False
