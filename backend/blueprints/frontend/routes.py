import requests
from flask import Blueprint, request, Response, current_app as app

frontend_bp = Blueprint("frontend_blueprint", __name__)


@frontend_bp.route("", methods=["GET", "POST"])
def proxy_to_panel_url():

    base_url = f"{app.config.get('WEB_PANEL_ADDRESS')}:{app.config.get('WEB_PANEL_PORT')}{app.config.get('WEB_PANEL_PREFIX')}"
    proxy_url = f"{base_url}"
    response = requests.get(proxy_url)

    if response.status_code == 200:
        return Response(response.content, content_type=response.headers["Content-Type"])

    else:
        return (
            f"Error: Failed to fetch data from {proxy_url}. Status code: {response.status_code}",
            response.status_code,
        )


@frontend_bp.route("/<path:subpath>", methods=["GET", "POST"])
def proxy_to_panel_url_paths(subpath):

    # if request.path.startswith("/api/"):
    #    return jsonify({"error": "API endpoint not found"}), 404

    base_url = f"{app.config.get('WEB_PANEL_ADDRESS')}:{app.config.get('WEB_PANEL_PORT')}{app.config.get('WEB_PANEL_PREFIX')}"
    proxy_url = f"{base_url}/{subpath}"
    response = requests.get(proxy_url)

    if response.status_code == 200:
        return Response(response.content, content_type=response.headers["Content-Type"])

    else:
        return (
            f"Error: Failed to fetch data from {proxy_url}. Status code: {response.status_code}",
            response.status_code,
        )


@frontend_bp.route("/static/<path>/<subpath>", methods=["GET", "POST"])
def proxy_to_panel_url_static(path, subpath):

    # if request.path.startswith("/api/"):
    #    return jsonify({"error": "API endpoint not found"}), 404

    base_url = f"{app.config.get('WEB_PANEL_ADDRESS')}:{app.config.get('WEB_PANEL_PORT')}{app.config.get('WEB_PANEL_PREFIX')}"
    proxy_url = f"{base_url}/static/{path}/{subpath}"
    response = requests.get(proxy_url)

    if response.status_code == 200:
        return Response(response.content, content_type=response.headers["Content-Type"])

    else:
        return (
            f"Error: Failed to fetch data from {proxy_url}. Status code: {response.status_code}",
            response.status_code,
        )
