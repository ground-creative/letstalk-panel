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
            "time": int(dt.timestamp() * 1000)  # Convert to milliseconds and round to integer
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
            "time": int(dt.timestamp() * 1000)  # Convert to milliseconds and round to integer
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
            "time": int(dt.timestamp() * 1000)  # Convert to milliseconds and round to integer
        }
        return response

    @staticmethod
    def output(data, code=None, contentType=None):
        response = make_response(data, code if code is not None else 200)
        
        if contentType:
            response.headers['Content-Type'] = contentType

        Response.logger.info(f'Response: {data}')
        return response
