import time
from flask import Blueprint, jsonify, request
import os
import csv
import json
from flask_socketio import emit
import uuid

from .setup_api import bp_setup_api
from .websocket import socketio
from PIL import Image

bp_setup_team = Blueprint('setup_team', __name__, url_prefix='/team')

def create_dir_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def check_jpeg_png(filename):
    """Vérifie si le fichier est un JPEG ou PNG valide"""
    if not os.path.exists(filename):
        return False
    try:
        # Ouvre le fichier pour vérifier son type rb = mode binaire
        with open(filename, 'rb') as file:
            img = Image.open(file)
            if img.format not in ['JPEG', 'PNG']:
                return False
            # img.verify() # Vérifie que le fichier est un image valide. La méthode verify() lève une exception si le fichier n'est pas valide
            return True
    except Exception as e:
        print(f"Erreur lors de la vérification du fichier {filename}: {e}")
        return False


def load_team_logo(logo_file,team_name):
    """Charge le logo de l'équipe depuis un fichier jpeg ou png"""
    media_folder = os.path.join(os.path.dirname(__file__), "static", "media", "team_logos")

    create_dir_if_not_exists(media_folder)

    if not check_jpeg_png(logo_file):
        print(f"Le fichier {logo_file} n'est pas un JPEG ou PNG valide.")
        return None

    # Créer un nom de fichier unique avec l'ID de l'équipe
    filename = f"team_{team_name}_logo.{'jpg' if logo_file.lower().endswith('.jpg') else 'png'}"
    destination = os.path.join(media_folder, filename)

    # Copier le fichier vers le dossier médias
    try:
        with open(logo_file, 'rb') as src_file:
            img = Image.open(src_file)
            img.save(destination)
        return destination
    except Exception as e:
        print(f"Erreur lors de la copie du logo de l'équipe: {e}")
        return None

def get_team_name():
    try:
        team_name=request.form.get('team_name', '').strip()
        if team_name:
            return team_name
        return None
    except Exception as e:
        print(f"Erreur lors de la récupération du nom d'équipe: {e}")
        return None

def load_team_players_from_csv(csv_file):
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            players = []
            #required_fields = ['nom', 'prenom']
            optional_fields = ['numero', 'position', 'date_naissance','taille']
            for row in csv_reader:
                player = {
                    'prenom':row['prenom'].strip(),
                    'nom':row['nom'].strip()
                }
                for field in optional_fields:
                    if field in row:
                        player[field] = row[field].strip()
                players.append(player)
        return players

    except Exception as e:
        print(f"Erreur lors du chargement des joueurs depuis le fichier CSV: {e}")
        return None

def save_teams_to_json(teams_data):
    """Sauvegarde les données des équipes dans le fichier JSON"""
    teams_file = os.path.join(os.path.dirname(__file__), "teams.json")
    try:
        with open(teams_file, 'w', encoding='utf-8') as f:
            json.dump(teams_data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des équipes: {e}")
        return False

def load_teams_from_json():
    """Charge les données des équipes depuis le fichier JSON"""
    teams_file = os.path.join(os.path.dirname(__file__), "teams.json")
    if not os.path.exists(teams_file):
        return {}
    try:
        with open(teams_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement des équipes: {e}")
        return {}

@bp_setup_team.route('/teams', methods=['GET'])
def get_teams():
    """Récupère la liste des équipes"""
    teams = load_teams_from_json()
    return jsonify({"teams": list(teams.values())})

@bp_setup_team.route('/teams/<team_id>', methods=['GET'])
def get_team(team_id):
    """Récupère les détails d'une équipe spécifique"""
    teams = load_teams_from_json()
    if team_id in teams:
        return jsonify(teams[team_id])
    return jsonify({"error": "Équipe non trouvée"}), 404

def create_team(data=None):
    """Crée une nouvelle équipe"""
    if data is None:
        # Cas d'une requête HTTP directe
        team_name = get_team_name()
        logo_file = request.files.get('team_logo')
        players_file = request.files.get('players_csv')
    else:
        # Cas d'un appel depuis l'API
        team_name = data.get('team_name')
        logo_file = data.get('team_logo')
        players_file = data.get('players_csv')

    if not team_name:
        return {"error": "Nom d'équipe invalide"}, 400

    # Générer un ID unique pour l'équipe
    team_id = str(uuid.uuid4())

    # Préparation des données de l'équipe
    team_data = {
        "id": team_id,
        "name": team_name,
        "logo_path": None,
        "players": []
    }

    # Traitement du logo
    if logo_file:
        temp_path = os.path.join(os.path.dirname(__file__), "temp", logo_file.filename)
        create_dir_if_not_exists(os.path.dirname(temp_path))
        logo_file.save(temp_path)
        logo_path = load_team_logo(temp_path, team_name)
        if logo_path:
            team_data["logo_path"] = logo_path
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Traitement du fichier CSV des joueurs
    if players_file:
        temp_path = os.path.join(os.path.dirname(__file__), "temp", players_file.filename)
        create_dir_if_not_exists(os.path.dirname(temp_path))
        players_file.save(temp_path)
        players = load_team_players_from_csv(temp_path)
        if players:
            team_data["players"] = players
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Sauvegarder l'équipe
    teams = load_teams_from_json()
    teams[team_id] = team_data
    if save_teams_to_json(teams):
        # Émettre un événement WebSocket
        socketio.emit('team_created', team_data)
        return {"success": True, "message": "Équipe créée avec succès", "team": team_data}

    return {"error": "Erreur lors de la sauvegarde de l'équipe"}, 500

@bp_setup_team.route('/create_team', methods=['POST'])
def create_team_route():
    """Route pour créer une nouvelle équipe"""
    result, status = create_team()
    return jsonify(result), status if isinstance(status, int) else 200

@bp_setup_team.route('/teams/<team_id>', methods=['PUT'])
def update_team(team_id):
    """Met à jour une équipe existante"""
    teams = load_teams_from_json()
    if team_id not in teams:
        return jsonify({"error": "Équipe non trouvée"}), 404

    team_data = teams[team_id]

    # Mise à jour du nom si fourni
    new_name = request.form.get('team_name')
    if new_name:
        team_data["name"] = new_name.strip()

    # Mise à jour du logo si fourni
    logo_file = request.files.get('team_logo')
    if logo_file:
        temp_path = os.path.join(os.path.dirname(__file__), "temp", logo_file.filename)
        create_dir_if_not_exists(os.path.dirname(temp_path))
        logo_file.save(temp_path)
        logo_path = load_team_logo(temp_path, team_data["name"])
        if logo_path:
            # Supprimer l'ancien logo si existant
            if team_data.get("logo_path") and os.path.exists(team_data["logo_path"]):
                os.remove(team_data["logo_path"])
            team_data["logo_path"] = logo_path
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Mise à jour des joueurs si fichier CSV fourni
    players_file = request.files.get('players_csv')
    if players_file:
        temp_path = os.path.join(os.path.dirname(__file__), "temp", players_file.filename)
        create_dir_if_not_exists(os.path.dirname(temp_path))
        players_file.save(temp_path)
        players = load_team_players_from_csv(temp_path)
        if players:
            team_data["players"] = players
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Sauvegarder les modifications
    teams[team_id] = team_data
    if save_teams_to_json(teams):
        # Émettre un événement WebSocket
        socketio.emit('team_updated', team_data)
        return jsonify({"success": True, "message": "Équipe mise à jour avec succès", "team": team_data})

    return jsonify({"error": "Erreur lors de la mise à jour de l'équipe"}), 500

@bp_setup_team.route('/teams/<team_id>', methods=['DELETE'])
def delete_team(team_id):
    """Supprime une équipe"""
    teams = load_teams_from_json()
    if team_id not in teams:
        return jsonify({"error": "Équipe non trouvée"}), 404

    team_data = teams[team_id]

    # Supprimer le logo si existant
    if team_data.get("logo_path") and os.path.exists(team_data["logo_path"]):
        os.remove(team_data["logo_path"])

    # Supprimer l'équipe du fichier JSON
    del teams[team_id]
    if save_teams_to_json(teams):
        # Émettre un événement WebSocket
        socketio.emit('team_deleted', {"id": team_id})
        return jsonify({"success": True, "message": "Équipe supprimée avec succès"})

    return jsonify({"error": "Erreur lors de la suppression de l'équipe"}), 500

@bp_setup_team.route('/update_roster_in_vmix', methods=['POST'])
def update_roster_in_vmix():
    """Met à jour la liste des joueurs dans un titre vMix."""
    try:
        if 'csvFile' not in request.files:
            return jsonify({'success': False, 'error': "Aucun fichier CSV n'a été fourni"})

        csv_file = request.files['csvFile']
        team_name = request.form.get('teamName', 'Équipe')
        team_logo = request.form.get('teamLogo', '')
        title_input = request.form.get('titleInput', '')

        # Vérifier que le fichier a un nom et une extension valide
        if csv_file.filename == '':
            return jsonify({'success': False, 'error': "Nom de fichier invalide"})

        if not csv_file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': "Le fichier doit être au format CSV"})

        # Sauvegarder temporairement le fichier CSV
        temp_csv_path = os.path.join(os.path.dirname(__file__), "temp_roster.csv")
        csv_file.save(temp_csv_path)

        # Lire les joueurs depuis le CSV
        players = load_team_players_from_csv(temp_csv_path)

        # Supprimer le fichier temporaire
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)

        if not players:
            return jsonify({'success': False, 'error': "Aucun joueur trouvé dans le fichier CSV"})

        # Importer le gestionnaire vMix
        from .vmix_manager import VmixManager
        vmix = VmixManager()

        # Vérifier que vMix est accessible
        if not vmix.check_connection():
            return jsonify({'success': False, 'error': "Impossible de se connecter à vMix"})

        # Vérifier que l'input existe
        if not title_input:
            return jsonify({'success': False, 'error': "Aucun input vMix spécifié"})

        # Mettre à jour le titre dans vMix
        # Vérifier les noms des champs dans le titre GT
        try:
            # Obtenir les informations sur les champs de texte disponibles dans le titre
            title_info = vmix.get_title_info(title_input)

            # Chercher les indices corrects pour les champs de texte
            team_name_index = None
            team_logo_index = None
            player_name_indices = []
            player_number_indices = []

            if title_info and 'texts' in title_info:
                for idx, text_info in enumerate(title_info['texts']):
                    name = text_info.get('name', '').lower()
                    if 'teamname' in name:
                        team_name_index = idx
                    elif 'teamlogo' in name:
                        team_logo_index = idx
                    elif 'name' in name and any(str(i) in name for i in range(1, 10)):
                        player_name_indices.append((idx, int(next(i for i in name if i.isdigit()))))
                    elif 'number' in name and any(str(i) in name for i in range(1, 10)):
                        player_number_indices.append((idx, int(next(i for i in name if i.isdigit()))))

            # Trier les indices par numéro de joueur
            player_name_indices.sort(key=lambda x: x[1])
            player_number_indices.sort(key=lambda x: x[1])

            # Si on n'a pas pu détecter automatiquement les indices, utiliser les valeurs par défaut
            if team_name_index is None:
                team_name_index = 0  # Par défaut
            if team_logo_index is None and 'teamlogo' in [t.get('name', '').lower() for t in title_info.get('texts', [])]:
                team_logo_index = 1  # Par défaut

        except Exception as e:
            print(f"Erreur lors de la détection des champs du titre: {e}")
            # Utiliser les indices par défaut en cas d'erreur
            team_name_index = 0
            team_logo_index = 1
            player_name_indices = [(2 + i*2, i+1) for i in range(9)]
            player_number_indices = [(3 + i*2, i+1) for i in range(9)]

        # 1. Nom de l'équipe
        print(f"Définition du nom d'équipe '{team_name}' à l'index {team_name_index}")
        vmix.set_text(title_input, team_name, team_name_index)

        # 2. Logo de l'équipe (si disponible et si l'index existe)
        if team_logo and team_logo_index is not None:
            print(f"Définition du logo d'équipe à l'index {team_logo_index}")
            vmix.set_text(title_input, team_logo, team_logo_index)

        # 3. Joueurs
        player_indices_used = []
        for i, player in enumerate(players):
            if i >= 9:  # Limiter à 9 joueurs maximum
                break

            # Format du nom: "Prénom NOM"
            player_name = f"{player.get('prenom', '')} {player.get('nom', '').upper()}"
            player_number = player.get('numero', '')

            # Utiliser les indices détectés si disponibles, sinon utiliser la méthode par défaut
            if i < len(player_name_indices):
                name_index = player_name_indices[i][0]
                player_indices_used.append(name_index)
                print(f"Définition du nom du joueur {i+1} '{player_name}' à l'index {name_index}")
                vmix.set_text(title_input, player_name, name_index)
            else:
                name_index = 2 + (i * 2)  # Méthode par défaut
                player_indices_used.append(name_index)
                print(f"Définition du nom du joueur {i+1} '{player_name}' à l'index {name_index} (défaut)")
                vmix.set_text(title_input, player_name, name_index)

            if i < len(player_number_indices):
                number_index = player_number_indices[i][0]
                player_indices_used.append(number_index)
                print(f"Définition du numéro du joueur {i+1} '{player_number}' à l'index {number_index}")
                vmix.set_text(title_input, player_number, number_index)
            else:
                number_index = 3 + (i * 2)  # Méthode par défaut
                player_indices_used.append(number_index)
                print(f"Définition du numéro du joueur {i+1} '{player_number}' à l'index {number_index} (défaut)")
                vmix.set_text(title_input, player_number, number_index)

        # Pour les joueurs manquants, mettre des valeurs vides
        # Récupérer tous les indices possibles de playerName et playerNumber
        all_name_indices = set(idx for idx, _ in player_name_indices)
        all_number_indices = set(idx for idx, _ in player_number_indices)

        # Si ces ensembles sont vides, utiliser la méthode par défaut
        if not all_name_indices:
            all_name_indices = set(2 + (i * 2) for i in range(9))
        if not all_number_indices:
            all_number_indices = set(3 + (i * 2) for i in range(9))

        # Effacer les champs inutilisés
        for idx in all_name_indices.union(all_number_indices):
            if idx not in player_indices_used:
                print(f"Effacement du champ à l'index {idx}")
                vmix.set_text(title_input, "", idx)

        return jsonify({
            'success': True,
            'message': f"Liste de {len(players)} joueurs importée dans vMix avec succès",
            'team': team_name
        })

    except Exception as e:
        print(f"Erreur lors de la mise à jour du roster dans vMix: {e}")
        return jsonify({'success': False, 'error': str(e)})

@bp_setup_team.route('/show_player_details_in_vmix', methods=['POST'])
def show_player_details_in_vmix():
    """Affiche les détails d'un joueur dans un titre vMix."""
    try:
        player_data = request.json
        if not player_data:
            return jsonify({'success': False, 'error': "Aucune donnée de joueur fournie"})

        # Récupérer les données du joueur
        player_name = f"{player_data.get('prenom', '')} {player_data.get('nom', '').upper()}"
        player_number = player_data.get('numero', '')
        player_position = player_data.get('position', '')
        player_age = player_data.get('date_naissance', '')
        player_size = player_data.get('taille', '')
        player_photo = player_data.get('photo', '')
        title_input = player_data.get('titleInput', '')

        # Importer le gestionnaire vMix
        from .vmix_manager import VmixManager
        vmix = VmixManager()

        # Vérifier que vMix est accessible
        if not vmix.check_connection():
            return jsonify({'success': False, 'error': "Impossible de se connecter à vMix"})

        # Vérifier que l'input existe
        if not title_input:
            return jsonify({'success': False, 'error': "Aucun input vMix spécifié"})

        # Mettre à jour le titre dans vMix
        # Essayer d'obtenir les informations sur les champs de texte disponibles
        try:
            title_info = vmix.get_title_info(title_input)
            field_indices = {}

            if title_info and 'texts' in title_info:
                for idx, text_info in enumerate(title_info['texts']):
                    name = text_info.get('name', '').lower()
                    # Mise à jour des mappages pour correspondre exactement aux noms des champs dans GT Title Designer
                    if 'playername' in name:
                        field_indices['playerName'] = idx
                    elif 'playernumber' in name :
                        field_indices['playerNumber'] = idx
                    elif 'playerstat' in name:
                        field_indices['playerStat'] = idx
                    elif 'Position' in name:
                        field_indices['position'] = idx
                    elif 'playersize' in name:
                        field_indices['playerSize'] = idx
                    elif 'playerage' in name:
                        field_indices['playerAge'] = idx
                    elif 'playerphoto' in name:
                        field_indices['playerPhoto'] = idx
        except Exception as e:
            print(f"Erreur lors de la détection des champs du titre: {e}")
            # Utiliser des indices par défaut en cas d'erreur avec les noms de champs corrects
            field_indices = {
                'playerStat': 0,
                'position': 1,
                # text field cm
                'playerSize': 3,
                'playerAge': 4,
                'playerNumber': 5,
                'playerName': 6,





                'playerPhoto': 6
            }

        # Mise à jour des champs avec les données du joueur
        if 'playerName' in field_indices:
            vmix.set_text(title_input, player_name, field_indices['playerName'])
        if 'playerStat' in field_indices:
            vmix.set_text(title_input, player_number, field_indices['playerStat'])
        if 'position' in field_indices:
            vmix.set_text(title_input, player_position, field_indices['position'])
        if 'playerSize' in field_indices:
            vmix.set_text(title_input, player_size, field_indices['playerSize'])
        if 'playerAge' in field_indices:
            vmix.set_text(title_input, player_age, field_indices['playerAge'])
        if 'playerNumber' in field_indices:
            vmix.set_text(title_input, player_number, field_indices['playerNumber'])
        if 'playerPhoto' in field_indices and player_photo:
            vmix.set_text(title_input, player_photo, field_indices['playerPhoto'])

        return jsonify({
            'success': True,
            'message': f"Détails du joueur {player_name} affichés dans vMix avec succès"
        })

    except Exception as e:
        print(f"Erreur lors de l'affichage des détails du joueur dans vMix: {e}")
        return jsonify({'success': False, 'error': str(e)})
