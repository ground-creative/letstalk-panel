from apiflask import APIFlask, Schema
from apiflask.fields import String, Integer, Dict


class BaseResponse(Schema):
    code = Integer()
    message = String()
    time = Integer()
    data = Dict()


class DocsConfig:

    SUCCESS_DESCRIPTION = "Successful response"
    NOT_FOUND_DESCRIPTION = "Not Found"
    VALIDATION_ERROR_STATUS_CODE = 422
    VALIDATION_ERROR_DESCRIPTION = "Validation error"
    AUTH_ERROR_DESCRIPTION = "Authentication error"
    DOCS_LOGO = "/panel/favicon.png"
    DOCS_FAVICON = "/static/api.png"
    SWAGGER_UI_LAYOUT = "BaseLayout"
    SYNC_LOCAL_SPEC = True
    LOCAL_SPEC_PATH = "docs/openapi-backend.json"
    SWAGGER_UI_CONFIG = {
        "displayRequestDuration": True,
        "requestSnippetsEnabled": False,
        "defaultModelsExpandDepth": -1,
    }
    BASE_RESPONSE_SCHEMA = BaseResponse
    VALIDATION_ERROR_SCHEMA = {
        "type": "object",
        "properties": {
            "<field_name>": {"type": "array", "items": {"type": "string"}},
        },
    }
    HTTP_ERROR_SCHEMA = {}
    TAGS = [
        # {"name": "Workspaces", "description": "Operations to manage workspaces"},
        # {"name": "Providers", "description": "Operations to manage providers"},
        "Workspaces",
        "Providers",
    ]
    DOCS_CONFIG = {
        "BACKEND": {
            "title": "Let's Talk Backend API",
            "description": "API to manage data in the frontend panel",
            "version": "1.0",
            "tags": [
                {"name": "Workspaces"},
                {"name": "Providers"},
                {"name": "Api Keys"},
            ],
        },
        "API": {
            "title": "Let's Talk API Docs",
            "description": "API for building assistants",
            "versions": [
                {
                    "name": "API v2",
                    "url": "/docs/api/v2",
                    "route_suffix": "v2",
                    "base_path": "/api/v2/",
                    "version": "2.0",
                    "tags": [{"name": "Assistants"}],
                }  # ,
                # {
                #    "name": "API v3",
                #    "url": "/docs/api/v3",
                #    "route_suffix": "v3",
                #    "base_path": "/api/v3/",
                #    "version": "3.0",
                # },
            ],
        },
    }
