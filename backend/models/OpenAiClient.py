import traceback, base64, os, json, importlib, copy
from openai import OpenAI, OpenAIError
from models.Response import Response as ApiResponse


def execute_function_call(functionName, args=None):

    functions_path = "functions"
    file_path = os.path.join(functions_path, f"{functionName}.py")

    if os.path.exists(file_path):
        try:
            module = importlib.import_module(f"functions.{functionName}")
            func = getattr(module, functionName)
            # print(f"args: {args}, type: {type(args)}")
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                print("Error decoding JSON function call arguments")
                args = {}

            if isinstance(args, dict) and args:
                results = func(**args)
            else:
                results = func()

        except AttributeError:
            results = (
                f"Error: function {functionName} does not exist in folder functions"
            )
            OpenAiClient.logger.error(results)
    else:
        results = f"Error: file for function {functionName} does not exist"

    return results


class OpenAiClient:

    apiKey = None
    logger = None
    logLevel = "INFO"

    @staticmethod
    def set_params(params):
        for key, value in params.items():
            if hasattr(OpenAiClient, key):
                setattr(OpenAiClient, key, value)
            else:
                raise AttributeError(f"Invalid attribute: {key}")

    @staticmethod
    def speech_to_text(audio_file, args, base_url=None):

        try:
            if base_url:
                client = OpenAI(api_key=OpenAiClient.apiKey, base_url=base_url)
            else:
                client = OpenAI(api_key=OpenAiClient.apiKey)

            args["file"] = audio_file
            # args["response_format"] = "json"
            transcript = client.audio.transcriptions.create(**args)

        except OpenAIError as e:

            if e.body is not None:
                if "message" in e.body:
                    response_message = e.body["message"]
                elif "result" in e.body:
                    response_message = e.body["result"]["message"]
                else:
                    response_message = "Unknown error"
            else:
                response_message = "Unknown error"

            payload_response = ApiResponse.payload(
                False, e.status_code, response_message
            )
            return ApiResponse.output(payload_response, e.status_code)

        except Exception as e:
            OpenAiClient.logger.error(f"Error getting STT: {str(e)}")

            if OpenAiClient.logLevel == "DEBUG":
                OpenAiClient.logger.error(traceback.format_exc())

            status_code, response_message = OpenAiClient._formatError(e)
            payload_response = ApiResponse.payload(False, status_code, response_message)
            return ApiResponse.output(payload_response, status_code)

        msg = "Speech to text converted successfully"
        payload_response = ApiResponse.payload(
            True, 200, msg, {"text": transcript.text}
        )
        return ApiResponse.output(payload_response, 200)

    @staticmethod
    def completion(
        message, conversation_history, max_conversation_history, args, base_url=None
    ):

        callback = None
        try:
            args["messages"] = OpenAiClient.append_conversation_to_history(
                conversation_history, message, max_conversation_history
            )

            if base_url:
                client = OpenAI(api_key=OpenAiClient.apiKey, base_url=base_url)
            else:
                client = OpenAI(api_key=OpenAiClient.apiKey)

            response = client.chat.completions.create(**args)
            message = response.choices[0].message
            content = message.content

            if message.tool_calls:
                for tool_call in message.tool_calls:
                    results = execute_function_call(
                        tool_call.function.name, tool_call.function.arguments
                    )
                    call_result = json.loads(results)

                    if "callback" in call_result and call_result["resend"] != None:
                        callback = call_result["callback"]

                    if "resend" in call_result and call_result["resend"] == True:
                        # call_result.pop("resend")
                        function_call_messages = copy.deepcopy(conversation_history)
                        function_call_messages.append(message)
                        function_call_messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name,
                                "content": json.dumps(call_result),
                            }
                        )
                        args["messages"] = function_call_messages

                        if base_url:
                            client = OpenAI(
                                api_key=OpenAiClient.apiKey, base_url=base_url
                            )
                        else:
                            client = OpenAI(api_key=OpenAiClient.apiKey)

                        response = client.chat.completions.create(**args)
                        message = response.choices[0].message
                        content = message.content

                    else:
                        content = call_result["content"]

        except OpenAIError as e:
            OpenAiClient.logger.error(f"Error getting completion: {str(e)}")

            if OpenAiClient.logLevel == "DEBUG":
                OpenAiClient.logger.error(traceback.format_exc())

            status_code, response_message = OpenAiClient._formatError(e)
            payload_response = ApiResponse.payload(False, status_code, response_message)
            return ApiResponse.output(payload_response, status_code)

        except Exception as e:
            OpenAiClient.logger.error(f"Error getting completion: {str(e)}")

            if OpenAiClient.logLevel == "DEBUG":
                OpenAiClient.logger.error(traceback.format_exc())

            payload_response = ApiResponse.payload(False, 500, "Internal server error")
            return ApiResponse.output(payload_response, 500)

        msg = "Completion received successfully"
        conversation_history = OpenAiClient.append_conversation_to_history(
            conversation_history, content, max_conversation_history, "assistant"
        )
        # print(
        #    {
        #        "response_message": content,
        #        "conversation_history": conversation_history,
        #        "callback": callback,
        #    }
        # )
        payload_response = ApiResponse.payload(
            True,
            200,
            msg,
            {
                "response_message": content,
                "conversation_history": conversation_history,
                "callback": callback,
            },
        )
        return ApiResponse.output(payload_response, 200)

    @staticmethod
    def text_to_speech(file_name, args, base_url=None):

        if base_url:
            client = OpenAI(api_key=OpenAiClient.apiKey, base_url=base_url)
        else:
            client = OpenAI(api_key=OpenAiClient.apiKey)

        try:
            response = client.audio.speech.create(**args)
            response.stream_to_file(file_name)
            with open(file_name, "rb") as audio_file:
                audio_data = audio_file.read()
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            os.remove(file_name)

        except OpenAIError as e:

            status_code, response_message = OpenAiClient._formatError(e)
            payload_response = ApiResponse.payload(False, status_code, response_message)
            return ApiResponse.output(payload_response, status_code)

        except Exception as e:
            OpenAiClient.logger.error(f"Error getting STT: {str(e)}")

            if OpenAiClient.logLevel == "DEBUG":
                OpenAiClient.logger.error(traceback.format_exc())

            payload_response = ApiResponse.payload(False, 500, "Internal server error")
            return ApiResponse.output(payload_response, 500)

        payload_response = ApiResponse.payload(
            True,
            200,
            "Successfully converted text to speech",
            {"audio_base64": audio_base64},
        )
        return ApiResponse.output(payload_response)

    @staticmethod
    def _formatError(e):

        if e.body is not None:
            if "message" in e.body:
                response_message = e.body["message"]
            elif "result" in e.body:
                response_message = e.body["result"]["message"]
            else:
                response_message = "Unknown error"
        else:
            response_message = "Unknown error"

        if hasattr(e, "status_code"):
            status_code = e.status_code
        else:
            status_code = 500

        return status_code, response_message

    @staticmethod
    def append_conversation_to_history(
        conversation_history, message, max_conversation_history=10, role="user"
    ):
        # Append the new message to the conversation history
        conversation_history.append({"role": role, "content": message})

        # Trim the conversation history if it exceeds the maximum length
        if (
            max_conversation_history > 0
            and len(conversation_history) > max_conversation_history
        ):
            # Keep the first element and remove the oldest messages to keep the total count to max_conversation_history
            conversation_history = [conversation_history[0]] + conversation_history[
                1 - max_conversation_history :
            ]

        return conversation_history
