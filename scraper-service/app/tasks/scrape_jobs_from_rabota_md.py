import requests
from dotenv import load_dotenv
import os

from .. import db, scheduler
from ..models import Skill, Job
from ..tools.rabota_md_scraper import RabotaMdScraper


load_dotenv()
SERVICE_DISCOVERY = os.getenv("SERVICE_DISCOVERY")
scraper = RabotaMdScraper()


def get_service_details(service_name):
    url = f'{SERVICE_DISCOVERY}/get-service?name={service_name}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print("Service not found." if response.status_code == 404 else f"Error: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


@scheduler.task('interval', id='scrape_jobs_from_rabota_md', seconds=20000, max_instances=3)
def scrape_jobs_from_rabota_md():
    print("RabotaMdScraper started scraping!")
    with scheduler.app.app_context():
        # Extract data
        page, max_page = 2, 100
        url = "https://www.rabota.md/ro/vacancies/category/it/"
        while page <= max_page:
            data_list = []
            jobs_pages_links = scraper.extract_page_links(url + str(page))
            print("jobs_pages_links", jobs_pages_links)
            for link in jobs_pages_links:
                # Check if it already exists
                job = Job.query.filter_by(link=link).first()
                if job: continue
                data = scraper.scrape_page_data(link)
                print("data", data)
                data_list.append(data)
                print("\n"*5)
                print(data)
            page += 1

            # Save data
            for data_dict in data_list:
                print("data_dict", data_dict)
                try:
                    # Create a new job record
                    new_job = Job(
                        title=data_dict.get("title"), 
                        salary=data_dict.get("salary"), 
                        currency=data_dict.get("currency"),
                        experience=data_dict.get("experience"), 
                        link=data_dict.get("link"), 
                        date=data_dict.get("date")
                    )
                    db.session.add(new_job)
                    db.session.commit()

                    # Add skills
                    skills = data_dict.get("skills")
                    if skills:
                        for skill, counter in skills.items():
                            new_skill_record = Skill(
                                job_id=new_job.id,
                                name=skill,
                                counter=counter
                            )
                            db.session.add(new_skill_record)

                    # Add the job to the session
                    db.session.commit()

                    # Send the job to the user
                    try:
                        user_services = get_service_details("user-service")
                        print("user_services", user_services, "-----------------")
                        for user_service in user_services:
                            url_user = f"{user_service["serviceAddress"]}:{user_service["servicePort"]}/broadcast-jobs-to-users"
                            print(url_user)
                            response = requests.post(url=url_user, json=data_dict)
                            print(response.status_code)
                    except Exception as e:
                        print(str(e))
                except Exception as e:
                    print(str(e))
                    db.session.rollback()
        print("RabotaMdScraper finished scraping!")