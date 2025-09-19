from flask import Flask
import sys
import os

# Ajouter le répertoire parent au chemin de recherche de Python
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))
sys.path.append(current_dir)

# Importation directe des modules app
from app import core_bp, create_app
from app.api import api_bp

# Création de l'application Flask avec la fonction create_app ou manuellement
if hasattr(core_bp, 'create_app'):
    app = create_app()
else:
    app = Flask(__name__, 
                static_folder=os.path.join(current_dir, 'app', 'static'),
                static_url_path='/static')
    app.register_blueprint(core_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

# Configuration de Socket.IO
try:
    from flask_socketio import SocketIO
    socketio = SocketIO(app)
    use_socketio = True
except ImportError:
    use_socketio = False
    print("Flask-SocketIO non disponible, fonctionnalités temps réel désactivées")

if __name__ == '__main__':
    if use_socketio:
        socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
    else:
        app.run(debug=True)
