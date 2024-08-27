class SecurityConfig:

    SECURITY_SCHEMES = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
        },
        "bearerAuth": {
            "type": "http",
            "in": "header",
            "scheme": "bearer",
        },
    }
