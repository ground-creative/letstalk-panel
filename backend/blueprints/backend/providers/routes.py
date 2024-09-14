from apiflask import APIBlueprint
from flask import g, current_app as app
from models.Response import Response as ApiResponse
from utils.views import AuthenticatedMethodView
from utils.llm import init_model, format_error
from decorators.Session import check_session_param
from blueprints.api.v2.schemas.Completions import CompletionsResponse
from blueprints.api.v2.models.Providers import ProviderModel
from blueprints.api.v2.schemas.Providers import (
    ProviderCreate,
    ProviderResponse,
    TestConnection,
)

backend_providers_bp = APIBlueprint("providers_blueprint", __name__)


class Providers(AuthenticatedMethodView):

    @backend_providers_bp.doc(tags=["Providers"], security="bearerAuth")
    @backend_providers_bp.output(ProviderResponse)
    def get(self, workspaceID):

        records = ProviderModel.get({"workspace_sid": workspaceID})
        payload = ProviderModel.to_dict(records)
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
    "/workspaces/<string:workspaceID>/providers",
    view_func=Providers.as_view("providers"),
)


class Provider(AuthenticatedMethodView):

    @backend_providers_bp.doc(tags=["Providers"], security="bearerAuth")
    @backend_providers_bp.output(ProviderResponse)
    def get(self, workspaceID, providerID):

        record = ProviderModel.get(providerID)
        if not record:
            payload_response = ApiResponse.payload_v2(404, "Record not found!")
        else:
            payload = ProviderModel.to_dict(record)
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
    "/workspaces/<string:workspaceID>/providers/<string:providerID>",
    view_func=Provider.as_view("provider"),
)


class TestConnection(AuthenticatedMethodView):
    @backend_providers_bp.doc(tags=["Providers"], security="bearerAuth")
    @backend_providers_bp.input(TestConnection.Schema, arg_name="record")
    @check_session_param
    @backend_providers_bp.output(CompletionsResponse)
    def post(elf, record: TestConnection):
        """Test Connection"""

        if record.type == "model":

            created_args = {
                "model": record.model,
                "api_key": record.api_key,
                "base_url": record.address,
            }

            if record.source == "cohere":
                created_args["cohere_api_key"] = created_args["api_key"]
                del created_args["api_key"]

            for key, value in record.args.items():
                created_args[key] = value

            result, llm = init_model(record.source, **created_args)

            if not result:
                payload_response = ApiResponse.payload_v2(500, llm)
                return ApiResponse.output(payload_response)

            invoke = ""
            try:
                invoke = llm.invoke("Hello, how are you today?")
            except Exception as e:
                error_code, error = format_error(record.source, e)
                app.logger.error(
                    f"Provider test connection completion service error: {error_code} {error}",
                    exc_info=app.config["DEBUG_APP"],
                )
                payload_response = ApiResponse.payload_v2(error_code, error)
                return ApiResponse.output(payload_response)
            payload_response = ApiResponse.payload_v2(200, invoke.content)
            return ApiResponse.output(payload_response)

        else:
            payload_response = ApiResponse.payload_v2(
                422, f"Type {record.type} not supported!"
            )

            return ApiResponse.output(payload_response)


backend_providers_bp.add_url_rule(
    "/test-connection",
    view_func=TestConnection.as_view("test-connection"),
)
