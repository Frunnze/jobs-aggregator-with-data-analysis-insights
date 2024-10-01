from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from flask_cors import CORS
from flask_socketio import SocketIO
import redis


db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")
redis_client = redis.StrictRedis(
    host='localhost',  # Redis server hostname or IP address
    port=6379,         # Redis server port
    db=0,              # Database number (default is 0)
    decode_responses=True  # Decodes responses to strings (instead of bytes)
)

load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

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
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL#"sqlite:///user.db"
    db.init_app(app)

    # Register the apis
    from .apis.user import user
    from .apis.broadcast import broadcast
    app.register_blueprint(user)
    app.register_blueprint(broadcast)

    # Create the dbs and add initial tables values
    with app.app_context():
        db.create_all()

    return app