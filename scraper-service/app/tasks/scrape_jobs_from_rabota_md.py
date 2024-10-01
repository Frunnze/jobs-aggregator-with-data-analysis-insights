import requests
from dotenv import load_dotenv
import os

from .. import db, scheduler
from ..models import Skill, Job
from ..tools.rabota_md_scraper import RabotaMdScraper


load_dotenv()
USER_SERVICE = os.getenv("USER_SERVICE")
scraper = RabotaMdScraper()


@scheduler.task('interval', id='scrape_jobs_from_rabota_md', seconds=60)
def scrape_jobs_from_rabota_md():
    print("RabotaMdScraper started scraping!")
    with scheduler.app.app_context():
        # Extract data
        data_list, page = [], 2
        url = "https://www.rabota.md/ro/vacancies/category/it/"
        while page <= 2:
            jobs_pages_links = scraper.extract_page_links(url + str(page))
            for link in jobs_pages_links:
                # Check if it already exists
                job = Job.query.filter_by(link=link).first()
                if job: continue
                data = scraper.scrape_page_data(link)
                data_list.append(data)
                print("\n"*5)
                print(data)
            page += 1

        # Save data
        for data_dict in data_list:
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
                    response = requests.post(
                        url=USER_SERVICE + "/broadcast-jobs-to-users", 
                        json=data_dict
                    )
                    print(response.status_code)
                except Exception as e:
                    print(str(e))
            except Exception as e:
                print(str(e))
                db.session.rollback()
        print("RabotaMdScraper finished scraping!")