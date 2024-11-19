from flask import Blueprint, request, jsonify

from ..models import Subscription
from .. import db


saga = Blueprint("saga", __name__)


@saga.route('/add-new-subscription-skill', methods=['POST'])
def add_new_subscription_skill():
    subscription_id = None
    try:
        subscription = Subscription(
            user_id=request.json.get("user_id"),
            room_name=request.json.get("skill_name")
        )
        db.session.add(subscription)
        db.session.flush()
        subscription_id = subscription.id
        db.session.commit()

        return jsonify({"subscription_id": subscription_id}), 201
    except:
        return jsonify({"subscription_id": subscription_id}), 500


@saga.route('/delete-new-subscription-skill/<int:subscription_id>', methods=['DELETE'])
def delete_new_subscription_skill(subscription_id):
    """Compensating transaction which deletes the subscription"""

    subscription = Subscription.query.filter_by(id=subscription_id).first()
    db.session.delete(subscription)
    db.session.commit()

    return jsonify({"msg": "Transaction undone successfully!"}), 200