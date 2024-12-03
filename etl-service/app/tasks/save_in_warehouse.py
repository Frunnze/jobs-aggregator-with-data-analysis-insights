import requests
from dotenv import load_dotenv
import os

from .. import db, scheduler
from ..models import Job, Skill, SkillsList, User, Subscription

load_dotenv()
USER_SERVICE_HOST = os.getenv("USER_SERVICE_HOST")
SCRAPER_SERVICE_HOST = os.getenv("SCRAPER_SERVICE_HOST")


@scheduler.task('interval', id='save_in_warehouse', seconds=5, max_instances=1)
def save_in_warehouse():
    with scheduler.app.app_context():
        print("SAVING DATA IN WAREHOUSE STARTED!")
        try:
            # Fetch data from the User API
            user_response = requests.get(USER_SERVICE_HOST + "/get-db-data")
            if user_response.status_code != 200:
                raise Exception(f"Failed to fetch users: {user_response.json().get('message')}")

            user_data = user_response.json().get('data', [])

            # Insert User and Subscription data
            for user in user_data:
                user_obj = User.query.get(user['id'])
                if user_obj:
                    # Check if the data has changed
                    if (
                        user_obj.username != user['username'] or
                        user_obj.email != user['email'] or
                        user_obj.password != user['password']
                    ):
                        db.session.delete(user_obj)  # Delete the existing record
                        db.session.commit()  # Commit the deletion
                        user_obj = None  # Mark for re-creation

                if not user_obj:
                    user_obj = User(
                        id=user['id'],
                        username=user['username'],
                        email=user['email'],
                        password=user['password']
                    )
                    db.session.add(user_obj)

                # Handle subscriptions
                for sub in user['subscriptions']:
                    subscription_obj = Subscription.query.get(sub['id'])
                    if subscription_obj:
                        # Check if the data has changed
                        if subscription_obj.room_name != sub['room_name'] or subscription_obj.user_id != user['id']:
                            db.session.delete(subscription_obj)  # Delete the existing record
                            db.session.commit()  # Commit the deletion
                            subscription_obj = None  # Mark for re-creation

                    if not subscription_obj:
                        subscription_obj = Subscription(
                            id=sub['id'],
                            room_name=sub['room_name'],
                            user_id=user['id']
                        )
                        db.session.add(subscription_obj)

            # Fetch data from the Job API
            job_response = requests.get(SCRAPER_SERVICE_HOST + "/get-db-data")
            if job_response.status_code != 200:
                raise Exception(f"Failed to fetch jobs: {job_response.json().get('message')}")

            job_data = job_response.json().get('data', {})
            jobs = job_data.get('jobs', [])
            skills_list = job_data.get('skills_list', [])
            # Insert Job and Skill data
            for job in jobs:
                job_obj = Job.query.get(job['id'])
                if job_obj:
                    # Check if the data has changed
                    if (
                        job_obj.title != job['title'] or
                        job_obj.salary != job['salary'] or
                        job_obj.currency != job['currency'] or
                        job_obj.experience != job['experience'] or
                        job_obj.link != job['link'] or
                        job_obj.date != job['date']
                    ):
                        db.session.delete(job_obj)  # Delete the existing record
                        db.session.commit()  # Commit the deletion
                        job_obj = None  # Mark for re-creation

                if not job_obj:
                    job_obj = Job(
                        id=job['id'],
                        title=job['title'],
                        salary=job['salary'],
                        currency=job['currency'],
                        experience=job['experience'],
                        link=job['link'],
                        date=job['date']
                    )
                    db.session.add(job_obj)

                # Handle skills for the job
                for skill in job['skills']:
                    skill_obj = Skill.query.get(skill['id'])
                    if skill_obj:
                        # Check if the data has changed
                        if (
                            skill_obj.name != skill['name'] or
                            skill_obj.job_id != job['id'] or
                            skill_obj.counter != skill['counter']
                        ):
                            db.session.delete(skill_obj)  # Delete the existing record
                            db.session.commit()  # Commit the deletion
                            skill_obj = None  # Mark for re-creation

                    if not skill_obj:
                        skill_obj = Skill(
                            id=skill['id'],
                            name=skill['name'],
                            job_id=job['id'],
                            counter=skill['counter']
                        )
                        db.session.add(skill_obj)

            # # Insert SkillsList data
            for skill in skills_list:
                skill_list_obj = SkillsList.query.filter_by(
                    name=str(skill['name'])
                ).first()
                if not skill_list_obj:
                    skill_list_obj = SkillsList(
                        id=skill['id'],
                        name=str(skill['name'])
                    )
                    db.session.add(skill_list_obj)

            # Commit all changes
            db.session.commit()
            print("Data synchronization completed successfully.")

        except Exception as e:
            db.session.rollback()
            print(f"An error occurred during synchronization: {str(e)}")