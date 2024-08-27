from apiflask import APIBlueprint
from models.Response import Response as ApiResponse
from utils.views import AuthenticatedMethodView
from blueprints.backend.models.Providers import ProviderModel
from blueprints.backend.schemas.Providers import (
    ProviderCreate,
    ProviderResponse,
)


backend_workspaces_bp = APIBlueprint(
    "backend_workspaces_blueprint",
    __name__,
    # tag={"name": "Workspaces", "description": "blah..."}, NOT WORKING
)


class Providers(AuthenticatedMethodView):

    # @backend_workspaces_bp.input(
    #    {"workspaceID": {"type": "string"}}, location="path", arg_name="workspaceID"
    # )
    @backend_workspaces_bp.doc(tags=["Providers"], security="bearerAuth")
    @backend_workspaces_bp.output(ProviderResponse)
    def get(self, workspaceID):

        records = ProviderModel.get({"workspace_sid": workspaceID})
        payload = ProviderModel.toDict(records)
        payload_response = ApiResponse.payload_v2(
            200,
            "Records retrieved successfully!",
            ProviderResponse(many=True).dump(payload),
        )
        return ApiResponse.output(payload_response)

    @backend_workspaces_bp.input(ProviderCreate.Schema, arg_name="provider")
    @backend_workspaces_bp.doc(tags=["Providers"], security="bearerAuth")
    def post(self, workspaceID, provider: ProviderCreate):
        """Create Provider"""
        provider.workspace_sid = workspaceID
        insert_id = ProviderModel.insert(provider)
        payload_response = ApiResponse.payload_v2(
            200, "Record created successfully!", {"sid": insert_id}
        )
        return ApiResponse.output(payload_response, 200)


backend_workspaces_bp.add_url_rule(
    "/<string:workspaceID>/providers", view_func=Providers.as_view("providers")
)


class Provider(AuthenticatedMethodView):

    @backend_workspaces_bp.doc(tags=["Providers"], security="bearerAuth")
    @backend_workspaces_bp.output(ProviderResponse)
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

    @backend_workspaces_bp.input(ProviderCreate.Schema, arg_name="record")
    @backend_workspaces_bp.doc(tags=["Providers"], security="bearerAuth")
    def patch(self, workspaceID, providerID, record: ProviderCreate):
        """Update Provider"""
        ProviderModel.update(providerID, record)
        payload_response = ApiResponse.payload_v2(
            200, "Record updated successfully!", {}
        )
        return ApiResponse.output(payload_response)

    @backend_workspaces_bp.doc(tags=["Providers"], security="bearerAuth")
    def delete(self, workspaceID, providerID):
        """Delete Provider"""
        ProviderModel.delete({"sid": providerID})
        payload_response = ApiResponse.payload_v2(
            200, "Record deleted successfully!", {}
        )
        return ApiResponse.output(payload_response)


backend_workspaces_bp.add_url_rule(
    "/<string:workspaceID>/providers/<string:providerID>",
    view_func=Provider.as_view("provider"),
)


class Workspaces(AuthenticatedMethodView):
    @backend_workspaces_bp.doc(tags=["Workspaces"])
    def get(self, workspaceID):

        payload_response = ApiResponse.payload(True, 200, "record created", {})
        return ApiResponse.output(payload_response, 200)

    @backend_workspaces_bp.doc(tags=["Workspaces"])
    def delete(self, workspaceID):
        payload_response = ApiResponse.payload(True, 200, "provider inserted", {})
        return ApiResponse.output(payload_response, 200)

    @backend_workspaces_bp.doc(tags=["Workspaces"])
    def patch(self, workspaceID):
        payload_response = ApiResponse.payload(True, 200, "provider inserted", {})
        return ApiResponse.output(payload_response, 200)

    @backend_workspaces_bp.doc(tags=["Workspaces"])
    def post(self, workspaceID):
        payload_response = ApiResponse.payload(True, 200, "provider inserted", {})
        return ApiResponse.output(payload_response, 200)


backend_workspaces_bp.add_url_rule(
    "/<string:workspaceID>", view_func=Workspaces.as_view("workspaces")
)


# class Users(AuthenticatedMethodView):
#    def get(self, workspaceID):
#        payload_response = ApiResponse.payload(True, 200, "provider inserted", {})
#        return ApiResponse.output(payload_response, 200)


# backend_workspaces_bp.add_url_rule(
#    "/<string:workspaceID>/users", view_func=Users.as_view("users")
# )
