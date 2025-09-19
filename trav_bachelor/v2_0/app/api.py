from flask import Blueprint, jsonify, request, current_app
import json
from . import setup_team
from .vmix_manager import VmixManager

bp_api = Blueprint('api', __name__, url_prefix='/api')

vmix_manager = VmixManager()

@bp_api.route('/vmix-status')
def get_vmix_status():
    """Retourne l'état de la connexion à vMix"""
    connected = vmix_manager.check_connection()
    return jsonify({
        "success": True,
        "vmix_connected": connected
    })

@bp_api.route('/vmix-connect', methods=['POST'])
def connect_vmix():
    """Simule la connexion à vMix"""
    data = request.json
    if data and 'host' in data and 'port' in data:
        vmix_manager.host = data['host']
        vmix_manager.port = data['port']
        vmix_manager.base_url = f'http://{data["host"]}:{data["port"]}/api/'

    connected = vmix_manager.check_connection()
    # Si connecté, envoi d'un événement SocketIO
    if connected and hasattr(current_app, 'socketio'):
        current_app.socketio.emit('vmix_status_update', {'connected': connected})

    return jsonify({
        "success": True,
        "message": "Connexion à vMix réussie" if connected else "Échec de la connexion à vMix",
        "vmix_connected": connected
    })

@bp_api.route('/vmix-disconnect', methods=['POST'])
def disconnect_vmix():
    """Simule la déconnexion de vMix"""
    # Ici, vous devriez implémenter la logique de déconnexion réelle de vMix

    if hasattr(current_app, 'socketio'):
        current_app.socketio.emit('vmix_status_update', {'connected': False})

    return jsonify({
        "success": True,
        "message": "Déconnexion de vMix réussie",
        "vmix_connected": False
    })

# Nouvel endpoint pour remplacer /api/vmix/inputs par /api/vmix-inputs
@bp_api.route('/vmix-inputs')
def get_vmix_inputs_compat():
    """
    Endpoint pour récupérer les entrées vMix avec un format d'URL cohérent avec le frontend
    """
    try:
        inputs = vmix_manager.get_inputs()

        # Catégoriser les entrées
        categorized_inputs = {
            'camera': [],
            'video': [],
            'audio': [],
            'other': []
        }

        for input_data in inputs:
            category = input_data.get('category', 'other')
            if category in categorized_inputs:
                categorized_inputs[category].append(input_data)
            else:
                categorized_inputs['other'].append(input_data)

        return jsonify({
            "success": True,
            "inputs": inputs,
            "categorized": categorized_inputs
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des entrées vMix: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@bp_api.route('/vmix-inputs/<input_id>', methods=['POST'])
def select_vmix_input(input_id):
    """Sélectionne une entrée vMix"""
    # Ici, vous devriez implémenter la logique pour sélectionner l'entrée dans vMix
    return jsonify({
        "success": True,
        "message": f"Entrée {input_id} sélectionnée"
    })

@bp_api.route('/vmix-inputs/<input_id>/activate', methods=['POST'])
def activate_vmix_input(input_id):
    """Active une entrée vMix"""
    # Ici, vous devriez implémenter la logique pour activer l'entrée dans vMix
    return jsonify({
        "success": True,
        "message": f"Entrée {input_id} activée"
    })

@bp_api.route('/vmix-inputs/<input_id>/deactivate', methods=['POST'])
def deactivate_vmix_input(input_id):
    """Désactive une entrée vMix"""
    # Ici, vous devriez implémenter la logique pour désactiver l'entrée dans vMix
    return jsonify({
        "success": True,
        "message": f"Entrée {input_id} désactivée"
    })

@bp_api.route('/match/setup-teams', methods=['POST'])
def setup_match_teams():
    """Configure les équipes pour un match"""
    try:
        # Récupérer les données JSON
        match_data = json.loads(request.form.get('match_data'))

        # Traiter l'équipe A
        if match_data.get('newTeamA'):
            team_a_data = {
                'team_name': match_data['newTeamA']['name'],
                'team_logo': request.files.get('teamA_logo'),
                'players_csv': request.files.get('teamA_players')
            }
            # Créer l'équipe A
            team_a_response = setup_team.create_team(team_a_data)
            if 'error' in team_a_response:
                return jsonify({'error': f"Erreur lors de la création de l'équipe A: {team_a_response['error']}"}), 400
            match_data['teamA'] = team_a_response['team']['id']

        # Traiter l'équipe B
        if match_data.get('newTeamB'):
            team_b_data = {
                'team_name': match_data['newTeamB']['name'],
                'team_logo': request.files.get('teamB_logo'),
                'players_csv': request.files.get('teamB_players')
            }
            # Créer l'équipe B
            team_b_response = setup_team.create_team(team_b_data)
            if 'error' in team_b_response:
                return jsonify({'error': f"Erreur lors de la création de l'équipe B: {team_b_response['error']}"}), 400
            match_data['teamB'] = team_b_response['team']['id']

        # À ce stade, nous avons les IDs des deux équipes
        return jsonify({
            'success': True,
            'message': 'Configuration des équipes réussie',
            'match_data': match_data,
            'redirect': '/setup_live'  # Redirection vers la page de configuration du direct
        })

    except Exception as e:
        return jsonify({'error': f'Erreur lors de la configuration des équipes: {str(e)}'}), 400
