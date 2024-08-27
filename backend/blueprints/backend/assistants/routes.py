from apiflask import APIBlueprint
from models.Response import Response as ApiResponse
from utils.views import AuthenticatedMethodView


backend_assistants_bp = APIBlueprint(
    "backend_assistants_blueprint",
    __name__,
    # tag={"name": "Workspaces", "description": "blah..."}, NOT WORKING
)


class Assistants(AuthenticatedMethodView):

    # @backend_workspaces_bp.input(
    #    {"workspaceID": {"type": "string"}}, location="path", arg_name="workspaceID"
    # )
    @backend_assistants_bp.doc(tags=["Assistants"], security="bearerAuth")
    # @backend_assistants_bp.output(ProviderResponse)
    def get(self, workspaceID):

        # records = ProviderModel.get({"workspace_sid": workspaceID})
        # payload = ProviderModel.toDict(records)
        payload_response = ApiResponse.payload_v2(
            200,
            "Records retrieved successfully!",
            # ProviderResponse(many=True).dump(payload),
        )
        return ApiResponse.output(payload_response)


backend_assistants_bp.add_url_rule(
    "/<string:workspaceID>/assistants", view_func=Assistants.as_view("assistants")
)
