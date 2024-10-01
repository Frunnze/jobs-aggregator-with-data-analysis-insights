from flask import request
from flask_socketio import join_room, send, emit

from .models import Subscription, User
from . import socketio, db, redis_client


@socketio.on('connect')
def handle_connect():
    # Assuming you use session or token authentication to identify the user
    user_id = request.args.get('user_id')
    print(type(user_id))
    if not user_id: return

    # Save session to redis
    redis_client.set("sid:user:"+user_id, request.sid)

    # Query the database to get the rooms the user is associated with
    user_rooms = Subscription.query.filter_by(user_id=user_id).all()

    # Register the user in their rooms
    for user_room in user_rooms:
        join_room(user_room.room_name)

    # Send a confirmation back to the user
    send('User connected and joined rooms')


@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.args.get('user_id')
    redis_client.delete("sid:user:"+user_id)
    # Optionally, you can handle leaving rooms or cleaning up on disconnect
    send(f'User {user_id} disconnected.')


@socketio.on('message')
def handle_message(data):
    print(data)
    message = data.get('message')
    
    if message:
        # Broadcast the message to all connected clients
        emit('echo_message', {'msg': message}, broadcast=True)
    else:
        return {"msg": "Message is required"}, 400
    

@socketio.on('subscribe')
def handle_subscribe(data):
    tag = data.get('tag')
    user_id = request.args.get('user_id')

    # Fetch the user from the database
    user = User.query.get(user_id)
    if not user:
        emit('error', {'msg': "User not found"})
        return

    # Check if the user is already subscribed to the tag
    existing_subscription = Subscription.query.filter_by(
        user_id=user_id, 
        room_name=tag
    ).first()
    if existing_subscription:
        emit('error', {'msg': "Already subscribed to this tag"})
        return

    # Add the subscription for the user
    new_subscription = Subscription(room_name=tag, user=user)
    db.session.add(new_subscription)
    db.session.commit()

    # Join the room for WebSocket
    join_room(tag)
    emit('subscribed', {'msg': "Subscribed successfully", 'tag': tag})