import os

from flask import Flask, Blueprint, render_template, redirect
from flask_socketio import SocketIO
from .api import api_bp  # Importer le Blueprint api

# Chemin vers le dossier statique
static_folder = os.path.join(os.path.dirname(__file__), 'static')

# Création du blueprint principal avec le dossier statique configuré
core_bp = Blueprint("core", __name__, 
                   template_folder="templates",
                   static_folder=static_folder,
                   static_url_path='/static')

socketio = SocketIO()

@core_bp.route("/")
def index():
    return render_template("core/index.html")

@core_bp.route("/team-setup")
def team_setup():
    return render_template("core/team_setup.html")

@core_bp.route("/live-setup")
def live_setup():
    return render_template("core/live_setup.html")

@core_bp.route("/live-broadcast")
def live_broadcast():
    return render_template("core/live_broadcast.html")

@core_bp.route("/settings")
def settings():
    return render_template("core/settings.html")

# Routes de test à supprimer ultérieurement
@core_bp.route("/hello")
def hello():
    return "Hello again"

@core_bp.route("/hellohtml")
def hello_html():
    return render_template("core/hello.html")

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True) #app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )
    #socketio code

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    #blueprint for every routes
    app.register_blueprint(core_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
