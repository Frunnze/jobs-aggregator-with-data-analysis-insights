from flask import request, jsonify, Blueprint
import traceback
import time
import json

from .. import socketio, redis_client
from ..models import User, Subscription


broadcast = Blueprint("broadcast", __name__)
REQUEST_TIMEOUT = 10

@broadcast.before_request
def start_timer():
    """Start the timer before each request."""
    request.start_time = time.time()

@broadcast.after_request
def check_timeout(response):
    """Check if the request processing exceeded the timeout."""
    elapsed_time = time.time() - request.start_time
    if elapsed_time > REQUEST_TIMEOUT:
        response.status_code = 408
        response.data = json.dumps({"error": "Request timed out"})
        response.headers['Content-Type'] = 'application/json'
    return response


@broadcast.route('/broadcast-jobs-to-users', methods=['POST'])
def broadcast_jobs_to_users():
    try:
        data = request.json
        rooms = data.get('skills', {})

        if not rooms:
            return jsonify({"msg": "Rooms and message are required"}), 400

        # Emit the message to each room
        # for room in rooms:
        #     socketio.emit('new_job', data, to=room)

        notified_users = set()
        for room in rooms:
            users_in_room = User.query\
                .join(Subscription)\
                .filter(Subscription.room_name == room)\
                .all()
            for user in users_in_room:
                if user.id not in notified_users:
                    user_sid = redis_client.get("sid:user:"+str(user.id))
                    socketio.emit('new_job', data, to=user_sid)
                    notified_users.add(user.id)

        return jsonify({"msg": f"Message broadcasted to rooms: {rooms}"}), 200
    except Exception as e:
        print(str(e))
        traceback.print_exc()
        return jsonify({"err": str(e)}), 500