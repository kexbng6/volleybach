from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )
    socketio.init_app(app)
    app.socketio = socketio  # Pour accéder à socketio depuis les blueprints

    # Enregistrement des blueprints
    from . import routes
    app.register_blueprint(routes.bp)

    # Enregistrement du blueprint de l'API pour Vue.js
    from . import api
    app.register_blueprint(api.bp_api)

    # Enregistrement du blueprint de l'API pour la configuration
    from . import setup_api
    app.register_blueprint(setup_api.bp_setup_api)

    from . import setup_team
    app.register_blueprint(setup_team.bp_setup_team)

    # Enregistrement du blueprint pour les overlays d'équipe dans vMix
    from . import vmix_team_updater
    app.register_blueprint(vmix_team_updater.bp_vmix_team)

    # Enregistrement du blueprint pour la diffusion live
    from . import broadcast_api
    app.register_blueprint(broadcast_api.bp_broadcast_api)

    return app
