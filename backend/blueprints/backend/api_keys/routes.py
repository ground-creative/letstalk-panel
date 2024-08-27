from apiflask import APIBlueprint
from models.Response import Response as ApiResponse
from utils.views import AuthenticatedMethodView
from blueprints.backend.models.ApiKeys import ApiKeyModel
from blueprints.backend.schemas.ApiKeys import (
    ApiKeyCreate,
    ApiKeyEdit,
    ApiKeyResponse,
)

backend_api_keys_bp = APIBlueprint("api_v2_api_keys_blueprint", __name__)


class ApiKeys(AuthenticatedMethodView):

    @backend_api_keys_bp.doc(tags=["API Keys"], security="bearerAuth")
    @backend_api_keys_bp.output(ApiKeyResponse)
    def get(self, workspaceID):
        records = ApiKeyModel.get({"workspace_sid": workspaceID})
        payload = ApiKeyModel.toDict(records)
        payload_response = ApiResponse.payload_v2(
            200,
            "Records retrieved successfully!",
            ApiKeyResponse(many=True).dump(payload),
        )
        return ApiResponse.output(payload_response)

    @backend_api_keys_bp.input(ApiKeyCreate.Schema, arg_name="record")
    @backend_api_keys_bp.doc(tags=["API Keys"], security="bearerAuth")
    def post(self, workspaceID, record: ApiKeyCreate):
        """Create ApiKey"""
        record.workspace_sid = workspaceID
        insert_id = ApiKeyModel.insert(record)
        payload_response = ApiResponse.payload_v2(
            200, "Record created successfully!", {"sid": insert_id}
        )
        return ApiResponse.output(payload_response, 200)


backend_api_keys_bp.add_url_rule(
    "/<string:workspaceID>/api-keys", view_func=ApiKeys.as_view("api_keys")
)


class ApiKey(AuthenticatedMethodView):

    @backend_api_keys_bp.doc(tags=["API Keys"], security="bearerAuth")
    @backend_api_keys_bp.output(ApiKeyResponse)
    def get(self, workspaceID, apiKeyID):
        record = ApiKeyModel.get(apiKeyID)
        if not record:
            payload_response = ApiResponse.payload_v2(404, "Record not found!", {})
        else:
            payload = ApiKeyModel.toDict(record)
            payload_response = ApiResponse.payload_v2(
                200,
                "Record retrieved successfully!",
                ApiKeyResponse().dump(payload),
            )
        return ApiResponse.output(payload_response)

    @backend_api_keys_bp.input(ApiKeyEdit.Schema, arg_name="record")
    @backend_api_keys_bp.doc(tags=["API Keys"], security="bearerAuth")
    def patch(self, workspaceID, apiKeyID, record: ApiKeyEdit):
        """Update ApiKey"""
        ApiKeyModel.update(apiKeyID, record)
        payload_response = ApiResponse.payload_v2(
            200, "Record updated successfully!", {}
        )
        return ApiResponse.output(payload_response)

    @backend_api_keys_bp.doc(tags=["API Keys"], security="bearerAuth")
    def delete(self, workspaceID, apiKeyID):
        ApiKeyModel.delete({"sid": apiKeyID})
        payload_response = ApiResponse.payload_v2(
            200, "Record deleted successfully!", {}
        )
        return ApiResponse.output(payload_response)


backend_api_keys_bp.add_url_rule(
    "/<string:workspaceID>/api-keys/<apiKeyID>", view_func=ApiKey.as_view("api_key")
)
