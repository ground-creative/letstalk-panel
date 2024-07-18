import traceback, base64, os
from openai import OpenAI, OpenAIError
from models.Response import Response as ApiResponse


class OpenAiClient:

    @staticmethod
    def set_params(apiKey, logger, logLevel="INFO"):

        OpenAiClient.apiKey = apiKey
        OpenAiClient.logger = logger
        OpenAiClient.logLevel = logLevel

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

        try:
            args["messages"] = OpenAiClient.append_conversation_to_history(
                conversation_history, message, max_conversation_history
            )

            if base_url:
                client = OpenAI(api_key=OpenAiClient.apiKey, base_url=base_url)
            else:
                client = OpenAI(api_key=OpenAiClient.apiKey)

            response = client.chat.completions.create(**args)
            content = response.choices[0].message.content

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
        payload_response = ApiResponse.payload(
            True,
            200,
            msg,
            {"response_message": content, "conversation_history": conversation_history},
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
        conversation_history.append({"role": role, "content": message})
        if len(conversation_history) > max_conversation_history:
            conversation_history = [conversation_history[0]] + conversation_history[
                2:max_conversation_history
            ]
        return conversation_history
