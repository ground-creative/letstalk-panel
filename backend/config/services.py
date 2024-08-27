services = {
    "docs": {
        "path": "blueprints.docs.routes",
        "blueprint_name": "docs_bp",
        "kwargs": {"url_prefix": "/docs"},
    },
    "backend": {
        "workspaces": {
            "path": "blueprints.backend.workspaces.routes",
            "blueprint_name": "backend_workspaces_bp",
            "kwargs": {"url_prefix": "/backend/workspaces"},
        },
        "api_keys": {
            "path": "blueprints.backend.api_keys.routes",
            "blueprint_name": "backend_api_keys_bp",
            "kwargs": {"url_prefix": "/backend/workspaces"},
        },
        "assistants": {
            "path": "blueprints.backend.assistants.routes",
            "blueprint_name": "backend_assistants_bp",
            "kwargs": {"url_prefix": "/backend/workspaces"},
        },
        # "providers": {
        #    "path": "blueprints.backend.providers.routes",
        #    "blueprint_name": "backend_providers_bp",
        #    "kwargs": {"url_prefix": "/backend/providers"},
        # },
    },
    "frontend": {
        "path": "blueprints.frontend.routes",
        "blueprint_name": "frontend_bp",
        "kwargs": {"url_prefix": "/panel"},
    },
    "api": {
        "v1": {
            "path": "blueprints.api.v1.routes",
            "blueprint_name": "api_bp",
            "kwargs": {"url_prefix": "/api/v1"},
        },
        "v2": {
            "path": "blueprints.api.v2.assistants.chat.routes",
            "blueprint_name": "api_v2_chat_bp",
            "kwargs": {"url_prefix": "/api/v2/assistants"},
        },
    },
}
