from flask import Response, request, g, current_app as app
from functools import wraps
from models.Response import Response as ApiResponse
from blueprints.backend.models.ApiKeys import ApiKeyModel


def get_api_key_header():
    """Obtains API Key from the X-API-Key Header"""
    auth = request.headers.get("X-API-Key", None)
    if not auth:
        payload_response = ApiResponse.payload_v2(401, "X-API-Key header is expected")
        return ApiResponse.output(payload_response)

    return auth


def validate_api_key(api_key):
    records = ApiKeyModel.get({"api_key": api_key, "type": "private"})
    if len(records) > 0:
        g.api_key = records[0]
        if app.config.get("DEBUG_APP"):
            app.logger.debug("API Key: %s", g.api_key)
        return None
    payload_response = ApiResponse.payload_v2(401, "API Key not found")
    return ApiResponse.output(payload_response)


def require_api_key_auth(scheme=None):
    """Determines if the API Key is valid"""

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            api_key_response = get_api_key_header()

            if isinstance(api_key_response, Response):
                return api_key_response

            error_response = validate_api_key(api_key_response)

            if error_response:
                return error_response

            return f(*args, **kwargs)

        return decorated

    return decorator
