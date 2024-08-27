# utils/views.py
from functools import wraps
from flask import request
from flask.views import MethodView
from decorators.UserAuth import require_jwt_auth
from decorators.ApiKeyAuth import require_api_key_auth


class AuthenticatedMethodView(MethodView):
    def dispatch_request(self, *args, **kwargs):
        method_func = getattr(self, request.method.lower())
        decorated_func = self._wrap_with_decorator(require_jwt_auth(), method_func)
        return decorated_func(*args, **kwargs)

    def _wrap_with_decorator(self, decorator, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return decorator(lambda *args, **kwargs: func(*args, **kwargs))(
                *args, **kwargs
            )

        return wrapper


class APIAuthenticatedMethodView(MethodView):
    def dispatch_request(self, *args, **kwargs):
        method_func = getattr(self, request.method.lower())
        decorated_func = self._wrap_with_decorator(require_api_key_auth(), method_func)
        return decorated_func(*args, **kwargs)

    def _wrap_with_decorator(self, decorator, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return decorator(lambda *args, **kwargs: func(*args, **kwargs))(
                *args, **kwargs
            )

        return wrapper
