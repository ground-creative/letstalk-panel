import copy
import json
from flask import current_app as app


def update_spec(spec):
    """Update OpenAPI spec and save to file."""
    print("Updating OpenAPI spec...")
    spec["components"]["schemas"].pop("HTTPError")
    spec["components"]["schemas"].pop("ValidationError")
    # spec["components"]["response_examples"] = {
    #    "AuthenticationErrorResponse": {
    #        "description": "SOME BLAHBLAHB BLAHBAS BLAB AHSDA BLA DAHD",
    #        "example": {
    #            "data": {},
    #            "message": "Token validation error",
    #            "status_code": 401,
    #            "time": 1724075162135,
    #        },
    #    }
    # }
    for path, methods in spec["paths"].items():
        for method, details in methods.items():
            if "responses" in details:
                response_schema = details["responses"]["200"]["content"][
                    "application/json"
                ]["schema"]["properties"]["data"]
                # if isinstance(response_schema, dict):
                #    details["responses"]["200"]["content"]["application/json"][
                #        "schema"
                #    ]["properties"]["data"] = {"type": "object"}
                details["responses"].pop("404", None)
                details["responses"].pop("401", None)
                details["responses"].pop("422", None)

    api_config = app.config.get("DOCS_CONFIG", {}).get("API", [])
    for api_version in api_config["versions"]:
        cloned_spec = copy.deepcopy(spec)
        cloned_spec["info"]["title"] = api_config["title"]
        cloned_spec["info"]["description"] = api_config["description"]
        cloned_spec["info"]["version"] = api_version["version"]
        cloned_spec["tags"] = api_version["tags"] if "tags" in api_version else []

        if "paths" in cloned_spec:
            cloned_spec["paths"] = {
                key: value
                for key, value in cloned_spec["paths"].items()
                if key.startswith(api_version["base_path"])
            }

        if (
            "components" in cloned_spec
            and "securitySchemes" in cloned_spec["components"]
        ):
            if "bearerAuth" in cloned_spec["components"]["securitySchemes"]:
                del cloned_spec["components"]["securitySchemes"]["bearerAuth"]

        try:
            with open(f"docs/openapi-api-{api_version['route_suffix']}.json", "w") as f:
                json.dump(cloned_spec, f, indent=2)
            print(
                f"docs/openapi-api-{api_version['route_suffix']}.json file has been created successfully."
            )
        except Exception as e:
            print(f"Error writing openapi-api-{api_version['route_suffix']}.json: {e}")

    backend_config = app.config.get("DOCS_CONFIG", {}).get("BACKEND", [])
    spec["info"]["title"] = backend_config["title"]
    spec["info"]["version"] = backend_config["version"]
    spec["info"]["description"] = backend_config["description"]
    # spec["info"][
    #    "description"
    # ] = "<details><summary>wow</summary> look at this!</details>"

    if "paths" in spec:
        spec["paths"] = {
            key: value
            for key, value in spec["paths"].items()
            if key.startswith("/backend/")
        }

    if "components" in spec and "securitySchemes" in spec["components"]:
        if "ApiKeyAuth" in spec["components"]["securitySchemes"]:
            del spec["components"]["securitySchemes"]["ApiKeyAuth"]

    # try:
    #     with open("static/api_v2.json", "w") as f:
    #         json.dump(spec, f, indent=2)
    #     print("api_v2.json file has been created successfully.")
    # except Exception as e:
    #     print(f"Error writing api_v2.json: {e}")

    print(f"docs/openapi-backend.json file has been updated successfully.")

    return spec
