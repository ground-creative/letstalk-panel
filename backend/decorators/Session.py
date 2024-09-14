from functools import wraps
from flask import request, g, jsonify
from utils.session_utils import generate_session_id


def check_session_param(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        session_prefix = ""

        if hasattr(g, "api_key"):
            session_prefix = f"{g.api_key.api_key}-"
            assistantID = kwargs.get("assistantID")

            if not assistantID:
                return (
                    jsonify(
                        {
                            "error": "assistantID is required when using decorator check_session_param"
                        }
                    ),
                    400,
                )

            session_prefix += f"{assistantID}-"

        else:
            session_prefix = f"backend-"
            assistantID = kwargs.get("assistantID")

            if not assistantID:
                session_prefix += f"help-assistant-"
            else:
                session_prefix += f"{assistantID}-"

        session_id = request.headers.get("X-Session-Id")

        if session_id is None:
            session_id = request.cookies.get("session_id")

        if session_id is None:
            session_id = generate_session_id()

        g.session_id = f"{session_prefix}{session_id}"
        g.original_session_id = session_id

        return f(*args, **kwargs)

    return decorated_function
