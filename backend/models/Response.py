from flask import make_response
from datetime import datetime


class Response:

    logger = None

    @staticmethod
    def set_logger(logger):
        Response.logger = logger

    @staticmethod
    def payload(success, code, msg, data={}):
        dt = datetime.now()
        response = {
            "result": {
                "success": success,
                "message": msg,
                "data": data,
            },
            "code": code,
            "time": int(
                dt.timestamp() * 1000
            ),  # Convert to milliseconds and round to integer
        }
        return response

    @staticmethod
    def payload_v2(code, msg, data={}):
        dt = datetime.now()
        response = {
            "status_code": code,
            "message": msg,
            "time": int(dt.timestamp() * 1000),
            "data": data,
        }
        return response

    @staticmethod
    def timeout(code, msg, data=None):
        dt = datetime.now()
        response = {
            "result": {
                "success": False,
                "message": msg,
                "data": data,
            },
            "code": code,
            "time": int(
                dt.timestamp() * 1000
            ),  # Convert to milliseconds and round to integer
        }
        return response

    @staticmethod
    def timeout_v2(code, msg, data=None):
        dt = datetime.now()
        response = {
            "status_code": code,
            "message": msg,
            "time": int(dt.timestamp() * 1000),
            "data": data,
        }
        return response

    @staticmethod
    def not_found_v2(msg, data=None):
        dt = datetime.now()
        response = {
            "status_code": 404,
            "message": msg,
            "time": int(dt.timestamp() * 1000),
            "data": data,
        }
        return response

    @staticmethod
    def not_found(msg, data=None):
        dt = datetime.now()
        response = {
            "result": {
                "success": False,
                "message": msg,
                "data": data,
            },
            "code": 404,
            "time": int(
                dt.timestamp() * 1000
            ),  # Convert to milliseconds and round to integer
        }
        return response

    @staticmethod
    def output(data, code=None, headers=None, cookies=None):
        response = make_response(data, data["status_code"] if code is None else code)

        if headers:
            response.headers = headers

        if cookies:
            for cookie in cookies:
                first_key = next(iter(cookie.keys()))
                response.set_cookie(first_key, cookie[first_key], httponly=True)

        Response.logger.info(f"Response: {data}")
        return response
