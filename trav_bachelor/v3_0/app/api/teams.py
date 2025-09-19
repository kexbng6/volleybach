from flask import Blueprint, request, jsonify
import os
import json
import uuid
import csv
import io
from werkzeug.utils import secure_filename
from ..core.team_manager import TeamManager

teams_bp = Blueprint('teams', __name__)
team_manager = TeamManager()

@teams_bp.route('', methods=['GET'])
def get_teams():
    """Récupérer la liste des équipes"""
    teams = team_manager.get_all_teams()
    return jsonify({"teams": teams})

@teams_bp.route('/create', methods=['POST'])
def create_team():
    """Créer une nouvelle équipe"""
    print("DEBUG: Appel de la route /api/teams/create")
    print(f"DEBUG: Contenu du formulaire: {request.form}")
    print(f"DEBUG: Fichiers reçus: {request.files}")
    
    if 'team_name' not in request.form:
        print("DEBUG: Erreur - Le nom de l'équipe est requis")
        return jsonify({"error": "Le nom de l'équipe est requis"}), 400

    team_name = request.form['team_name']
    team_logo = None
    players = []

    # Gérer le logo de l'équipe s'il est fourni
    if 'team_logo' in request.files and request.files['team_logo'].filename:
        logo_file = request.files['team_logo']
        print(f"DEBUG: Logo reçu: {logo_file.filename}")
        # Sauvegarder le logo et obtenir son chemin
        team_logo = team_manager.save_team_logo(logo_file)
        print(f"DEBUG: Chemin du logo sauvegardé: {team_logo}")

    # Gérer le fichier CSV des joueurs s'il est fourni
    if 'players_csv' in request.files and request.files['players_csv'].filename:
        csv_file = request.files['players_csv']
        print(f"DEBUG: Fichier CSV reçu: {csv_file.filename}")
        # Lire et parser le CSV
        players = team_manager.parse_players_csv(csv_file)
        print(f"DEBUG: Nombre de joueurs parsés: {len(players)}")

    # Créer l'équipe
    team_id = team_manager.create_team(team_name, team_logo, players)
    print(f"DEBUG: Équipe créée avec ID: {team_id}")

    return jsonify({
        "message": f"Équipe '{team_name}' créée avec succès",
        "team": {
            "id": team_id,
            "name": team_name,
            "logo": team_logo,
            "players": players
        }
    })

@teams_bp.route('/<team_id>', methods=['GET'])
def get_team(team_id):
    """Récupérer les détails d'une équipe"""
    team = team_manager.get_team(team_id)
    if not team:
        return jsonify({"error": "Équipe non trouvée"}), 404

    return jsonify({"team": team})

@teams_bp.route('/<team_id>/delete', methods=['DELETE'])
def delete_team(team_id):
    """Supprimer une équipe"""
    success = team_manager.delete_team(team_id)
    if not success:
        return jsonify({"error": "Équipe non trouvée ou impossible à supprimer"}), 404

    return jsonify({"message": "Équipe supprimée avec succès"})

@teams_bp.route('/<team_id>/players', methods=['GET'])
def get_team_players(team_id):
    """Récupérer les joueurs d'une équipe"""
    players = team_manager.get_team_players(team_id)
    if players is None:
        return jsonify({"error": "Équipe non trouvée"}), 404

    return jsonify({"players": players})

@teams_bp.route('/match/configure', methods=['POST'])
def configure_match_teams():
    """Configurer les équipes pour un match"""
    # Si nous avons des fichiers (nouvelles équipes), utiliser FormData
    if request.files:
        if 'match_data' not in request.form:
            return jsonify({"error": "Les données du match sont requises"}), 400

        try:
            match_data = json.loads(request.form['match_data'])
        except:
            return jsonify({"error": "Format de données invalide"}), 400

        # Traiter les données des équipes A et B
        for team_key in ['teamA', 'teamB']:
            if match_data[team_key]['createNew']:
                team_name = match_data[team_key]['name']
                team_logo = None
                players = []

                # Traiter le logo
                if f'{team_key}_logo' in request.files:
                    logo_file = request.files[f'{team_key}_logo']
                    if logo_file.filename:
                        team_logo = team_manager.save_team_logo(logo_file)

                # Traiter le CSV des joueurs
                if f'{team_key}_players' in request.files:
                    csv_file = request.files[f'{team_key}_players']
                    if csv_file.filename:
                        players = team_manager.parse_players_csv(csv_file)

                # Créer l'équipe
                team_id = team_manager.create_team(team_name, team_logo, players)
                match_data[team_key]['id'] = team_id

        # Sauvegarder la configuration du match
        team_manager.set_match_teams(match_data['teamA']['id'], match_data['teamB']['id'])

        return jsonify({
            "message": "Configuration du match enregistrée avec succès",
            "redirect": "/live-setup"
        })

    # Si nous n'avons pas de fichiers (équipes existantes), utiliser JSON
    else:
        try:
            match_data = request.json
        except:
            return jsonify({"error": "Format de données invalide"}), 400

        # Vérifier que les IDs des équipes sont fournis
        if not match_data.get('teamA', {}).get('id') or not match_data.get('teamB', {}).get('id'):
            return jsonify({"error": "Les IDs des équipes sont requis"}), 400

        # Sauvegarder la configuration du match
        team_manager.set_match_teams(match_data['teamA']['id'], match_data['teamB']['id'])

        return jsonify({
            "message": "Configuration du match enregistrée avec succès",
            "redirect": "/live-setup"
        })

@teams_bp.route('/match/current', methods=['GET'])
def get_current_match():
    """Récupérer les équipes du match actuel"""
    current_match = team_manager.get_current_match()

    # Si aucune équipe n'est configurée, renvoyer un objet vide
    if not current_match or not current_match.get('team_a') or not current_match.get('team_b'):
        return jsonify({
            "team_a": None,
            "team_b": None
        })

    return jsonify({
        "team_a": current_match.get('team_a'),
        "team_b": current_match.get('team_b')
    })
