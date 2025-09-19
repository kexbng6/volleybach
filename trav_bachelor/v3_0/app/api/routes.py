#fonctionnalités à implémenter :
# -quelles routes sont essentielles
# -comment organiser logiquement les routes par func
# -comment structurer les réponses JSON pour qu'elles soient cohérentes ?

fev crom flask import Blueprint, render_template

bp = Blueprint('routes', __name__)

@bp.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')