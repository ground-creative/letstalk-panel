from apiflask import APIBlueprint
from flask import current_app as app
from flask.views import MethodView
from models.Response import Response as ApiResponse
from decorators.UserAuth import require_jwt_auth
from utils.views import AuthenticatedMethodView


from dataclasses import field
from apiflask.validators import Length, OneOf, URL
from marshmallow_dataclass import dataclass

backend_providers_bp = APIBlueprint("providers_blueprint", __name__)


@dataclass
class ProviderIn:
    name: str = field(metadata={"required": True, "validate": Length(min=5, max=30)})
    apiKey: str = field(metadata={"required": True})
    address: str = field(metadata={"required": True, "validate": URL()})
    # workspace: str = field(metadata={"required": True})
    modelType: str = field(
        metadata={
            "required": True,
            "validate": OneOf(["transcriber", "model", "voice"]),
        }
    )
    sourceType: str = field(metadata={"required": True})
    defaultConfig: dict = field(default="")
    workspaces: str = field(
        default="",
        metadata={
            "metadata": {
                "example": "Medor",
                "description": "This will be printed in the generated doc. "
                'The "example" value "Medor" will be fed '
                'into the "try it"/"Send API request".',
            },
        },
    )


# /provider POST INSERT NEW PROVIDER
# /provider/<providerID> DELETE DEL PROVIDER
# /provider/<providerID> GET GET PROVIDER
# /provider/<providerID> PATCH UPDATE PROVIDER


class Provider(AuthenticatedMethodView):
    @require_jwt_auth
    def get(self, providerID):
        some_config_value = app.config.get("WEB_PANEL_PREFIX")

        print(some_config_value)
        print(providerID)

        providers = {
            "bbb8989gg": {"type": "model", "name": "Some name", "source": "openai"},
            "da78da8ee": {
                "type": "model",
                "name": "Some other name",
                "source": "openai",
            },
        }

        payload_response = ApiResponse.payload(True, 200, "lalalala", providers)
        return ApiResponse.output(payload_response, 200)

    @backend_providers_bp.input(ProviderIn.Schema, arg_name="provider")
    def create(self, provider: ProviderIn):

        payload_response = ApiResponse.payload(True, 200, "new provider created", {})
        return ApiResponse.output(payload_response, 200)


backend_providers_bp.add_url_rule(
    "/<string:providerID>",
    view_func=Provider.as_view("provider"),
)

backend_providers_bp.add_url_rule(
    "/",
    view_func=Provider.as_view("create"),
    methods=["POST"],
)
