from apiflask import APIBlueprint
from flask import (
    send_from_directory,
    render_template,
    redirect,
    request,
    g,
    abort,
    current_app as app,
)
from decorators.UserAuth import require_jwt_auth

docs_bp = APIBlueprint(
    "docs_blueprint",
    __name__,
)


def match_api_version(version):

    api_config = app.config.get("DOCS_CONFIG", {}).get("API", [])
    matching_version = next(
        (item for item in api_config["versions"] if item["route_suffix"] == version),
        None,
    )

    if not matching_version:
        return False

    return True


@docs_bp.route("/backend")
@require_jwt_auth(scheme="cookie")
def backend_docs():

    if "is_superadmin" in g.jwt_payload and g.jwt_payload["is_superadmin"]:
        auth = request.cookies.get("accessToken", None)
        docs_config = app.config["DOCS_CONFIG"]["BACKEND"]
        app.config["DOCS_TITLE"] = docs_config["title"]
        app.config["DOCS_SOURCE"] = "/docs/openapi-backend.json"
        app.config["SWAGGER_UI_CONFIG"]["onComplete"] = (
            "function() {ui.preauthorizeApiKey('bearerAuth', '" + auth + "');}"
        )
        app.config["DOCS_VERSIONS"] = []
        return render_template("/swagger.html")

    abort(404)


@docs_bp.route("/api", methods=["GET"])
@docs_bp.route("/", methods=["GET"])
def handle_redirect_to_api_docs():

    return redirect(f"/docs/api/v2", code=307)


@docs_bp.route("/api/<version>")
def api_docs(version):

    if not match_api_version(version):
        abort(404, description="Version not found")

    docs_config = app.config["DOCS_CONFIG"]["API"]
    app.config["DOCS_TITLE"] = docs_config["title"]
    app.config["DOCS_SOURCE"] = f"/docs/openapi-api-{version}.json"
    app.config["SWAGGER_UI_CONFIG"]["onComplete"] = "function() {}"
    app.config["DOCS_VERSIONS"] = docs_config["versions"]
    return render_template("/swagger.html")


@docs_bp.route("/openapi-api-<version>.json")
def api_docs_json(version):

    if not match_api_version(version):
        abort(404, description="Version not found")

    file_name = f"openapi-api-{version}.json"
    return send_from_directory("docs", file_name)
