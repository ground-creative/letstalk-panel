# services/knowledge_base_service.py
import os
from flask import current_app as app
from werkzeug.utils import secure_filename
from blueprints.api.v2.models.ChatAssistants import ChatAssistantModel
from blueprints.api.v2.models.LanguageModels import LanguageModel
from utils.files import generate_unique_filename, read_files_in_folder


class KnowledgeBaseService:
    def __init__(self, workspace_id):
        self.workspace_id = workspace_id
        self.knowledge_base_path = os.path.join(
            app.config.get("KNOWLEDGE_BASE_PATH"), workspace_id
        )

    def get_files(self):
        return read_files_in_folder(self.knowledge_base_path)

    def save_file(self, file):
        filename = secure_filename(file.filename)
        unique_filename = generate_unique_filename(self.knowledge_base_path, filename)
        file.save(os.path.join(self.knowledge_base_path, unique_filename))
        return unique_filename

    def delete_file(self, filename):
        file_to_delete = os.path.join(self.knowledge_base_path, filename)
        if os.path.isfile(file_to_delete):
            os.remove(file_to_delete)

    def is_file_in_use(self, filename):
        """
        Check if the given file is being used by any assistants.
        Returns a list of assistant IDs that are using the file.
        """
        files_error = []
        records = ChatAssistantModel.get({"workspace_sid": self.workspace_id})

        for record in records:
            model = LanguageModel.get(record.model_config_sid)
            model_object = LanguageModel.to_dict(model)

            if filename in model_object.get("knowledge_base", []):
                files_error.append(record.sid)

        return files_error
