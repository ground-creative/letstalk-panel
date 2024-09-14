from apiflask import APIBlueprint
from flask import current_app as app, g
from models.Response import Response as ApiResponse
from utils.views import APIAuthenticatedMethodView
from marshmallow import fields
from services.knowledge_base_service import KnowledgeBaseService
from blueprints.api.v2.schemas.KnowledgeBase import (
    KnowledgeBaseFile,
    KnowledgeBaseResponse,
)

api_v2_knowledge_base_bp = APIBlueprint(
    "api_v2_knowledge_base_blueprint",
    __name__,
)


class KnowledgeBase(APIAuthenticatedMethodView):

    @api_v2_knowledge_base_bp.doc(tags=["Knowledge Base"], security="ApiKeyAuth")
    @api_v2_knowledge_base_bp.output(KnowledgeBaseResponse(many=True))
    def get(self):
        """Get Knowledge Base Files"""

        knowledge_base_service = KnowledgeBaseService(g.api_key.workspace_sid)
        data = knowledge_base_service.get_files()
        payload_response = ApiResponse.payload_v2(
            200,
            "Files retrieved successfully!",
            KnowledgeBaseResponse(many=True).dump(data),
        )
        return ApiResponse.output(payload_response)

    @api_v2_knowledge_base_bp.doc(tags=["Knowledge Base"], security="ApiKeyAuth")
    @api_v2_knowledge_base_bp.input(KnowledgeBaseFile, location="files")
    def post(self, files_data):
        """Post Knowledge Base File"""

        knowledge_base_service = KnowledgeBaseService(g.api_key.workspace_sid)
        try:
            file = files_data["filename"]
            knowledge_base_service.save_file(file)
            payload_response = ApiResponse.payload_v2(
                200,
                "File added successfully!",
            )
            return ApiResponse.output(payload_response)
        except Exception as e:
            app.logger.error(f"File upload error: {str(e)}")
            payload_response = ApiResponse.payload_v2(500, "Internal Server Error!")
            return ApiResponse.output(payload_response)

    @api_v2_knowledge_base_bp.doc(tags=["Knowledge Base"], security="ApiKeyAuth")
    @api_v2_knowledge_base_bp.input(
        {"filename": fields.Str(required=True)}, location="query"
    )
    def delete(self, query_data):
        """Delete Knowledge Base File"""
        knowledge_base_service = KnowledgeBaseService(g.api_key.workspace_sid)

        if not any(
            query_data["filename"] == file["filename"]
            for file in knowledge_base_service.get_files()
        ):
            payload_response = ApiResponse.payload_v2(404, "File not found!")
            return ApiResponse.output(payload_response)

        files_error = knowledge_base_service.is_file_in_use(query_data["filename"])

        if files_error:
            payload_response = ApiResponse.payload_v2(
                409,
                "Cannot delete file, it is being used by at least 1 assistant!",
                files_error,
            )
            return ApiResponse.output(payload_response)

        knowledge_base_service.delete_file(query_data["filename"])
        payload_response = ApiResponse.payload_v2(200, "Record deleted successfully!")
        return ApiResponse.output(payload_response)


api_v2_knowledge_base_bp.add_url_rule(
    "/",
    view_func=KnowledgeBase.as_view("knowledge_base"),
)
