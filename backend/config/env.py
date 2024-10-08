import os
from dotenv import load_dotenv

load_dotenv()


class EnvConfig:
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    DEBUG_APP = os.getenv("DEBUG_APP", 1)
    SERVER_ADDRESS = os.getenv("SERVER_ADDRESS", "0.0.0.0")
    SERVER_PORT = os.getenv("SERVER_PORT", 5000)
    BACKEND_PREFIX = os.getenv("BACKEND_PREFIX", "/backend")
    WEB_PANEL_ADDRESS = os.getenv("WEB_PANEL_ADDRESS", "")
    WEB_PANEL_PORT = os.getenv("WEB_PANEL_PORT", "3000")
    WEB_PANEL_PREFIX = os.getenv("WEB_PANEL_PREFIX", "/panel")
    APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "appsecretkey")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/tmp")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "letstalk")
    MYSQL_PASS = os.getenv("MYSQL_PASS", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "letstalk")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
    API_AUDIENCE = os.getenv("API_AUDIENCE", "https://letstalk")
    ALGORITHMS = os.getenv("ALGORITHMS", "RS256").split(",")
    SERVERS = [{"url": "https://letstalk.serveo.net"}]

    # @ Deprecated
    EXTERNAL_ADDRESS = os.getenv("EXTERNAL_ADDRESS", "")
    OPENVOICE_API_URL = os.getenv("OPENVOICE_API_URL", "http://127.0.0.1:5001")
    OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434")
    LMSTUDIO_API_URL = os.getenv("LMSTUDIO_API_URL", "http://127.0.0.1:1234")
    FAST_WHISPER_API_URL = os.getenv("FAST_WHISPER_API_URL", "http://127.0.0.1:5003")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    MONGODB_ADDRESS = os.getenv("MONGODB_ADDRESS", "mongodb://localhost:27017")
    SESSION_MONGODB_DB = os.getenv("SESSION_MONGODB_DB", "letstalk")
    VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "/vector_store")
    KNOWLEDGE_BASE_PATH = os.getenv("KNOWLEDGE_BASE_PATH", "/knowledge_base")
