from apiflask import APIBlueprint
from models.Response import Response as ApiResponse

api_v2_test_bp = APIBlueprint("api_v2_test_blueprint", __name__)


@api_v2_test_bp.route("/<workspace>", methods=["GET"])
def get_test(workspace):

    providers = {
        "bbb8989gg": {"type": "model", "name": "Some name", "source": "openai"},
        "da78da8ee": {"type": "model", "name": "Some other name", "source": "openai"},
    }

    payload_response = ApiResponse.payload(True, 200, "new user created", providers)
    return ApiResponse.output(payload_response, 200)


@api_v2_test_bp.route("/testing_w/<workspace>", methods=["GET"])
def get_testing(workspace):

    providers = {
        "bbb8989gg": {"type": "model", "name": "Some name", "source": "openai"},
        "da78da8ee": {"type": "model", "name": "Some other name", "source": "openai"},
    }

    payload_response = ApiResponse.payload(True, 200, "new user created", providers)
    return ApiResponse.output(payload_response, 200)
