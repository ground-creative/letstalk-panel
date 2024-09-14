from config.env import EnvConfig

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
            "kwargs": {"url_prefix": f"{EnvConfig.BACKEND_PREFIX}/workspaces"},
        },
        "api_keys": {
            "path": "blueprints.backend.api_keys.routes",
            "blueprint_name": "backend_api_keys_bp",
            "kwargs": {"url_prefix": f"{EnvConfig.BACKEND_PREFIX}/workspaces"},
        },
        "chat_assistants": {
            "path": "blueprints.backend.assistants.chat.routes",
            "blueprint_name": "backend_chat_assistants_bp",
            "kwargs": {"url_prefix": f"{EnvConfig.BACKEND_PREFIX}/workspaces"},
        },
        "providers": {
            "path": "blueprints.backend.providers.routes",
            "blueprint_name": "backend_providers_bp",
            "kwargs": {"url_prefix": f"{EnvConfig.BACKEND_PREFIX}/workspaces"},
        },
        "help_assistant": {
            "path": "blueprints.backend.assistants.help_assistant.routes",
            "blueprint_name": "backend_help_assistant_bp",
            "kwargs": {"url_prefix": f"{EnvConfig.BACKEND_PREFIX}/help-assistant"},
        },
        "Knowledge_base": {
            "path": "blueprints.backend.knowledge_base.routes",
            "blueprint_name": "backend_knowledge_base_bp",
            "kwargs": {"url_prefix": f"{EnvConfig.BACKEND_PREFIX}/workspaces"},
        },
    },
    "api": {
        "v1": {
            "path": "blueprints.api.v1.routes",
            "blueprint_name": "api_bp",
            "kwargs": {"url_prefix": "/api/v1"},
        },
        "v2": {
            "chat_assistants": {
                "path": "blueprints.api.v2.assistants.chat.routes",
                "blueprint_name": "api_v2_chat_bp",
                "kwargs": {"url_prefix": "/api/v2/assistants/chat"},
            },
            "completions": {
                "path": "blueprints.api.v2.assistants.completions.routes",
                "blueprint_name": "api_v2_completions_bp",
                "kwargs": {"url_prefix": "/api/v2/assistants"},
            },
        },
    },
}

# Conditionally add "frontend" services
if EnvConfig.WEB_PANEL_ADDRESS:
    services["frontend"] = {
        "path": "blueprints.frontend.routes",
        "blueprint_name": "frontend_bp",
        "kwargs": {"url_prefix": f"{EnvConfig.WEB_PANEL_PREFIX}"},
    }
