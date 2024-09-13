import json, random, string, secrets
import re
from marshmallow import ValidationError


def convert_properties(fields_to_convert, obj):
    if isinstance(obj, list):
        return [convert_properties(fields_to_convert, item) for item in obj]
    elif isinstance(obj, dict):
        for key, value in obj.items():
            if key in fields_to_convert and isinstance(value, str):
                try:
                    obj[key] = json.loads(value)
                except json.JSONDecodeError:
                    pass
        return obj
    else:
        return obj


def generate_random_string(length=10):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def generate_api_key(prefix="", length=32):
    """Generate a secure API key with an optional prefix."""
    characters = string.ascii_letters + string.digits
    api_key = "".join(secrets.choice(characters) for _ in range(length))

    if prefix:
        api_key = f"{prefix}-{api_key}"

    return api_key


def validate_pattern(value, pattern, errorMsg=None):
    if not re.match(pattern, value):
        errorMsg = (
            f"Field does not match the required pattern: {pattern}"
            if errorMsg is None
            else errorMsg
        )
        raise ValidationError(errorMsg)


def validate_provider_sid(value):
    from blueprints.api.v2.models.Providers import ProviderModel

    provider = ProviderModel.get(value)
    if not provider:
        raise ValidationError(f"Provider id {value} not found")
    return provider
