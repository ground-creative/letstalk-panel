import logging, colorlog, os, traceback, sys, base64, requests, json, io, magic, uuid
from flask import Flask, request, redirect, Response
from flask_cors import CORS
from dotenv import load_dotenv
from models.Response import Response as ApiResponse
from models.OpenAiClient import OpenAiClient
from time import time
from datetime import datetime
from elevenlabs.client import ElevenLabs
from openvoice_api_client.client import OpenVoiceApiClient
from werkzeug.utils import secure_filename
from flask import jsonify, send_file
from pydub import AudioSegment

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "/tmp"
CORS(app)

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
SERVER_ADDRESS = os.getenv("SERVER_ADDRESS", "0.0.0.0")
SERVER_PORT = os.getenv("SERVER_PORT", 5000)
OPENVOICE_API_URL = os.getenv("OPENVOICE_API_URL", "http://127.0.0.1:5001")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434")
LMSTUDIO_API_URL = os.getenv("LMSTUDIO_API_URL", "http://127.0.0.1:1234")
FAST_WHISPER_API_URL = os.getenv("FAST_WHISPER_API_URL", "http://127.0.0.1:5003")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
WEB_PANEL_ADDRESS = os.getenv("WEB_PANEL_ADDRESS", "http://127.0.0.1:3000")

# Configure colored logging
handler = colorlog.StreamHandler()
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_colors={
        "DEBUG": "white",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)
handler.setFormatter(formatter)

logger = colorlog.getLogger()
logger.addHandler(handler)
logger.setLevel(LOG_LEVEL)

ApiResponse.set_logger(app.logger)
OpenAiClient.set_params(OPENAI_API_KEY, app.logger, LOG_LEVEL)


@app.before_request
def log_request_info():
    app.logger.info(
        f"Started processing {request.method} request from {request.remote_addr} => {request.url}"
    )
    if request.path.endswith("/") and request.path != "/":
        return redirect(request.path[:-1], code=308)
    request.start_time = time()


@app.after_request
def add_header(response):
    if hasattr(request, "start_time"):
        elapsed_time = time() - request.start_time
        response.headers["X-Elapsed-Time"] = str(elapsed_time)
        response.headers["Access-Control-Expose-Headers"] = "X-Elapsed-Time"
    return response


@app.teardown_request
def log_teardown(exception=None):
    if exception:
        app.logger.error(f"Exception occurred: {exception}")
    app.logger.info(
        f"Finished processing {request.method} request from {request.remote_addr} => {request.url}"
    )


def generate_random_filename(prefix="", ext="wav"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    random_filename = f"{prefix}{timestamp}.{ext}"
    return random_filename


@app.route("/api/speech-to-text/<engine>", methods=["POST"])
def speech_to_text(engine):

    try:
        params = dict(request.form)
        create_args = {key: params[key] for key in params if not key.startswith("__")}

        if "audio" in request.files:
            audio = request.files["audio"]
            app.logger.debug(f"Received audio file: {audio.filename}")
            filename = secure_filename(audio.filename)
            file_name = generate_random_filename(
                app.config["UPLOAD_FOLDER"] + "/", filename
            )
            audio.save(file_name)
            audio_file = open(file_name, "rb")

            if engine == "openai":
                create_args["response_format"] = "json"
                return OpenAiClient.speech_to_text(audio_file, create_args)

            elif engine == "fast-whisper":
                return OpenAiClient.speech_to_text(
                    audio_file, create_args, base_url=f"{FAST_WHISPER_API_URL}/v1"
                )

            else:
                payload_response = ApiResponse.payload(
                    False, 400, f"STT engine {engine} not supported"
                )
                return ApiResponse.output(payload_response, 400)
        else:
            payload_response = ApiResponse.payload(False, 400, "No audio file provided")
            return ApiResponse.output(payload_response, 400)

    except Exception as e:
        app.logger.error(f"Error uploading audio: {str(e)}")

        if LOG_LEVEL == "DEBUG":
            app.logger.error(traceback.format_exc())

        payload_response = ApiResponse.payload(False, 500, "Internal server error")
        return ApiResponse.output(payload_response, 500)


@app.route("/api/chat/<engine>", methods=["POST"])
def chat(engine):

    try:
        params = request.json
        conversation_history = params.get("__conversation_history", [])
        max_conversation_history = params.get("__max_conversation_history", 10)
        message = params.get("__message", "")
        create_args = {key: params[key] for key in params if not key.startswith("__")}

        if engine == "openai":
            return OpenAiClient.completion(
                message, conversation_history, max_conversation_history, create_args
            )
        elif engine == "ollama":
            return OpenAiClient.completion(
                message,
                conversation_history,
                max_conversation_history,
                create_args,
                f"{OLLAMA_API_URL}/v1",
            )
        elif engine == "lmstudio":
            return OpenAiClient.completion(
                message,
                conversation_history,
                max_conversation_history,
                create_args,
                f"{LMSTUDIO_API_URL}/v1",
            )
        else:
            payload_response = ApiResponse.payload(
                False, 400, f"Completion engine {engine} not supported"
            )
            return ApiResponse.output(payload_response, 400)

    except Exception as e:
        app.logger.error(f"Error getting completion: {str(e)}")

        if LOG_LEVEL == "DEBUG":
            app.logger.error(traceback.format_exc())

        payload_response = ApiResponse.payload(False, 500, "Internal server error")
        return ApiResponse.output(payload_response, 500)


@app.route("/api/text-to-speech/<engine>", methods=["POST"])
def text_to_speech(engine):

    try:
        params = request.json
        create_args = {key: params[key] for key in params if not key.startswith("__")}
        file_name = generate_random_filename(app.config["UPLOAD_FOLDER"] + "/", ".wav")

        if engine == "openai":
            create_args["response_format"] = "wav"
            return OpenAiClient.text_to_speech(file_name, create_args)

        elif engine == "openvoicev1" or engine == "openvoicev2":
            model = params.get("model", "")
            input_text = params.get("input", "")
            voice = params.get("voice", "")
            extra_body = {
                key: params[key]
                for key in params
                if key not in ["model", "input", "voice"]
            }
            create_args = {
                "model": model,
                "input": input_text,
                "voice": voice,
                "extra_body": extra_body,
                "response_format": "wav",
            }
            base_url = OPENVOICE_API_URL + "/" + engine[-2:].lower()
            return OpenAiClient.text_to_speech(file_name, create_args, base_url)

        elif engine == "elevenlabs":
            create_args["text"] = create_args["input"]
            create_args.pop("input", None)
            if ELEVENLABS_API_KEY:
                client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            else:
                client = ElevenLabs()
            audio = client.generate(**create_args)
            audio_bytes = b"".join(audio)
            audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
            output_wav = io.BytesIO()
            audio_segment.export(output_wav, format="wav")
            output_wav.seek(0)
            converted_audio_bytes = output_wav.read()
            audio_base64 = base64.b64encode(converted_audio_bytes).decode("utf-8")
            payload_response = ApiResponse.payload(
                True,
                200,
                "Successfully converted text to speech",
                {"audio_base64": audio_base64},
            )
            return ApiResponse.output(payload_response)

        else:
            payload_response = ApiResponse.payload(
                False, 400, f"TTS engine {engine} not supported"
            )
            return ApiResponse.output(payload_response, 400)

    except Exception as e:
        app.logger.error(f"Error getting completion: {str(e)}")

        if LOG_LEVEL == "DEBUG":
            app.logger.error(traceback.format_exc())

        payload_response = ApiResponse.payload(False, 500, "Internal server error")
        return ApiResponse.output(payload_response, 500)


@app.route("/api/convert-voice/<engine>", methods=["POST"])
def convert_voice(engine):

    try:
        params = dict(request.form)
        create_args = {key: params[key] for key in params if not key.startswith("__")}

        if "audio" in request.files:
            audio = request.files["audio"]
            app.logger.debug(f"Received audio file: {audio.filename}")
            filename = secure_filename(audio.filename)
            file_name = generate_random_filename(
                app.config["UPLOAD_FOLDER"] + "/", filename
            )
            audio.save(file_name)

            if engine == "openvoicev1" or engine == "openvoicev2":

                output_file = generate_random_filename("", "wav")
                client = OpenVoiceApiClient(
                    base_url=OPENVOICE_API_URL, log_level=LOG_LEVEL
                )
                create_args["audio_file"] = file_name
                create_args["encode"] = True
                create_args["response_format"] = "base64"
                audio_base64, status_code, response_message = client.change_voice(
                    **create_args
                )
                if status_code == 200:
                    app.logger.info(
                        f"Audio data generated successfully, bytes: {len(audio_base64)}"
                    )
                    payload_response = ApiResponse.payload(
                        True if status_code == 200 else False,
                        status_code,
                        response_message,
                        {"audio_base64": audio_base64},
                    )
                    return ApiResponse.output(payload_response)
                else:
                    app.logger.error(f"Failed to generate audio data")
                    payload_response = ApiResponse.payload(
                        False, 500, "Internal server error"
                    )
                    return ApiResponse.output(payload_response, 500)

            else:
                payload_response = ApiResponse.payload(
                    False, 400, f"VC engine {engine} not supported"
                )
                return ApiResponse.output(payload_response, 400)

        else:
            payload_response = ApiResponse.payload(
                False, 400, f"No audio file was sent"
            )
            return ApiResponse.output(payload_response, 500)

    except Exception as e:
        app.logger.error(f"Error getting completion: {str(e)}")

        if LOG_LEVEL == "DEBUG":
            app.logger.error(traceback.format_exc())

        payload_response = ApiResponse.payload(False, 500, "Internal server error")
        return ApiResponse.output(payload_response, 500)


@app.route("/api/health-check", methods=["POST"])
def health_check():

    data = request.json
    # check_all = data.get("checkAll")

    response_message = ""
    open_voice_server = data.get("checkOpenVoiceServer")

    if open_voice_server:
        try:
            response = requests.get(OPENVOICE_API_URL)
            response.raise_for_status()  # Raise exception for bad responses (4xx or 5xx)
            result = response.json()
            models_v1 = result["result"]["data"]["models_v1"]
            processed_models_v1 = [model.split(":")[0].lower() for model in models_v1]
            models_v2 = result["result"]["data"]["models_v2"]
            processed_models_v2 = [model.lower() for model in models_v2]
            response_message += (
                "🟢 OpenVoice: Server is up and running using "
                f"{result['result']['data']['device_v1']} for v1 and "
                f"{result['result']['data']['device_v2']} for v2 with "
                f"loaded models v1 {processed_models_v1} and "
                f"v2 {processed_models_v2}\n\n"
            )

        except Exception as err:
            response_message += "🔴 OpenVoice: Server was not reachable\n\n"

    open_ai_completion_request = data.get("tryOpenAICompletion")

    if open_ai_completion_request:

        args = {}
        args["model"] = "gpt-4o"
        response_data = OpenAiClient.completion("Hi, how do you do?", [], 10, args)
        response_json = json.loads(response_data.data.decode("utf-8"))
        result = response_json["result"]["success"]
        if result:
            response_message += "🟢 OpenAI: Completion request successful\n\n"
        else:
            response_message += (
                "🔴 OpenAI: " + response_json["result"]["message"] + "\n\n"
            )

    ollama_completion_request = data.get("checkOllamaServer")

    if ollama_completion_request:
        args = {}
        args["model"] = "llama3"
        response_data = OpenAiClient.completion(
            "Hi, how do you do?",
            [],
            10,
            args,
            f"{OLLAMA_API_URL}/v1",
        )
        response_json = json.loads(response_data.data.decode("utf-8"))
        result = response_json["result"]["success"]
        if result:
            response_message += "🟢 Ollama: Completion request successful\n\n"
        else:
            response_message += (
                "🔴 Ollama: " + response_json["result"]["message"] + "\n\n"
            )

    lmstudio_completion_request = data.get("checkLMStudioServer")

    if lmstudio_completion_request:
        args = {}
        args["model"] = "local-model"
        response_data = OpenAiClient.completion(
            "Hi, how do you do?",
            [],
            10,
            args,
            f"{LMSTUDIO_API_URL}/v1",
        )
        response_json = json.loads(response_data.data.decode("utf-8"))
        result = response_json["result"]["success"]
        if result:
            response_message += "🟢 LMStudio: Completion request successful\n\n"
        else:
            response_message += (
                "🔴 LMStudio: " + response_json["result"]["message"] + "\n\n"
            )

    elevenlabs_tts_request = data.get("checkElevenLabsCredits")

    if elevenlabs_tts_request:

        try:
            if ELEVENLABS_API_KEY:
                client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            else:
                client = ElevenLabs()

            audio = client.generate(
                text="Hi, how do you do?",
                voice="Rachel",
                model="eleven_multilingual_v2",
            )
            audio_bytes = b"".join(audio)
            response_message += (
                "🟢 ElevenLabs: Generated test audio file of "
                + str(len(audio_bytes))
                + " bytes"
                + "\n\n"
            )

        except Exception as err:
            response_message += "🔴 ElevenLabs: " + str(err) + " <<<\n\n"

    fw_server = data.get("checkFWServer")

    if fw_server:
        try:
            response = requests.get(FAST_WHISPER_API_URL)
            response.raise_for_status()  # Raise exception for bad responses (4xx or 5xx)
            data = response.json()
            response_message += (
                f"🟢 Fast Whisper: Server is up and running using "
                + f"{data['result']['data']['device']}"
                + f" with loaded models {data['result']['data']['models']}\n\n"
            )

        except Exception as err:
            response_message += "🔴 Fast Whisper: Server was not reachable\n\n"

    payload_response = ApiResponse.payload(
        True, 200, "Health check results", {"message": response_message}
    )
    return ApiResponse.output(payload_response, 200)


import mimetypes


@app.route("/api/concatenate-audio", methods=["POST"])
def concatenate_audio():
    try:

        if not request.files.getlist("audio"):
            return jsonify({"error": "No audio files found"}), 400

        random_folder_name = str(uuid.uuid4())
        output_dir = os.path.join(app.config["UPLOAD_FOLDER"], random_folder_name)
        os.makedirs(output_dir, exist_ok=True)
        saved_files = []
        for idx, audio_file in enumerate(request.files.getlist("audio")):
            mime_type = audio_file.mimetype
            file_path = os.path.join(output_dir, f"audio_{idx + 1}.wav")

            if mime_type == "audio/webm":
                temp_file_path = os.path.join(output_dir, f"temp_audio_{idx + 1}.webm")
                audio_file.save(temp_file_path)
                audio = AudioSegment.from_file(temp_file_path, format="webm")
                audio.export(file_path, format="wav")
                os.remove(temp_file_path)
                saved_files.append(file_path)
            else:
                audio_file.save(file_path)
                saved_files.append(file_path)

        combined_audio = None
        for file_path in saved_files:
            audio_segment = AudioSegment.from_wav(file_path)

            if combined_audio:
                combined_audio += audio_segment
            else:
                combined_audio = audio_segment

        final_filename = "conversation.wav"
        combined_audio_path = os.path.join(output_dir, final_filename)
        combined_audio.export(combined_audio_path, format="wav")
        with open(combined_audio_path, "rb") as f:
            blob_data = io.BytesIO(f.read())
        return send_file(
            blob_data,
            mimetype="audio/wav",
            as_attachment=True,
            download_name=final_filename,
        )

    except Exception as e:
        print("Error: ", e)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/", methods=["GET", "POST"])
def proxy_to_panel_url():

    base_url = WEB_PANEL_ADDRESS
    proxy_url = f"{base_url}"
    response = requests.get(proxy_url)

    if response.status_code == 200:
        return Response(response.content, content_type=response.headers["Content-Type"])

    else:
        return (
            f"Error: Failed to fetch data from {proxy_url}. Status code: {response.status_code}",
            response.status_code,
        )


@app.route("/<path:subpath>", methods=["GET", "POST"])
def proxy_to_panel_url_paths(subpath):

    if request.path.startswith("/api/"):
        return jsonify({"error": "API endpoint not found"}), 404

    base_url = WEB_PANEL_ADDRESS
    proxy_url = f"{base_url}/{subpath}"
    response = requests.get(proxy_url)

    if response.status_code == 200:
        return Response(response.content, content_type=response.headers["Content-Type"])

    else:
        return (
            f"Error: Failed to fetch data from {proxy_url}. Status code: {response.status_code}",
            response.status_code,
        )


@app.route("/static/<path>/<subpath>", methods=["GET", "POST"])
def proxy_to_panel_url_static(path, subpath):

    if request.path.startswith("/api/"):
        return jsonify({"error": "API endpoint not found"}), 404

    base_url = WEB_PANEL_ADDRESS
    proxy_url = f"{base_url}/static/{path}/{subpath}"
    response = requests.get(proxy_url)

    if response.status_code == 200:
        return Response(response.content, content_type=response.headers["Content-Type"])

    else:
        return (
            f"Error: Failed to fetch data from {proxy_url}. Status code: {response.status_code}",
            response.status_code,
        )


# Handle 404 errors
@app.errorhandler(404)
def page_not_found(error):

    msg = f" > No service is associated with the url => {request.method}:{request.url}"
    app.logger.error(msg)
    payload_response = ApiResponse.not_found(msg, {})
    return ApiResponse.output(payload_response, 404)


if __name__ == "__main__":
    app.run(host=SERVER_ADDRESS, port=SERVER_PORT, debug=True)
