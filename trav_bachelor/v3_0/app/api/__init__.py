from flask import Blueprint, render_template, redirect, url_for

api_bp = Blueprint("api", __name__)

@api_bp.route("/")
def index():
    return "This is the api blueprint"

@api_bp.route("/test_redirect")
def test_redirect():
    return redirect(url_for("core.hello_html"))

# Endpoint pour la compatibilité avec le frontend existant
@api_bp.route("/vmix-inputs")
def get_vmix_inputs_compat():
    """
    Endpoint de compatibilité pour rediriger vers /vmix/inputs
    """
    return redirect(url_for("api.vmix.get_vmix_inputs"))

# Importer les blueprints après avoir défini api_bp pour éviter les imports circulaires
from .vmix import vmix_bp
from .teams import teams_bp
from .stream import stream_bp
from .replay import replay_bp

# Enregistrer les Blueprints
api_bp.register_blueprint(vmix_bp, url_prefix='/vmix')
api_bp.register_blueprint(teams_bp, url_prefix='/teams')
api_bp.register_blueprint(stream_bp, url_prefix='/stream')
api_bp.register_blueprint(replay_bp, url_prefix='/replay')
