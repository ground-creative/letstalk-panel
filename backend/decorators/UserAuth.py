from flask import Response, json, request, current_app as app, g
from urllib.request import urlopen
from jose import jwt
from functools import wraps
from models.Response import Response as ApiResponse


def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header"""
    auth = request.headers.get("Authorization", None)
    if not auth:
        payload_response = ApiResponse.payload_v2(
            401, "Authorization header is expected"
        )
        return ApiResponse.output(payload_response)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        payload_response = ApiResponse.payload_v2(
            401, "Authorization header must start with Bearer"
        )
        return ApiResponse.output(payload_response)
    elif len(parts) == 1:
        payload_response = ApiResponse.payload_v2(401, "Token not found")
        return ApiResponse.output(payload_response)
    elif len(parts) > 2:
        payload_response = ApiResponse.payload_v2(
            401, "Authorization header must be Bearer token"
        )
        return ApiResponse.output(payload_response)

    token = parts[1]
    return token


def get_token_cookie():
    """Obtains the Access Token from the cookie"""
    auth = request.cookies.get("accessToken", None)
    if not auth:
        payload_response = ApiResponse.payload_v2(
            401, "Authorization header is expected"
        )
        return ApiResponse.output(payload_response)
    token = auth
    return token


def validate_token(token):
    """Validates the Access Token and sets g.jwt_payload."""
    try:
        # Load the JWKS (JSON Web Key Set)
        jsonurl = urlopen(
            "https://" + app.config.get("AUTH0_DOMAIN") + "/.well-known/jwks.json"
        )
        jwks = json.loads(jsonurl.read())

        # Decode the token header
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }

        if rsa_key:
            try:
                # Decode the token
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=app.config.get("ALGORITHMS"),
                    audience=app.config.get("API_AUDIENCE"),
                    issuer="https://" + app.config.get("AUTH0_DOMAIN") + "/",
                )
                g.jwt_payload = payload
                print(payload)
                return None  # Indicate success
            except jwt.ExpiredSignatureError:
                return ApiResponse.output(
                    ApiResponse.payload_v2(401, "Token is expired")
                )
            except jwt.JWTClaimsError:
                return ApiResponse.output(
                    ApiResponse.payload_v2(
                        401,
                        "Incorrect claims, please check the audience and issuer",
                    ),
                )
            except Exception as e:
                app.logger.error(f"JWT decode error: {e}")
                return ApiResponse.output(
                    ApiResponse.payload_v2(401, "Unable to parse authentication token.")
                )
        else:
            app.logger.error("RSA key not found")
            return ApiResponse.output(ApiResponse.payload_v2(401, "Invalid token"))
    except Exception as e:
        app.logger.error(f"Error in token validation: {e}")
        return ApiResponse.output(ApiResponse.payload_v2(401, "Token validation error"))


def require_jwt_auth(scheme=None):
    """Determines if the Access Token is valid"""

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if scheme == "cookie":
                token_response = get_token_cookie()
            else:
                token_response = get_token_auth_header()

            if isinstance(token_response, Response):
                return token_response

            # Use validate_token function
            error_response = validate_token(token_response)
            if error_response:
                return error_response

            return f(*args, **kwargs)

        return decorated

    return decorator
