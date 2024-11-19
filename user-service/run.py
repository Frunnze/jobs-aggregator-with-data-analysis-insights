from app import create_app, socketio
import os


app = create_app()

if __name__ == '__main__':
    # server_port = os.environ.get('PORT', '8080')
    # app.run(port=server_port, host='0.0.0.0', debug=True)
    socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True )