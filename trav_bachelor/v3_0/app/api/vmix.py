from flask import Blueprint, request, jsonify
import os
import json
from ..core.vmix_manager import VMixManager
from ..core.team_manager import TeamManager

vmix_bp = Blueprint('vmix', __name__)
vmix_manager = VMixManager()
team_manager = TeamManager()

@vmix_bp.route('/status', methods=['GET'])
def get_vmix_status():
    """Vérifier le statut de connexion à vMix"""
    status = vmix_manager.check_connection()
    host = '127.0.0.1'  # Par défaut
    port = 8088  # Par défaut

    # Si la connexion est établie, récupérer les infos de connexion
    if status:
        host = vmix_manager.host
        port = vmix_manager.port

    return jsonify({
        "connected": status,
        "host": host,
        "port": port
    })

@vmix_bp.route('/send-roster', methods=['POST'])
def send_roster_to_vmix():
    """Envoyer un roster d'équipe vers vMix depuis un fichier CSV"""
    if 'team_name' not in request.form:
        return jsonify({"error": "Le nom de l'équipe est requis"}), 400

    if 'players_csv' not in request.files or not request.files['players_csv'].filename:
        return jsonify({"error": "Un fichier CSV des joueurs est requis"}), 400

    team_name = request.form['team_name']
    csv_file = request.files['players_csv']

    # Parser le CSV pour obtenir la liste des joueurs
    players = team_manager.parse_players_csv(csv_file)

    # Envoyer les données à vMix
    success = vmix_manager.send_roster_to_vmix(team_name, players)

    if success:
        return jsonify({"message": f"Roster de l'équipe '{team_name}' envoyé avec succès à vMix"})
    else:
        return jsonify({"error": "Erreur lors de l'envoi du roster à vMix"}), 500

@vmix_bp.route('/send-roster/<team_id>', methods=['POST'])
def send_team_roster_to_vmix(team_id):
    """Envoyer le roster d'une équipe existante vers vMix"""
    # Récupérer les détails de l'équipe
    team = team_manager.get_team(team_id)
    if not team:
        return jsonify({"error": "Équipe non trouvée"}), 404

    # Récupérer les joueurs de l'équipe
    players = team_manager.get_team_players(team_id)
    if not players:
        return jsonify({"error": "Aucun joueur trouvé pour cette équipe"}), 404

    # Envoyer les données à vMix
    success = vmix_manager.send_roster_to_vmix(team['name'], players)

    if success:
        return jsonify({"message": f"Roster de l'équipe '{team['name']}' envoyé avec succès à vMix"})
    else:
        return jsonify({"error": "Erreur lors de l'envoi du roster à vMix"}), 500

@vmix_bp.route('/show-player', methods=['POST'])
def show_player_in_vmix():
    """Afficher les détails d'un joueur dans vMix"""
    data = request.json
    if not data or 'player' not in data:
        return jsonify({"error": "Les données du joueur sont requises"}), 400

    player = data['player']
    team_id = data.get('teamId')

    # Si l'ID de l'équipe est fourni, récupérer les détails de l'équipe
    team_name = None
    if team_id:
        team = team_manager.get_team(team_id)
        if team:
            team_name = team['name']

    # Envoyer les détails du joueur à vMix
    success = vmix_manager.show_player_details(player, team_name)

    if success:
        player_name = f"{player.get('prenom', '')} {player.get('nom', '').upper()}"
        return jsonify({"message": f"Détails du joueur '{player_name}' affichés dans vMix"})
    else:
        return jsonify({"error": "Erreur lors de l'affichage des détails du joueur dans vMix"}), 500

@vmix_bp.route('/inputs', methods=['GET'])
def get_vmix_inputs():
    """Récupérer la liste des inputs disponibles dans vMix avec option de rafraîchissement forcé"""
    # Vérifier si on demande un rafraîchissement
    should_refresh = request.args.get('refresh', 'false').lower() == 'true'

    try:
        if should_refresh:
            # Forcer une nouvelle connexion à vMix pour obtenir des données fraîches
            vmix_manager.check_connection()

        inputs = vmix_manager.get_inputs()

        # Catégoriser les inputs
        categorized_inputs = {
            'video': [],
            'audio': [],
            'title': [],
            'other': []
        }

        for input_data in inputs:
            input_type = input_data.get('type', '').lower()
            name = input_data.get('title', '').lower()

            # Déterminer la catégorie de l'input
            if any(keyword in input_type for keyword in ['capture', 'camera', 'video']):
                category = 'video'
            elif any(keyword in input_type for keyword in ['audio', 'sound']) or \
                 any(keyword in name for keyword in ['mic', 'audio', 'sound', 'comment', 'ambiance']):
                category = 'audio'
            elif any(keyword in input_type for keyword in ['title', 'gt']):
                category = 'title'
            else:
                category = 'other'

            # Ajouter l'input à sa catégorie avec toutes les informations nécessaires
            categorized_inputs[category].append({
                'id': input_data.get('number'),
                'name': input_data.get('title'),
                'type': input_data.get('type'),
                'state': input_data.get('state')
            })

        return jsonify(categorized_inputs)

    except Exception as e:
        return jsonify({
            "error": f"Erreur lors de la récupération des inputs vMix: {str(e)}",
            "status": "error"
        }), 500

@vmix_bp.route('/start-streaming', methods=['POST'])
def start_streaming():
    """Démarrer le streaming dans vMix"""
    try:
        # Récupérer le canal de streaming spécifié dans la requête (par défaut: 0)
        data = request.json or {}
        channel = data.get('channel', 0)

        success = vmix_manager.start_streaming(channel)
        if success:
            return jsonify({"message": f"Streaming démarré avec succès sur le canal {channel if channel else 'par défaut'}"})
        else:
            return jsonify({"error": "Erreur lors du démarrage du streaming"}), 500
    except Exception as e:
        return jsonify({"error": f"Erreur lors du démarrage du streaming: {str(e)}"}), 500

@vmix_bp.route('/stop-streaming', methods=['POST'])
def stop_streaming():
    """Arrêter le streaming dans vMix"""
    try:
        # Récupérer le canal de streaming spécifié dans la requête (par défaut: 0)
        data = request.json or {}
        channel = data.get('channel', 0)

        success = vmix_manager.stop_streaming(channel)
        if success:
            return jsonify({"message": f"Streaming arrêté avec succès sur le canal {channel if channel else 'par défaut'}"})
        else:
            return jsonify({"error": "Erreur lors de l'arrêt du streaming"}), 500
    except Exception as e:
        return jsonify({"error": f"Erreur lors de l'arrêt du streaming: {str(e)}"}), 500

@vmix_bp.route('/start-recording', methods=['POST'])
def start_recording():
    """Démarrer l'enregistrement dans vMix"""
    try:
        success = vmix_manager.start_recording()
        if success:
            return jsonify({"message": "Enregistrement démarré avec succès"})
        else:
            return jsonify({"error": "Erreur lors du démarrage de l'enregistrement"}), 500
    except Exception as e:
        return jsonify({"error": f"Erreur lors du démarrage de l'enregistrement: {str(e)}"}), 500

@vmix_bp.route('/stop-recording', methods=['POST'])
def stop_recording():
    """Arrêter l'enregistrement dans vMix"""
    try:
        success = vmix_manager.stop_recording()
        if success:
            return jsonify({"message": "Enregistrement arrêté avec succès"})
        else:
            return jsonify({"error": "Erreur lors de l'arrêt de l'enregistrement"}), 500
    except Exception as e:
        return jsonify({"error": f"Erreur lors de l'arrêt de l'enregistrement: {str(e)}"}), 500

@vmix_bp.route('/streaming-status', methods=['GET'])
def get_streaming_status():
    """Récupérer le statut du streaming et de l'enregistrement"""
    try:
        streaming_status = vmix_manager.get_streaming_status()
        recording_status = vmix_manager.get_recording_status()

        return jsonify({
            "isStreaming": streaming_status,
            "isRecording": recording_status,
            "streamingStartTime": None,  # À implémenter si nécessaire
            "recordingStartTime": None   # À implémenter si nécessaire
        })
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération du statut: {str(e)}"}), 500

@vmix_bp.route('/load-teams', methods=['POST'])
def load_teams_to_vmix():
    """Charger les équipes du match actuel dans vMix"""
    try:
        # Récupérer les IDs des équipes depuis la requête
        data = request.json
        team_a_id = data.get('teamA')
        team_b_id = data.get('teamB')

        # Si les IDs ne sont pas fournis, utiliser les équipes du match actuel
        if not team_a_id or not team_b_id:
            current_match = team_manager.get_current_match()
            if not current_match or not current_match.get('team_a') or not current_match.get('team_b'):
                return jsonify({"error": "Aucune équipe configurée pour le match"}), 400

            team_a_id = current_match['team_a']['id']
            team_b_id = current_match['team_b']['id']

        # Récupérer les détails des équipes
        team_a = team_manager.get_team(team_a_id)
        team_b = team_manager.get_team(team_b_id)

        if not team_a or not team_b:
            return jsonify({"error": "Une ou plusieurs équipes non trouvées"}), 404

        # Envoyer les informations des équipes vers vMix

        # 1. Envoyer les noms des équipes pour le score
        score_success = vmix_manager.update_title_multiple("ScoreOverlay", {
            "TeamA": team_a['name'],
            "TeamB": team_b['name'],
            "ScoreA": "0",
            "ScoreB": "0",
            "Sets": "0-0"
        })

        # 2. Envoyer les logos des équipes si disponibles
        logo_success = True
        if team_a.get('logo'):
            logo_success = logo_success and vmix_manager.set_image("ScoreOverlay", "LogoA", team_a['logo'])
        if team_b.get('logo'):
            logo_success = logo_success and vmix_manager.set_image("ScoreOverlay", "LogoB", team_b['logo'])

        # 3. Envoyer les rosters des équipes
        roster_a_success = True
        roster_b_success = True

        players_a = team_manager.get_team_players(team_a_id)
        if players_a:
            roster_a_success = vmix_manager.send_roster_to_vmix(team_a['name'], players_a)

        players_b = team_manager.get_team_players(team_b_id)
        if players_b:
            roster_b_success = vmix_manager.send_roster_to_vmix(team_b['name'], players_b)

        # Vérifier si toutes les opérations ont réussi
        if score_success and logo_success and roster_a_success and roster_b_success:
            return jsonify({"message": "Équipes chargées avec succès dans vMix"})
        else:
            # Identifier quelles opérations ont échoué
            errors = []
            if not score_success:
                errors.append("Erreur lors de la mise à jour du score")
            if not logo_success:
                errors.append("Erreur lors du chargement des logos")
            if not roster_a_success:
                errors.append(f"Erreur lors du chargement du roster de l'équipe {team_a['name']}")
            if not roster_b_success:
                errors.append(f"Erreur lors du chargement du roster de l'équipe {team_b['name']}")

            return jsonify({
                "message": "Équipes partiellement chargées dans vMix",
                "errors": errors
            }), 500

    except Exception as e:
        return jsonify({"error": f"Erreur lors du chargement des équipes dans vMix: {str(e)}"}), 500

@vmix_bp.route('/toggle-audio', methods=['POST'])
def toggle_audio():
    """Activer ou désactiver l'audio d'une entrée vMix"""
    data = request.get_json()

    if not data or 'inputId' not in data:
        return jsonify({"status": "error", "message": "L'ID de l'entrée est requis"}), 400

    input_id = data['inputId']

    # Si mute est spécifié explicitement, utiliser AudioOn ou AudioOff
    if 'mute' in data:
        mute = data['mute']
        if mute:
            result = vmix_manager.toggle_audio(input_id, mute=True)
        else:
            result = vmix_manager.toggle_audio(input_id, mute=False)
    else:
        # Sinon utiliser AudioToggle
        result = vmix_manager.toggle_audio(input_id)

    if result:
        return jsonify({"status": "success", "message": "État audio modifié avec succès"})
    else:
        return jsonify({"status": "error", "message": "Erreur lors de la modification de l'état audio"}), 500

@vmix_bp.route('/audio/volume', methods=['POST'])
def set_audio_volume():
    """Définir le volume d'une entrée audio vMix"""
    data = request.get_json()

    if not data or 'inputId' not in data or 'volume' not in data:
        return jsonify({"status": "error", "message": "L'ID de l'entrée et le volume sont requis"}), 400

    input_id = data['inputId']
    volume = data['volume']

    # Valider que le volume est entre 0 et 100
    try:
        volume = int(volume)
        if volume < 0 or volume > 100:
            return jsonify({"status": "error", "message": "Le volume doit être entre 0 et 100"}), 400
    except ValueError:
        return jsonify({"status": "error", "message": "Le volume doit être un nombre entier"}), 400

    result = vmix_manager.adjust_audio_volume(input_id, volume)

    if result:
        return jsonify({"status": "success", "message": f"Volume ajusté à {volume}%"})
    else:
        return jsonify({"status": "error", "message": "Erreur lors de l'ajustement du volume"}), 500

@vmix_bp.route('/audio/status', methods=['GET'])
def get_audio_status():
    """Récupérer le statut audio de toutes les entrées vMix"""
    try:
        audio_status = vmix_manager.get_audio_status()

        if audio_status is not None:
            return jsonify({
                "status": "success",
                "audioStatus": audio_status
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Impossible de récupérer le statut audio"
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erreur lors de la récupération du statut audio: {str(e)}"
        }), 500

@vmix_bp.route('/update-score', methods=['POST'])
def update_score():
    """
    Met à jour le score et les noms des équipes dans vMix
    
    Attend un JSON avec le format suivant:
    {
        "teamA": {
            "name": "Nom Équipe A",
            "score": 10,
            "sets": 2
        },
        "teamB": {
            "name": "Nom Équipe B",
            "score": 8,
            "sets": 1
        },
        "titleInput": "scoreboard"  // Optionnel, nom du titre vMix à mettre à jour
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Aucune donnée fournie", "status": "error"}), 400
            
        # Vérifier que les données nécessaires sont présentes
        if 'teamA' not in data or 'teamB' not in data:
            return jsonify({"error": "Les données des équipes sont requises", "status": "error"}), 400
            
        # Extraire les données
        team_a = data['teamA']
        team_b = data['teamB']
        title_input = data.get('titleInput', 'scoreboard')
        
        # Vérifier que les données minimales sont présentes pour chaque équipe
        if 'name' not in team_a or 'score' not in team_a or 'sets' not in team_a:
            return jsonify({"error": "Données incomplètes pour l'équipe A", "status": "error"}), 400
            
        if 'name' not in team_b or 'score' not in team_b or 'sets' not in team_b:
            return jsonify({"error": "Données incomplètes pour l'équipe B", "status": "error"}), 400
            
        # Mettre à jour le scoreboard dans vMix
        success = vmix_manager.update_scoreboard(
            team_a['name'], 
            team_b['name'], 
            team_a['score'], 
            team_b['score'], 
            team_a['sets'], 
            team_b['sets'],
            title_input
        )
        
        if success:
            return jsonify({
                "message": "Score mis à jour avec succès",
                "status": "success"
            })
        else:
            return jsonify({
                "error": "Erreur lors de la mise à jour du score",
                "status": "error"
            }), 500
            
    except Exception as e:
        return jsonify({
            "error": f"Erreur lors de la mise à jour du score: {str(e)}",
            "status": "error"
        }), 500
