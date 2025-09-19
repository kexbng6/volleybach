from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

bp = Blueprint('routes', __name__)

@bp.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@bp.route('/setup')
def setup():
    """Page d'accueil"""
    return render_template('setup.html')

@bp.route('/setup_live')
def setup_live():
    """Page de configuration du direct"""
    return render_template('setup_live.html')

@bp.route('/diffusion_live')
def diffusion_live():
    """Page de gestion de la diffusion en direct"""
    return render_template('diffusion_live.html')

@bp.route('/setup_team')
def setup_team():
    """Page de configuration de l'équipe"""
    return render_template('setup_team.html')
