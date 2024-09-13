from apiflask import APIBlueprint
from models.Response import Response as ApiResponse
from utils.views import AuthenticatedMethodView


backend_workspaces_bp = APIBlueprint(
    "backend_workspaces_blueprint",
    __name__,
    # tag={"name": "Workspaces", "description": "blah..."}, NOT WORKING
)


class Workspaces(AuthenticatedMethodView):
    @backend_workspaces_bp.doc(tags=["Workspaces"], security="bearerAuth")
    def get(self, workspaceID):

        payload_response = ApiResponse.payload(True, 200, "record created", {})
        return ApiResponse.output(payload_response, 200)

    @backend_workspaces_bp.doc(tags=["Workspaces"], security="bearerAuth")
    def post(self, workspaceID):
        payload_response = ApiResponse.payload(True, 200, "provider inserted", {})
        return ApiResponse.output(payload_response, 200)


backend_workspaces_bp.add_url_rule(
    "/<string:workspaceID>", view_func=Workspaces.as_view("workspaces")
)


class Workspace(AuthenticatedMethodView):
    @backend_workspaces_bp.doc(tags=["Workspaces"], security="bearerAuth")
    def get(self, workspaceID):

        payload_response = ApiResponse.payload(True, 200, "record created", {})
        return ApiResponse.output(payload_response, 200)

    @backend_workspaces_bp.doc(tags=["Workspaces"], security="bearerAuth")
    def delete(self, workspaceID):
        payload_response = ApiResponse.payload(True, 200, "provider inserted", {})
        return ApiResponse.output(payload_response, 200)

    @backend_workspaces_bp.doc(tags=["Workspaces"], security="bearerAuth")
    def patch(self, workspaceID):
        payload_response = ApiResponse.payload(True, 200, "provider inserted", {})
        return ApiResponse.output(payload_response, 200)


backend_workspaces_bp.add_url_rule(
    "/<string:workspaceID>", view_func=Workspace.as_view("workspace")
)
