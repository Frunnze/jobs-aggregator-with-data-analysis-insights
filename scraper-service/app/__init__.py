from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from flask_cors import CORS
from flask_apscheduler import APScheduler
import redis
import requests
import sys
from prometheus_flask_exporter import PrometheusMetrics, NO_PREFIX


# set configuration values
class Config:
    SCHEDULER_API_ENABLED = True

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

db = SQLAlchemy()
scheduler = APScheduler()
redis_client = redis.StrictRedis(
    host=os.getenv("REDIS_HOST"),  # Redis server hostname or IP address
    port=6379,         # Redis server port
    db=0,              # Database number (default is 0)
    decode_responses=True  # Decodes responses to strings (instead of bytes)
)
try:
    redis_client.flushall()
except: pass

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

    # Register the apis
    from .apis.data import data
    from .apis.saga import saga
    app.register_blueprint(data)
    app.register_blueprint(saga)

    # Create the dbs and add initial tables values
    from .models import SkillsList, Skill, Job
    with app.app_context():
        db.create_all()
        from .tools import rabota_md_scraper
        it_skills = [
            ["jest"],
            ["syncfusion"],
            ["pytest"],
            ["unittest"],
            ["redux"],
            ["solidjs", "solid.js", "solid js"],
            ["nestjs", "nest.js", "nest js"],
            [".net"],
            ["gatsby"],
            ["html"],
            ["sql"], 
            ["javascript", "js"],
            ["nodejs", "node.js", "node", "node js"],
            ["geomapping"],
            ["gis"],
            ["openstreetmaps"],
            ["nosql"],
            ["python"], 
            ["restful", "rest", "rest api", "restapi"], 
            ["java"],
            ["c#", "csharp"], 
            ["linux"],
            ["c++"], 
            ["ruby"], 
            ["php"], 
            ["swift"], 
            ["go", "golang"], 
            ["kotlin"], 
            ["r"], 
            ["typescript"], 
            ["rust"], 
            ["perl"], 
            ["github", "git hub"],
            ["scala"], 
            ["apache hadoop"],
            ["apache cassandra"],
            ["oop"],
            ["devops", "dev ops"],
            ["design patterns"],
            ["spark"],
            ["nosql"],
            ["django"], 
            ["flask"], 
            ["express.js", "express", "expressjs", "express js"], 
            ["ruby on rails"], 
            ["spring"], 
            ["asp.net", "asp net", "aspnet"], 
            ["angular", "angularjs", "angular.js", "angular js"], 
            ["react", "react.js", "reactjs"], 
            ["vue.js", "vue", "vuejs", "vue js"], 
            ["windows"],
            ["macos", "mac os"],
            ["unix"],
            ["kvm"],
            ["tcp ip", "tcpip"],
            ["laravel"], 
            ["preact", "preact.js", "preact js"],
            ["ember", "ember.js", "ember js"],
            ["lit", "lit.js", "lit js"],
            ["alpin", "alpin.js", "alpin js"],
            ["svelte", "svelte js", "svelte.js"], 
            ["jquery"], 
            ["bootstrap"], 
            ["c"], 
            ["fastapi", "fast api"], 
            ["tailwind", "tailwind css", "tailwindcss"], 
            ["css"],
            ["react native"], 
            ["flutter"], 
            ["xamarin"], 
            ["pandas"], 
            ["numpy"], 
            ["scikitlearn", "scikit-learn", "scikit learn", "scikit"],
            ["version control"],
            ["xgboost"],
            ["tensorflow"], 
            ["keras"], 
            ["pytorch"], 
            ["matplotlib"], 
            ["seaborn"], 
            ["nltk"], 
            ["opencv"], 
            ["mysql"],
            ["postgresql", "postgres", "postgre"], 
            ["mongodb", "mongo db", "mongo"], 
            ["sqlite"], 
            ["oracle"], 
            ["microsoft sql server", "sql server"], 
            ["redis"], 
            ["cassandra"], 
            ["aws"], 
            ["azure"], 
            ["gc", "google cloud", "gcp", "google cloud platform"],
            ["tableau"],
            ["heroku"], 
            ["digitalocean"], 
            ["docker"], 
            ["nextjs", "next js", "next.js"],
            ["docker compose"],
            ["kubernetes"], 
            ["jenkins"], 
            ["git"], 
            ["gitlab", "git lab"],
            ["ansible"], 
            ["terraform"], 
            ["ci cd"], 
            ["english"],
            ["penetration testing"], 
            ["ethical hacking"], 
            ["firewall configuration"], 
            ["network security"], 
            ["malware analysis"], 
            ["tcp ip"], 
            ["dns"], 
            ["lan wan"], 
            ["vpn"], 
            ["voip"], 
            ["git"], 
            ["subversion", "svn"], 
            ["mercurial"], 
            ["agile"], 
            ["scrum"], 
            ["bash"],
            ["terraform"],
            ["ansible"],
            ["kanban"], 
            ["waterfall"], 
            ["jira"], 
            ["trello"], 
            ["asana"], 
            ["web scraping"], 
            ["ui ux design", "ui ux"], 
            ["machine learning", "ml", "ai"], 
            ["nlp"], 
            ["blockchain"], 
            ["iot"],
            ["ios"],
            ["sqlalchemy"],
            ["orm"],
            ["bs4", "beautifulsoup", "beautifulsoup4", "beautiful soup"],
            ["websocket", "web socket"],
            ["celery"],
            ["elasticsearch", "elastic search"]
        ]
        for skill in it_skills:
            exists = SkillsList.query.filter_by(name=str(skill)).first()
            if not exists:
                db.session.add(SkillsList(name=str(skill)))
                db.session.commit()

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