from pymongo import MongoClient
from flask import session, current_app as app, g
import secrets, string


def get_db():
    with app.app_context():
        client = app.config["SESSION_MONGODB"]
        db = client[app.config["SESSION_MONGODB_DB"]]
        return db


def get_collection():
    """
    Retrieve the MongoDB collection based on the Flask application configuration.
    """
    db = get_db()
    collection = db[
        app.config["SESSION_MONGODB_COLLECT"]
    ]  # Access the specific collection
    return collection


def get_session(session_id):
    """
    Retrieve or create session data based on the session_param.
    """
    collection = get_collection()
    session_data = collection.find_one({"_id": session_id})

    if not session_data:
        session_data = {"_id": session_id}
        collection.insert_one(session_data)

    return session_data


def save_session(session_data):
    """
    Save or update session data in MongoDB or Flask's default session.
    """
    if "_id" in session_data:
        collection = get_collection()
        collection.update_one(
            {"_id": session_data["_id"]}, {"$set": session_data}, upsert=True
        )
    else:
        session.update(session_data)


def generate_session_id(prefix="", length=32):
    """Generate a secure session ID with the given length (in bytes)."""
    characters = string.ascii_letters + string.digits + "_"
    session_id = "".join(secrets.choice(characters) for _ in range(length))

    return prefix + session_id
