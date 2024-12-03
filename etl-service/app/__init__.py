from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from flask_cors import CORS
from flask_apscheduler import APScheduler
from prometheus_flask_exporter import PrometheusMetrics, NO_PREFIX
import requests
import sys


# set configuration values
class Config:
    SCHEDULER_API_ENABLED = True

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

db = SQLAlchemy()
scheduler = APScheduler()


def create_app():
    # Create and configure the flask app
    app = Flask(__name__)
    app.config.from_object(Config())
    app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY")

    # Define the cross origin resource sharing
    CORS(app)

    # scraped real-estate data
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    #app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///scraped_data.db"
    db.init_app(app)

    # Connect Prometheus
    metrics = PrometheusMetrics(app, defaults_prefix=NO_PREFIX)
    metrics.info('app_info', 'Application info', version='1.0.3')

    # Create the dbs and add initial tables values
    with app.app_context():
        from . import models
        db.create_all()

        @app.route('/status', methods=['GET'])
        def status():
            return jsonify({"msg": "Service is running"}), 200

        
    scheduler.init_app(app)
    from .tasks.save_in_warehouse import save_in_warehouse  
    scheduler.start()

    # Register in the service discovery
    address =  os.getenv("ETL_SERVICE_ADDRESS")
    port = os.getenv("ETL_SERVICE_PORT")
    response = requests.post(
        url=os.getenv("SERVICE_DISCOVERY") + "/add-service", 
        json={
            "name": "etl-service", 
            "address": address,
            "port": port
        }
    )
    if not (response.status_code >= 200 and response.status_code < 300): 
        print(f"Scraper service: {address}:{port} could not register to the service discovery!")
        sys.exit(1)

    return app