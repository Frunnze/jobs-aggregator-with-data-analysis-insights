from flask import Blueprint, request, jsonify
import time

from ..models import SkillsList
from .. import db


saga = Blueprint("saga", __name__)


@saga.route('/add-skill-to-list', methods=['POST'])
def add_skill_to_list():
    skill_id = None
    try:
        skill = SkillsList(
            name=str([request.json.get("skill_name")])
        )
        db.session.add(skill)
        db.session.flush()
        skill_id = skill.id
        db.session.commit()

        # Assume error
        if not skill:
            raise ValueError("Some error!")

        return jsonify({"skill_id": skill_id}), 201
    except Exception as e:
        return jsonify({"skill_id": skill_id}), 500


@saga.route('/delete-skill-from-list/<int:skill_id>', methods=['DELETE'])
def delete_skill_from_list(skill_id):
    """Compensating transaction which deletes the skill from list"""

    skill = SkillsList.query.filter_by(id=skill_id).first()
    if skill:
        db.session.delete(skill)
        db.session.commit()

    return jsonify({"msg": "Transaction undone successfully!"}), 200