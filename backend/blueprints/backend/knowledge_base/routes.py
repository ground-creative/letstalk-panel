from apiflask import APIBlueprint
from models.Response import Response as ApiResponse
from utils.views import AuthenticatedMethodView
from utils.files import read_files_in_folder
from flask import current_app as app

backend_knowledge_base_bp = APIBlueprint(
    "backend_knowledge_base_blueprint",
    __name__,
)


class KnowledgeBase(AuthenticatedMethodView):

    @backend_knowledge_base_bp.doc(tags=["Knowledge Base"], security="bearerAuth")
    # @backend_knowledge_base_bp.output(ChatAssistantResponse)
    def get(self, workspaceID):
        """Get Knowledge Base Files"""

        knowledge_base_path = app.config.get("KNOWLEDGE_BASE_PATH") + "/" + workspaceID
        payload_response = ApiResponse.payload_v2(
            200,
            "Files retrieved successfully!",
            read_files_in_folder(knowledge_base_path),
        )
        return ApiResponse.output(payload_response)


backend_knowledge_base_bp.add_url_rule(
    "/<string:workspaceID>/knowledge-base",
    view_func=KnowledgeBase.as_view("knowledge_base"),
)
