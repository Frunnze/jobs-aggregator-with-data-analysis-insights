from flask import Blueprint, request, jsonify
from sqlalchemy import func
import json
import time
from fuzzywuzzy import fuzz

from .. import db, redis_client
from ..models import Skill, Job, SkillsList


data = Blueprint("data", __name__)
REQUEST_TIMEOUT = 5

@data.before_request
def start_timer():
    """Start the timer before each request."""
    request.start_time = time.time()

@data.after_request
def check_timeout(response):
    """Check if the request processing exceeded the timeout."""
    elapsed_time = time.time() - request.start_time
    if elapsed_time > REQUEST_TIMEOUT:
        response.status_code = 408
        response.data = json.dumps({"error": "Request timed out"})
        response.headers['Content-Type'] = 'application/json'
    return response


@data.route('/find-jobs', methods=['GET'])
def find_jobs():
    title = request.args.get('title')
    jobs = Job.query.all()
    similar_jobs = []
    for job in jobs:
        ratio = fuzz.token_set_ratio(title, job.title)
        if ratio >= 80:
            similar_jobs.append(job)

    # Prepare the response data
    jobs_data = [
        {
            'id': job.id,
            'title': job.title,
            'salary': job.salary,
            'currency': job.currency,
            'experience': job.experience,
            'link': job.link,
            'date': job.date,
            'skills': [skill.name for skill in job.skills]
        }
        for job in similar_jobs
    ]

    return jsonify({
        'total_jobs': len(jobs),
        'jobs': jobs_data
    })


@data.route('/generate-insight-skills-by-demand/<string:keywords>', methods=['GET'])
def generate_insight_skills_by_demand(keywords):
    jobs = Job.query.all()
    similar_jobs = []
    for job in jobs:
        ratio = fuzz.token_set_ratio(keywords, job.title)
        if ratio >= 85:
            similar_jobs.append(job)
    
    # Get all related skills for those jobs
    skill_counts = {}
    for job in similar_jobs:
        for skill in job.skills:
            if skill.name in skill_counts:
                skill_counts[skill.name] += skill.counter
            else:
                skill_counts[skill.name] = skill.counter

    # Sort the skills by demand (counter) in descending order
    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
    
    return jsonify({
        'skills_by_demand': sorted_skills,
        'total_jobs': len(similar_jobs)
    })


@data.route('/all-skills-by-demand', methods=['GET'])
def all_skills_by_demand():
    try:
        if redis_client.exists("skills_data2"):
            skills_data = json.loads(redis_client.get("skills_data2"))
            return jsonify(skills_data), 200

        # Query skills, grouping by name and summing the counter
        skills = (
            db.session.query(
                Skill.name,
                func.count(Skill.name).label('total_demand')
            )
            .group_by(Skill.name)
            .order_by(func.count(Skill.name).desc())
            .all()
        )

        # Prepare the response data
        skills_data = [
            {
                'name': skill.name,
                'demand': skill.total_demand
            } for skill in skills
        ]
        redis_client.set("skills_data2", json.dumps(skills_data), ex=500)
        return jsonify(skills_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data.route('/generate-insight-average-experience/<string:keywords>', methods=['GET'])
def generate_insight_average_experience(keywords):
    print("wtfsdsdsdds")
    jobs = Job.query.all()
    jobs_with_keyword = []
    for job in jobs:
        ratio = fuzz.token_set_ratio(keywords, job.title)
        if ratio >= 85:
            jobs_with_keyword.append(job)

    if jobs_with_keyword:
        total_experience = sum(job.experience for job in jobs_with_keyword)
        average_experience = total_experience / len(jobs_with_keyword)
    else:
        average_experience = 0
    
    return jsonify({
        'average_experience': average_experience,
        'total_jobs': len(jobs_with_keyword)
    })


@data.route('/status', methods=['GET'])
def status():
    return jsonify({"msg": "Service is running"}), 200


@data.route('/skills-by-salary', methods=['GET'])
def list_skills_by_salary():
    # Query the database to get all jobs with their associated skills
    jobs = Job.query.all()
    
    # Dictionary to hold skills and their corresponding salaries
    skills_salary = {}

    # Populate the dictionary with skills and their associated job salaries
    for job in jobs:
        if job.salary is not None:
            # Normalize currency to lowercase for consistency
            currency = job.currency.lower()
            for skill in job.skills:
                if skill.name not in skills_salary:
                    skills_salary[skill.name] = {"usd": [], "mdl": [], "euro": []}
                if currency in skills_salary[skill.name]:
                    skills_salary[skill.name][currency].append(job.salary)

    # Create a response list to contain average salary for each skill
    result = []
    for skill, salaries in skills_salary.items():
        mdl_avg = sum(salaries["mdl"]) / len(salaries["mdl"]) if salaries["mdl"] else 0
        usd_avg = sum(salaries["usd"]) / len(salaries["usd"]) if salaries["usd"] else 0
        euro_avg = sum(salaries["euro"]) / len(salaries["euro"]) if salaries["euro"] else 0

        jobs_num = len(salaries["euro"]) + len(salaries["usd"]) + len(salaries["mdl"])
        if len(salaries["euro"]) >= 10 and len(salaries["usd"]) >= 10 and len(salaries["mdl"]) >= 10:
            result.append({
                "skill": skill,
                "avg": (euro_avg + usd_avg * 0.91 + mdl_avg * 0.052) / 3,
                "jobs": jobs_num
            })

    # Sort skills by general coefficient in descending order
    result.sort(key=lambda x: x['avg'], reverse=True)

    return jsonify(result)


@data.route('/average-job-salary', methods=['GET'])
def average_job_salary():
    jobs = Job.query.all()

    total_salary, salary_count = 0, 0
    for job in jobs:
        if job.salary is not None:
            if job.currency == "usd":
                total_salary += job.salary * 17.66
            elif job.currency == "euro":
                total_salary += job.salary * 19.33
            elif job.currency == "mdl":
                total_salary += job.salary
            salary_count += 1

    # Calculate average salary
    average_salary = total_salary / salary_count if salary_count > 0 else 0

    return jsonify({
        'average_salary': average_salary,
        'jobs_num': salary_count
    })


@data.route('/average-job-salary-by-experience', methods=['GET'])
def average_job_salary_by_experience():
    experience = float(request.args.get("experience"))
    jobs = Job.query.all()
    
    total_salary = 0
    salary_count = 0

    for job in jobs:
        if job.salary is not None \
            and job.experience <= experience + 0.25 \
            and job.experience >= experience - 0.25:
            if job.currency == "mdl":
                total_salary += job.salary
            elif job.currency == "euro":
                total_salary += job.salary * 19.28
            elif job.currency == "usd":
                total_salary += job.salary * 17.56
            salary_count += 1

    # Calculate average salary
    average_salary = total_salary / salary_count if salary_count > 0 else 0

    return jsonify({
        'average_salary': average_salary,
        'jobs_num': salary_count
    })


@data.route('/avg-salary/<string:keywords>', methods=['GET'])
def avg_salary_by_keywords(keywords):
    jobs = Job.query.all()
    total_salary, salary_count = 0, 0
    for job in jobs:
        ratio = fuzz.token_set_ratio(keywords, job.title)
        if ratio >= 85:
            if job.salary is not None:
                if job.currency == "usd":
                    total_salary += job.salary * 17.66
                elif job.currency == "euro":
                    total_salary += job.salary * 19.33
                elif job.currency == "mdl":
                    total_salary += job.salary
                salary_count += 1
    average_salary = total_salary / salary_count if salary_count > 0 else 0
    return jsonify({
        'average_salary': average_salary,
        'jobs_num': salary_count
    })


@data.route('/get-db-data', methods=['GET'])
def get_db_data():
    try:
        # Query all jobs and their related skills
        jobs = Job.query.all()
        skills_list = SkillsList.query.all()

        # Format jobs data into a list of dictionaries
        job_data = []
        for job in jobs:
            job_data.append({
                'id': job.id,
                'title': job.title,
                'salary': job.salary,
                'currency': job.currency,
                'experience': job.experience,
                'link': job.link,
                'date': job.date,
                'skills': [
                    {'id': skill.id, 'name': skill.name, 'counter': skill.counter}
                    for skill in job.skills
                ]
            })

        # Format skills list into a separate list of dictionaries
        skills_data = [{'id': skill.id, 'name': skill.name} for skill in skills_list]

        # Return JSON response
        return jsonify({
            'status': 'success',
            'data': {
                'jobs': job_data,
                'skills_list': skills_data
            }
        }), 200

    except Exception as e:
        # Handle errors
        return jsonify({'status': 'error', 'message': str(e)}), 500