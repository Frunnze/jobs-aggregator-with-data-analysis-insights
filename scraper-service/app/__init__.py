from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from flask_cors import CORS
from flask_apscheduler import APScheduler
import redis
import requests
import sys


# set configuration values
class Config:
    SCHEDULER_API_ENABLED = True

db = SQLAlchemy()
scheduler = APScheduler()
redis_client = redis.StrictRedis(
    host='localhost',  # Redis server hostname or IP address
    port=6379,         # Redis server port
    db=0,              # Database number (default is 0)
    decode_responses=True  # Decodes responses to strings (instead of bytes)
)

load_dotenv()
# DATABASE_URL = os.environ["DATABASE_URL"]

def create_app():
    # Create and configure the flask app
    app = Flask(__name__)
    app.config.from_object(Config())
    app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY")

    # Define the cross origin resource sharing
    CORS(app)

    # scraped real-estate data
    #app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost:5432/scraped_real_estate_data"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///scraped_data.db"
    db.init_app(app)

    # Register the apis
    from .apis.data import data
    app.register_blueprint(data)

    # Create the dbs and add initial tables values
    from . import models
    with app.app_context():
        db.create_all()

    # Start scheduler
    scheduler.init_app(app)
    from .tasks.scrape_jobs_from_rabota_md import scrape_jobs_from_rabota_md
    scheduler.start()

    # Register in the service discovery
    address =  os.getenv("SCRAPER_SERVICE_ADDRESS")
    port = os.getenv("SCRAPER_SERVICE_PORT")
    response = requests.post(
        url=os.getenv("SERVICE_DISCOVERY") + "/add-service", 
        json={
            "name": "scraper-service", 
            "address": address,
            "port": port
        }
    )
    if not (response.status_code >= 200 and response.status_code < 300): 
        print(f"Scraper service: {address}:{port} could not register to the service discovery!")
        sys.exit(1)

    return app