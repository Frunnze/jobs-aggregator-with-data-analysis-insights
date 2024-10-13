from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from flask_cors import CORS
from flask_socketio import SocketIO
import redis
import sys
import requests


db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")
redis_client = redis.StrictRedis(
    host='localhost',  # Redis server hostname or IP address
    port=6379,         # Redis server port
    db=0,              # Database number (default is 0)
    decode_responses=True  # Decodes responses to strings (instead of bytes)
)

load_dotenv()
#DATABASE_URL = os.environ["DATABASE_URL"]

def create_app():
    # Create and configure the flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'

    # Define the cross origin resource sharing
    CORS(app)

    # Initiate the web socket
    socketio.init_app(app)
    from . import websocket

    # scraped real-estate data
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///user.db"
    db.init_app(app)

    # Register the apis
    from .apis.user import user
    from .apis.broadcast import broadcast
    app.register_blueprint(user)
    app.register_blueprint(broadcast)

    # Create the dbs and add initial tables values
    with app.app_context():
        db.create_all()

    # Register in the service discovery
    address =  os.getenv("USER_SERVICE_ADDRESS")
    port = os.getenv("USER_SERVICE_PORT")
    response = requests.post(
        url=os.getenv("SERVICE_DISCOVERY") + "/add-service", 
        json={
            "name": "user-service", 
            "address": address,
            "port": port
        }
    )
    if not (response.status_code >= 200 and response.status_code < 300): 
        print(f"User service: {address}:{port} could not register to the service discovery!")
        sys.exit(1)

    return app