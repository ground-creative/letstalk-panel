import requests
from flask import Blueprint, current_app as app
from models.Response import Response as ApiResponse

users_bp = Blueprint("users_blueprint", __name__)

from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.sql import insert
import random
import string


# Function to generate a random string
def generate_random_string(length=10):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


@users_bp.route("/user", methods=["POST"])
def new_user():

    print("DDDDDDDDDDDDDDDD")
    print("DDDDDDDDDDDDDDDD")
    print("DDDDDDDDDDDDDDDD")
    print("DDDDDDDDDDDDDDDD")

    # Database connection
    engine = create_engine(
        f"mysql+mysqlconnector://{app.config.get('MYSQL_USER')}:{app.config.get('MYSQL_PASS')}@{app.config.get('MYSQL_HOST')}/{app.config.get('MYSQL_DB')}"
    )
    connection = engine.connect()
    metadata = MetaData()
    table_name = Table("workspaces", metadata, autoload_with=engine)
    sid = generate_random_string()
    insert_query = insert(table_name).values(sid=sid, name="Default", status=1)
    connection.execute(insert_query)
    connection.commit()

    workspaces = {sid: {"role": "admin", "name": "Default"}}

    payload_response = ApiResponse.payload(True, 200, "new user created", workspaces)
    return ApiResponse.output(payload_response, 200)
