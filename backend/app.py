import logging, colorlog, os, traceback, sys, base64, requests, json, io, magic, uuid, urllib, time
from flask import Flask, request, redirect, Response, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from models.Response import Response as ApiResponse
from models.OpenAiClient import OpenAiClient
from datetime import datetime
from elevenlabs.client import ElevenLabs
from openvoice_api_client.client import OpenVoiceApiClient
from werkzeug.utils import secure_filename
from flask import jsonify, send_file
from pydub import AudioSegment
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather

# Load environment variables from .env file
load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
SERVER_ADDRESS = os.getenv("SERVER_ADDRESS", "0.0.0.0")
SERVER_PORT = os.getenv("SERVER_PORT", 5000)
OPENVOICE_API_URL = os.getenv("OPENVOICE_API_URL", "http://127.0.0.1:5001")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434")
LMSTUDIO_API_URL = os.getenv("LMSTUDIO_API_URL", "http://127.0.0.1:1234")
FAST_WHISPER_API_URL = os.getenv("FAST_WHISPER_API_URL", "http://127.0.0.1:5003")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
EXTERNAL_ADDRESS = os.getenv("EXTERNAL_ADDRESS")
WEB_PANEL_ADDRESS = os.getenv("WEB_PANEL_ADDRESS", "http://127.0.0.1:3000")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "appsecretkey")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/tmp")

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = APP_SECRET_KEY
CORS(app)
socketio = SocketIO(app)

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
    request.start_time = time.time()


@app.after_request
def add_header(response):
    if hasattr(request, "start_time"):
        elapsed_time = time.time() - request.start_time
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


@app.route("/api/speech-to-text/<engine>", methods=["POST"])
def speech_to_text(engine):

    test_file = False

    try:
        params = dict(request.form)
        create_args = {key: params[key] for key in params if not key.startswith("__")}

        if "test" in create_args:
            create_args.pop("test")
            test_file = True

        if "audio" in request.files or test_file:

            if test_file:
                audio_file = open("outputs/test.wav", "rb")
            else:
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

    test_file = False

    try:
        params = dict(request.form)
        create_args = {key: params[key] for key in params if not key.startswith("__")}

        if "test" in create_args:
            create_args.pop("test")
            test_file = True

        if "audio" in request.files or test_file:

            if test_file:
                file_name = "outputs/test.wav"
            else:
                audio = request.files["audio"]
                app.logger.debug(f"Received audio file: {audio.filename}")
                filename = secure_filename(audio.filename)
                file_name = generate_random_filename(
                    app.config["UPLOAD_FOLDER"] + "/", filename
                )
                audio.save(file_name)

            if engine == "openvoicev1" or engine == "openvoicev2":

                # output_file = generate_random_filename("", "wav")
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


def emit_event(message, debugLevel=0, ended=False):
    socketio.emit(
        "event_log", {"message": message, "debugLevel": debugLevel, "ended": ended}
    )


# Route to initiate a phone call
@app.route("/api/call", methods=["POST"])
def call():

    data = request.json
    to_number = data.get("to")
    emit_event(f"Initiating call to {to_number}", 1)
    system_message = urllib.parse.quote(data.get("systemMessage"))
    tts_config_json = urllib.parse.quote(str(data.get("ttsConfig")))
    llm_config_json = urllib.parse.quote(str(data.get("llmConfig")))
    stt_config_json = urllib.parse.quote(str(data.get("sttConfig")))
    vc_config_json = urllib.parse.quote(str(data.get("vcConfig")))
    ttsSource = data.get("ttsSource")
    llmSource = data.get("llmSource")
    sttSource = data.get("sttSource")
    vcSource = data.get("vcSource")
    maxHistory = data.get("maxHistory")
    url = (
        f"{EXTERNAL_ADDRESS}/api/handle-call?start_conversation=1&"
        + f"system_message={system_message}&"
        + f"ttsConfig={tts_config_json}&"
        + f"llmConfig={llm_config_json}&"
        + f"sttConfig={stt_config_json}&"
        + f"vcConfig={vc_config_json}&"
        + f"ttsSource={ttsSource}&"
        + f"llmSource={llmSource}&"
        + f"sttSource={sttSource}&"
        + f"vcSource={vcSource}&"
        + f"maxHistory={maxHistory}"
    )
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    call = client.calls.create(
        url=url,
        to=to_number,
        from_=TWILIO_NUMBER,
        status_callback=f"{EXTERNAL_ADDRESS}/api/call-status",
        status_callback_event=["completed", "ringing", "in-progress", "initiated"],
        record=True,
    )
    emit_event(f"Call initiated: {call.sid}", 0)
    payload_response = ApiResponse.payload(
        True,
        200,
        f"Call initiated: {call.sid}",
    )
    return ApiResponse.output(payload_response)


# Route to handle incoming voice call
@app.route("/api/handle-call", methods=["GET", "POST"])
def handle_call():

    start_conversation = request.args.get("start_conversation", False)

    if start_conversation:
        emit_event("Conversation Started", 1)
        session["conversation_ended"] = False
        session["system_message"] = urllib.parse.unquote(
            request.args.get("system_message")
        )
        tts_config_str = urllib.parse.unquote(request.args.get("ttsConfig"))
        llm_config_str = urllib.parse.unquote(request.args.get("llmConfig"))
        stt_config_str = urllib.parse.unquote(request.args.get("sttConfig"))
        # vc_config = request.args.get("vcConfig")  # No need for decoding if it's None or actual value
        session["ttsSource"] = request.args.get("ttsSource")
        session["llmSource"] = request.args.get("llmSource")
        session["sttSource"] = request.args.get("sttSource")
        session["vcSource"] = request.args.get("vcSource")
        session["maxHistory"] = request.args.get("maxHistory")
        session["conversation_history"] = [
            {
                "role": "system",
                "content": session["system_message"],
            }
        ]
        try:
            session["ttsConfig"] = (
                json.loads(tts_config_str.replace("'", '"')) if tts_config_str else {}
            )
            session["llmConfig"] = (
                json.loads(llm_config_str.replace("'", '"')) if llm_config_str else {}
            )
            session["sttConfig"] = (
                json.loads(stt_config_str.replace("'", '"')) if stt_config_str else {}
            )

        except json.JSONDecodeError as e:
            return jsonify({"error": "Failed to parse JSON", "message": str(e)}), 400

    response = VoiceResponse()
    gather = Gather(input="speech", action="/api/process-call", speechTimeout="auto")
    response.append(gather)
    return str(response)

    """response.record(
        action="/api/process-call",
        playBeep=False,
        timeout=1,
        # recording_status_callback="/api/process-call",
        # recording_status_callback_method="POST",
        # recording_status_callback_event="completed",
    )
    return str(response)"""


@app.route("/api/handle-speech", methods=["POST"])
def handle_speech():

    print("SPEECH")
    print(session)

    # Check if speech was detected
    speech_result = request.form.get("SpeechResult")

    response = VoiceResponse()
    if speech_result:
        # If speech was detected, start recording
        response.record(
            action="/api/process-call",
            playBeep=False,
            timeout=1,
            # recording_status_callback="/api/process-call",
            # recording_status_callback_method="POST",
        )
    else:
        # If no speech was detected, redirect back to gather speech
        response.redirect("/api/handle-call")

    return str(response)


# Route to process voice call
@app.route("/api/process-call", methods=["POST"])
def process_call():

    if session.get("conversation_ended", False):
        return "", 200

    conversation_history = session.get("conversation_history", [])

    try:
        """recording_url = request.form.get("RecordingUrl")
        start_time = time.time()
        time.sleep(1)
        recording_response = requests.get(
            recording_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        )
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        formatted_duration = f"{duration_ms:.4f} ms"
        if recording_response.status_code == 200:
            random_filename = UPLOAD_FOLDER + "/" + str(uuid.uuid4()) + ".wav"
            with open(random_filename, "wb") as f:
                f.write(recording_response.content)
            emit_event(
                f"({formatted_duration}ms) User STT audio file created: {random_filename}",
                0,
            )
        else:
            response = VoiceResponse()
            response.say("Can you please repeat that.")
            emit_event(
                f"({formatted_duration}ms) User STT result: Can you please repeat that.",
                0,
            )
            response.redirect("/api/handle-call")
            return str(response)

        files = {
            "audio": ("audio.webm", recording_response.content, "audio/webm"),
        }
        sttSource = session.get("sttSource")
        params = session.get("sttConfig")
        data = {}
        for key, value in params.items():
            data[key] = value
        response = requests.post(
            EXTERNAL_ADDRESS + "/api/speech-to-text/" + sttSource,
            files=files,
            data=data,
        )
        elapsed_time = response.headers.get("X-Elapsed-Time")
        formatted_duration = f"{float(elapsed_time):.4f} ms"
        if response.status_code == 200:
            data = response.json()
            transcription_text = data["result"]["data"]["text"]
            emit_event(
                f"({formatted_duration}ms) User STT result: {transcription_text}", 0
            )
        else:
            response = VoiceResponse()
            response.say("Can you please repeat that.")
            emit_event(
                f"({formatted_duration}ms) User STT result: Can you please repeat that.",
                0,
            )
            response.redirect("/api/handle-call")
            return str(response)"""

        transcription_text = (
            request.form.get("SpeechResult", "No speech detected").strip().lower()
        )
        emit_event(f"(0.0000ms) User STT result: {transcription_text}", 0)

        if transcription_text == "no speech detected" or not transcription_text:
            response = VoiceResponse()
            response.say("Can you please repeat that.")
            emit_event(
                f"({formatted_duration}ms) Bot STT result: Can you please repeat that.",
                0,
            )
            response.redirect("/api/handle-call")
            return str(response)

        llmSource = session.get("llmSource")
        params = session.get("llmConfig")
        params["__conversation_history"] = conversation_history
        params["__message"] = transcription_text
        params["__max_conversation_history"] = int(session.get("maxHistory"))
        response = requests.post(
            EXTERNAL_ADDRESS + "/api/chat/" + llmSource, json=params
        )
        data = response.json()
        elapsed_time = response.headers.get("X-Elapsed-Time")
        formatted_duration = f"{float(elapsed_time):.4f} ms"

        if response.status_code == 200:
            emit_event(
                f"({formatted_duration}ms) Bot LLM result: {data['result']['data']['response_message']}",
                0,
            )
            session["conversation_history"] = data["result"]["data"][
                "conversation_history"
            ]
        else:
            response = VoiceResponse()
            response.say("Can you please repeat that.")
            emit_event(
                f"({formatted_duration}ms) Bot STT result: Can you please repeat that.",
                0,
            )
            response.redirect("/api/handle-call")
            return str(response)

        if data["result"]["data"]["response_message"]:
            ttsSource = session.get("ttsSource")
            params = session.get("ttsConfig")
            params["input"] = data["result"]["data"]["response_message"]
            response = requests.post(
                EXTERNAL_ADDRESS + "/api/text-to-speech/" + ttsSource, json=params
            )
            elapsed_time = response.headers.get("X-Elapsed-Time")
            formatted_duration = f"{float(elapsed_time):.4f} ms"

            if response.status_code == 200:
                data = response.json()
                emit_event(
                    f"({formatted_duration}ms) Bot TTS result: {data['result']['message']}",
                    0,
                )
                audio_data = base64.b64decode(data["result"]["data"]["audio_base64"])
                output_file = generate_random_filename(
                    app.config["UPLOAD_FOLDER"] + "/", "wav"
                )
                with open(output_file, "wb") as f:
                    f.write(audio_data)
                response = VoiceResponse()
                response.play(f"{EXTERNAL_ADDRESS}/play-audio?file={output_file}")
                response.redirect("/api/handle-call")
                return str(response)

            return Response()

    except Exception as e:
        app.logger.error(f"Error uploading audio: {str(e)}")

        if LOG_LEVEL == "DEBUG":
            app.logger.error(traceback.format_exc())

        emit_event(f"An error occurred: {e}", 0)
        response = VoiceResponse()
        response.say("Can you please repeat that.")
        response.redirect("/api/handle-call")
        return str(response)


@app.route("/api/call-status", methods=["POST"])
def status_callback():
    # call_sid = request.form["CallSid"]
    call_status = request.form["CallStatus"]
    # print(f"Call SID: {call_sid}, Status: {call_status}")

    if call_status == "completed":
        emit_event("Call ended", 0, True)
        session["conversation_ended"] = True
    elif call_status == "initiated":
        emit_event("Dialing the number", 0)
    elif call_status == "ringing":
        emit_event("Phone ringing", 0)
    elif call_status == "in-progress":
        emit_event("Call in progress", 0)

    return "", 200


@app.route("/play-audio")
def play_audio():
    file_path = request.args.get("file")
    return send_file(file_path, mimetype="audio/wav")


# Handle 404 errors
@app.errorhandler(404)
def page_not_found(error):

    msg = f" > No service is associated with the url => {request.method}:{request.url}"
    app.logger.error(msg)
    payload_response = ApiResponse.not_found(msg, {})
    return ApiResponse.output(payload_response, 404)


if __name__ == "__main__":
    socketio.run(app, host=SERVER_ADDRESS, port=SERVER_PORT, debug=True)
