from flask import Blueprint, request, jsonify
from sqlalchemy import func
import json
import time

from .. import db, redis_client
from ..models import Skill, Job


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
    if title:
        jobs = Job.query.filter(Job.title.ilike(f"%{title}%")).all()

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
        for job in jobs
    ]

    return jsonify({
        'total_jobs': len(jobs),
        'jobs': jobs_data
    })


@data.route('/generate-insight-skills-by-demand/<string:keywords>', methods=['GET'])
def generate_insight_skills_by_demand(keywords):
    jobs_with_keyword = Job.query.filter(Job.title.ilike(f"%{keywords}%")).all()
    
    # Get all related skills for those jobs
    skill_counts = {}
    for job in jobs_with_keyword:
        for skill in job.skills:
            if skill.name in skill_counts:
                skill_counts[skill.name] += skill.counter
            else:
                skill_counts[skill.name] = skill.counter

    # Sort the skills by demand (counter) in descending order
    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
    
    return jsonify({
        'skills_by_demand': sorted_skills,
        'total_jobs': len(jobs_with_keyword)
    })


@data.route('/all-skills-by-demand', methods=['GET'])
def all_skills_by_demand():
    try:
        if redis_client.exists("skills_data"):
            skills_data = json.loads(redis_client.get("skills_data"))
            return jsonify(skills_data), 200

        # Query skills, grouping by name and summing the counter
        skills = (
            db.session.query(
                Skill.name,
                func.sum(Skill.counter).label('total_demand')
            )
            .group_by(Skill.name)
            .order_by(func.sum(Skill.counter).desc())
            .all()
        )

        # Prepare the response data
        skills_data = [
            {
                'name': skill.name,
                'demand': skill.total_demand
            } for skill in skills
        ]
        redis_client.set("skills_data", json.dumps(skills_data), ex=10)
        return jsonify(skills_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data.route('/generate-insight-average-experience/<string:keywords>', methods=['GET'])
def generate_insight_average_experience(keywords):
    if keywords == "all":
        jobs_with_keyword = Job.query.all()
    else:
        jobs_with_keyword = Job.query.filter(Job.title.ilike(f"%{keywords}%")).all()
    
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