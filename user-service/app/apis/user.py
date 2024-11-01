from flask import request, jsonify, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
import time
import json 
from dotenv import load_dotenv
import os

from .. import db
from ..models import User


user = Blueprint("user", __name__)
REQUEST_TIMEOUT = 5
load_dotenv()
USER_SERVICE_ADDRESS = os.getenv("USER_SERVICE_ADDRESS")
USER_SERVICE_ADDRESS = USER_SERVICE_ADDRESS.replace("http://", "ws://")
USER_SERVICE_PORT = os.getenv("SOCKET_PORT")

@user.before_request
def start_timer():
    """Start the timer before each request."""
    request.start_time = time.time()

@user.after_request
def check_timeout(response):
    """Check if the request processing exceeded the timeout."""
    elapsed_time = time.time() - request.start_time
    if elapsed_time > REQUEST_TIMEOUT:
        response.status_code = 408
        response.data = json.dumps({"error": "Request timed out"})
        response.headers['Content-Type'] = 'application/json'
    return response


@user.route('/sign-up', methods=['POST'])
def sign_up():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    # Validation checks
    if "@" not in email:
        return jsonify({"msg": "Invalid email"}), 400
    if len(password) < 6:
        return jsonify({"msg": "Password too short"}), 400
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"msg": "User already exists"}), 409
    
    # Hash the password and create a new user
    hashed_password = generate_password_hash(password)
    new_user = User(username=name, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "msg": f"Successful sign up!", 
        "user_id": new_user.id,
        "websocket": f"{USER_SERVICE_ADDRESS}:{USER_SERVICE_PORT}"
    }), 201


@user.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Check if user exists in the database
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "Invalid email or password"}), 401

    # Verify password
    if not check_password_hash(user.password, password):
        return jsonify({"msg": "Invalid email or password"}), 401

    time.sleep(10)
    return jsonify({
        "msg": "Successful login!",
        "user_id": user.id,
        "websocket": f"{USER_SERVICE_ADDRESS}:{USER_SERVICE_PORT}"
    }), 500


@user.route('/get-subscriptions/<int:user_id>', methods=['GET'])
def get_user_subscriptions(user_id):
    user = User.query.get_or_404(user_id)
    subscriptions = user.subscriptions
    return jsonify([sub.room_name for sub in subscriptions]), 200


@user.route('/status', methods=['GET'])
def status():
    return jsonify({"msg": "Service is running"}), 200