from apiflask import APIBlueprint
from models.Response import Response as ApiResponse
from utils.views import AuthenticatedMethodView
from blueprints.api.v2.models.Providers import ProviderModel
from blueprints.api.v2.schemas.Providers import (
    ProviderCreate,
    ProviderResponse,
)

backend_providers_bp = APIBlueprint("providers_blueprint", __name__)


class Providers(AuthenticatedMethodView):

    @backend_providers_bp.doc(tags=["Providers"], security="bearerAuth")
    @backend_providers_bp.output(ProviderResponse)
    def get(self, workspaceID):

        records = ProviderModel.get({"workspace_sid": workspaceID})
        payload = ProviderModel.toDict(records)
        payload_response = ApiResponse.payload_v2(
            200,
            "Records retrieved successfully!",
            ProviderResponse(many=True).dump(payload),
        )
        return ApiResponse.output(payload_response)

    @backend_providers_bp.input(ProviderCreate.Schema, arg_name="provider")
    @backend_providers_bp.doc(tags=["Providers"], security="bearerAuth")
    def post(self, workspaceID, provider: ProviderCreate):
        """Create Provider"""
        provider.workspace_sid = workspaceID
        insert_id = ProviderModel.insert(provider)
        payload_response = ApiResponse.payload_v2(
            200, "Record created successfully!", {"sid": insert_id}
        )
        return ApiResponse.output(payload_response, 200)


backend_providers_bp.add_url_rule(
    "/<string:workspaceID>/providers", view_func=Providers.as_view("providers")
)


class Provider(AuthenticatedMethodView):

    @backend_providers_bp.doc(tags=["Providers"], security="bearerAuth")
    @backend_providers_bp.output(ProviderResponse)
    def get(self, workspaceID, providerID):

        record = ProviderModel.get(providerID)
        if not record:
            payload_response = ApiResponse.payload_v2(404, "Record not found!")
        else:
            payload = ProviderModel.toDict(record)
            payload_response = ApiResponse.payload_v2(
                200,
                "Record retrieved successfully!",
                ProviderResponse().dump(payload),
            )
        return ApiResponse.output(payload_response)

    @backend_providers_bp.input(ProviderCreate.Schema, arg_name="record")
    @backend_providers_bp.doc(tags=["Providers"], security="bearerAuth")
    def patch(self, workspaceID, providerID, record: ProviderCreate):
        """Update Provider"""
        ProviderModel.update(providerID, record)
        payload_response = ApiResponse.payload_v2(
            200, "Record updated successfully!", {}
        )
        return ApiResponse.output(payload_response)

    @backend_providers_bp.doc(tags=["Providers"], security="bearerAuth")
    def delete(self, workspaceID, providerID):
        """Delete Provider"""
        ProviderModel.delete({"sid": providerID})
        payload_response = ApiResponse.payload_v2(
            200, "Record deleted successfully!", {}
        )
        return ApiResponse.output(payload_response)


backend_providers_bp.add_url_rule(
    "/<string:workspaceID>/providers/<string:providerID>",
    view_func=Provider.as_view("provider"),
)
