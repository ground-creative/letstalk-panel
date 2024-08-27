import colorlog, time, warnings
from flask import request, redirect, render_template, abort, g, send_file
from flask_cors import CORS
from flask_socketio import SocketIO
from apiflask import APIFlask
from models.Response import Response as ApiResponse
from models.OpenAiClient import OpenAiClient
from config.env import EnvConfig
from config.docs import DocsConfig
from config.models import ModelsConfig
from config.security import SecurityConfig
from config.services import services
from utils.spec import update_spec
from decorators.UserAuth import validate_token
from utils.blueprints import register_blueprints
from utils.get_config import get_config
from db.db import db
from flask.cli import with_appcontext
from utils.get_models import import_models

# Filter pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

imported_models = import_models(ModelsConfig)


socketio = SocketIO()


def create_app():
    app = APIFlask(__name__, docs_path=None, spec_path="/docs/openapi-backend.json")
    app.config.from_object(EnvConfig)
    app.config.update(get_config(DocsConfig))
    app.config.update(get_config(SecurityConfig))
    app.secret_key = app.config.get("APP_SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+mysqlconnector://{app.config.get('MYSQL_USER')}:{app.config.get('MYSQL_PASS')}@{app.config.get('MYSQL_HOST')}:{app.config.get('MYSQL_PORT')}/{app.config.get('MYSQL_DB')}"
    )

    # Initialize extensions with the app
    db.init_app(app)
    socketio.init_app(app)
    CORS(app)

    # Configure logging
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
    logger.setLevel(app.config.get("LOG_LEVEL"))

    # Set up logging for ApiResponse and OpenAiClient
    ApiResponse.set_logger(app.logger)
    OpenAiClient.set_params(
        app.config.get("OPENAI_API_KEY"), app.logger, app.config.get("LOG_LEVEL")
    )

    # Register blueprints
    register_blueprints(app, services)

    # Custom error and spec processors
    @app.error_processor
    def my_error_processor(error):
        validation_error_code = app.config.get("VALIDATION_ERROR_STATUS_CODE", 422)
        if validation_error_code == error.status_code and "json" in error.detail:
            json_content = error.detail.pop("json")
            final_result = {"details": json_content}
            error.detail = final_result
        payload_response = ApiResponse.payload_v2(
            error.status_code, error.message, error.detail
        )
        return payload_response, error.status_code, error.headers

    @app.spec_processor
    def update_spec_handler(spec):
        return update_spec(spec)

    if app.config.get("WEB_PANEL_ADDRESS"):

        @app.route("/", methods=["GET"])
        def handle_redirect_to_panel():
            return redirect("/panel", code=302)

    @app.before_request
    def log_request_info():
        app.logger.info(
            f"Started processing {request.method} request from {request.remote_addr} => {request.url}"
        )
        if request.path == "/docs/openapi-backend.json":
            accessToken = request.cookies.get("accessToken", None)
            is_invalid = validate_token(accessToken)
            if is_invalid:
                abort(401)
            if (
                "is_superadmin" not in g.jwt_payload
                or not g.jwt_payload["is_superadmin"]
            ):
                abort(401)
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

    # ?????????????????
    @app.route("/play-audio")
    def play_audio():
        file_path = request.args.get("file")
        return send_file(file_path, mimetype="audio/wav")

    # Handle 404 errors
    @app.errorhandler(404)
    def page_not_found(error):
        if request.path.startswith("/api/") or request.path.startswith("/backend"):
            msg = f" > No service is associated with the url => {request.method}:{request.url}"
            app.logger.error(msg)
            if request.path.startswith("/api/v2"):
                payload_response = ApiResponse.not_found_v2(msg, {})
            else:
                payload_response = ApiResponse.not_found(msg, {})
            return ApiResponse.output(payload_response, 404)
        else:
            return render_template("404.html"), 404

    # Create database
    @app.cli.command("create-db")
    @with_appcontext
    def create_db():
        """Create the database tables."""
        db.create_all()
        print("Database tables created.")

    return app


if __name__ == "__main__":
    app = create_app()
    socketio.run(
        app,
        host=app.config.get("SERVER_ADDRESS"),
        port=app.config.get("SERVER_PORT"),
        debug=True,
    )
