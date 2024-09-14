from functools import wraps
from flask import request, g
from utils.session_utils import generate_session_id


def check_session_cookie(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.cookies.get("session_id")
        if session_id is None:
            session_id = generate_session_id()

        g.session_id = session_id

        return f(*args, **kwargs)

    return decorated_function
