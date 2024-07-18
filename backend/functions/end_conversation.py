import json, sys


def end_conversation():

    return json.dumps(
        {
            "resend": False,
            "callback": "some_callback",
            "content": "Alright, have a good day!",
        }
    )
