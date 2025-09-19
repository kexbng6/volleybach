import os
import json
from flask import Blueprint, jsonify, request
import logging
from .vmix_manager import VmixManager
from .vmix_team_overlay import VmixTeamOverlayManager

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('vmix_team_updater')

bp_vmix_team = Blueprint('vmix_team', __name__, url_prefix='/api/vmix/team')

# Initialiser le gestionnaire vMix
vmix_manager = VmixManager()
team_overlay_manager = VmixTeamOverlayManager(vmix_manager)

@bp_vmix_team.route('/status', methods=['GET'])
def check_status():
    """Vérifie la connexion à vMix et détecte les inputs d'overlay disponibles"""
    connected = vmix_manager.check_connection()
    if connected:
        # Mettre à jour la détection des inputs d'overlay
        team_overlay_manager.detect_overlay_inputs()
        return jsonify({
            'connected': True,
            'overlay_inputs': team_overlay_manager.overlay_inputs
        })
    else:
        return jsonify({'connected': False}), 503

@bp_vmix_team.route('/teams', methods=['GET'])
def get_teams():
    """Récupère la liste des équipes disponibles"""
    teams_data = team_overlay_manager.load_teams_data()
    return jsonify(teams_data)

@bp_vmix_team.route('/update-team-overlay', methods=['POST'])
def update_team_overlay():
    """Met à jour les overlays d'une équipe"""
    try:
        data = request.json
        team_id = data.get('team_id')
        overlay_type = data.get('overlay_type')  # Optionnel

        if not team_id:
            return jsonify({'success': False, 'message': 'ID d\'équipe requis'}), 400

        success = team_overlay_manager.update_team_overlay(team_id, overlay_type)
        if success:
            return jsonify({'success': True, 'message': 'Overlays d\'équipe mis à jour avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Échec de la mise à jour des overlays d\'équipe'}), 500

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des overlays d'équipe: {str(e)}")
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@bp_vmix_team.route('/update-player-overlay', methods=['POST'])
def update_player_overlay():
    """Met à jour les overlays d'un joueur"""
    try:
        data = request.json
        team_id = data.get('team_id')
        player_index = data.get('player_index')
        overlay_type = data.get('overlay_type')  # Optionnel

        if not team_id or player_index is None:
            return jsonify({'success': False, 'message': 'ID d\'équipe et index du joueur requis'}), 400

        success = team_overlay_manager.update_player_overlay(team_id, int(player_index), overlay_type)
        if success:
            return jsonify({'success': True, 'message': 'Overlays du joueur mis à jour avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Échec de la mise à jour des overlays du joueur'}), 500

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des overlays du joueur: {str(e)}")
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500
