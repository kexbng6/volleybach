from app import create_app
from app.websocket import socketio, init_app

app = create_app()
init_app(app)

#todo en production, utiliser un serveur WSGI comme Gunicorn ou uWSGI
if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
