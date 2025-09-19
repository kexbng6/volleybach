import time
from flask import Blueprint, jsonify, request
import os
import json
from flask_socketio import emit
from .websocket import socketio
from .vmix_input_manager import create_vmix_input

#todo revoir les fonctions à partir de add_input

# Blueprint pour l'API de configuration
CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'stream_config.json')
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# Fonction pour charger la configuration depuis le fichier JSON
bp_setup_api = Blueprint('setup_api', __name__, url_prefix='/api')

def ensure_data_dir():
    """Vérifie si le répertoire de données existe, sinon le crée"""
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR)
            print(f"Répertoire de données créé : {DATA_DIR}")
            return True
        except Exception as e:
            print(f"Erreur lors de la création du répertoire de données : {e}")
            return False
    return True

def load_config():
    """Charge la configuration depuis le fichier"""
    ensure_data_dir()
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"stream": {}, "inputs": []}
    return {"stream": {}, "inputs": []}

def save_config(config):
    """Sauvegarde la configuration dans le fichier"""
    ensure_data_dir()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def send_inputs_update(data):
    """Envoie une notification WebSocket pour informer les clients des mises à jour d'inputs"""
    try:
        socketio.emit('inputs_update', data)
        print(f"Notification WebSocket envoyée: {data}")
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification WebSocket: {e}")
        return False

def send_stream_config_update(data):
    """Envoie une notification WebSocket pour informer les clients des mises à jour de la configuration du stream"""
    try:
        socketio.emit('stream_config_update', data)
        print(f"Notification WebSocket de mise à jour de la configuration du stream envoyée: {data}")
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification WebSocket de mise à jour du stream: {e}")
        return False

@bp_setup_api.route('/stream-config')
def get_stream_config():
    config = load_config()
    return jsonify({
        "success": True,
        "config": config.get('stream', {})
    })

@bp_setup_api.route('/save-stream-config', methods=['POST'])
def save_stream_config():
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "Aucune donnée reçue"}), 400

    if not data.get('url'):
        return jsonify({"success": False, "message": "L'URL de la destination de streaming est requise"}), 400
    if not data.get('name'):
        return jsonify({"success": False, "message": "Le nom du stream est obligatoire"}), 400

    config = load_config()
    config['stream'] = data
    save_config(config)

    send_stream_config_update({"config": config.get('stream', {})})

    return jsonify({"success": True, "message": "Configuration du stream sauvegardée avec succès"})

@bp_setup_api.route('/inputs')
def get_inputs():
    """Récupère la liste des inputs configurés"""
    config = load_config()
    return jsonify({
        "success": True,
        "inputs": config.get("inputs", [])
    })

@bp_setup_api.route('/add-input', methods=['POST'])
def add_input():
    """Ajoute une nouvelle entrée (input) à la configuration"""
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "Aucune donnée reçue"}), 400

    # Validation des données
    if not data.get('type'):
        return jsonify({"success": False, "message": "Le type d'entrée (audio/video) est requis"}), 400
    if not data.get('name'):
        return jsonify({"success": False, "message": "Le nom de l'entrée est requis"}), 400
    if not data.get('source'):
        return jsonify({"success": False, "message": "La source de l'entrée est requise"}), 400

    # Vérification du type valide
    if data.get('type') not in ['audio', 'video', 'image', 'title']:
        return jsonify({"success": False, "message": "Le type doit être 'audio','image', 'video' ou 'title'"}), 400

    # Créer l'input dans vMix
    vmix_result = create_vmix_input(data.get('type'), data.get('source'))
    if not vmix_result['success']:
        return jsonify({"success": False, "message": f"Erreur lors de la création dans vMix: {vmix_result.get('message')}"}), 400

    # Ajout de l'input à la configuration
    config = load_config()
    if 'inputs' not in config:
        config['inputs'] = []

    # Création d'un ID unique pour cette entrée
    import time
    input_id = str(int(time.time() * 1000))  # Timestamp en millisecondes

    # Ajout des métadonnées
    input_data = {
        'id': input_id,
        'type': data.get('type'),
        'name': data.get('name'),
        'source': data.get('source'),
        'sourceName': data.get('sourceName', ''),
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }

    config['inputs'].append(input_data)
    save_config(config)

    # Notification WebSocket
    send_inputs_update({"inputs": config.get("inputs", [])})

    return jsonify({
        "success": True,
        "message": "Entrée ajoutée avec succès",
        "input": input_data
    })

@bp_setup_api.route('/remove-input', methods=['POST'])
def remove_input():
    """Supprime une entrée de la configuration"""
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "Aucune donnée reçue"}), 400

    # On peut supprimer par index ou par identifiant
    input_id = data.get('inputId')
    input_data = data.get('input')

    if input_id is None and not input_data:
        return jsonify({"success": False, "message": "Identifiant ou données de l'entrée requis"}), 400

    # Chargement de la configuration
    config = load_config()
    if 'inputs' not in config or not config['inputs']:
        return jsonify({"success": False, "message": "Aucune entrée configurée à supprimer"}), 404

    removed = False

    # Si on a un identifiant numérique (index)
    if isinstance(input_id, int) and 0 <= input_id < len(config['inputs']):
        del config['inputs'][input_id]
        removed = True
    # Si on a un identifiant unique
    elif isinstance(input_id, str):
        for i, inp in enumerate(config['inputs']):
            if inp.get('id') == input_id:
                del config['inputs'][i]
                removed = True
                break
    # Si on a les données de l'entrée
    elif input_data:
        for i, inp in enumerate(config['inputs']):
            if (inp.get('name') == input_data.get('name') and
                inp.get('source') == input_data.get('source')):
                del config['inputs'][i]
                removed = True
                break

    if not removed:
        return jsonify({"success": False, "message": "Entrée non trouvée"}), 404

    # Sauvegarde des modifications
    save_config(config)

    # Notification WebSocket
    send_inputs_update({"inputs": config.get("inputs", [])})

    return jsonify({
        "success": True,
        "message": "Entrée supprimée avec succès"
    })


@bp_setup_api.route('/available-sources')
def get_available_sources():
    """Récupère les sources audio et vidéo disponibles sur le système"""
    import logging
    logger = logging.getLogger('setup_api')

    from .vmix_input_manager import get_vmix_manager

    # Initialiser les listes vides par défaut
    video_sources = []
    camera_sources = []
    audio_sources = []
    blank_sources = []

    vmix = get_vmix_manager()
    logger.info("Tentative de récupération des sources disponibles")

    # Si vMix est connecté, récupérer les sources réelles
    if vmix.check_connection():
        try:
            # Récupérer les inputs existants comme sources potentielles
            logger.info("vMix connecté, récupération des entrées")
            inputs = vmix.get_inputs()

            if inputs:
                # Séparer les entrées par catégorie
                camera_sources = [{'id': inp['id'], 'name': inp['name'], 'type': inp['type']}
                                for inp in inputs if inp.get('category') == 'camera']

                video_sources = [{'id': inp['id'], 'name': inp['name'], 'type': inp['type']}
                               for inp in inputs if inp.get('category') == 'video']

                audio_sources = [{'id': inp['id'], 'name': inp['name'], 'type': inp['type']}
                               for inp in inputs if inp.get('category') == 'audio']

                blank_sources = [{'id': inp['id'], 'name': inp['name'], 'type': inp['type']}
                               for inp in inputs if inp.get('category') == 'blank']

                logger.info(f"Sources récupérées: {len(camera_sources)} caméras, {len(video_sources)} vidéos, {len(audio_sources)} audio, {len(blank_sources)} blank")
            else:
                logger.warning("Aucune entrée n'a été récupérée depuis vMix")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des sources depuis vMix: {str(e)}", exc_info=True)
    else:
        logger.warning("vMix n'est pas connecté. Impossible de récupérer les sources.")

    # En option : sauvegarde des sources dans la configuration
    try:
        config = load_config()
        config['detectedSources'] = {
            'camera': camera_sources,
            'video': video_sources,
            'audio': audio_sources,
            'blank': blank_sources,
            'lastUpdated': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        save_config(config)
        logger.info("Sources sauvegardées dans la configuration")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des sources dans la configuration: {str(e)}")

    return jsonify({
        "success": True,
        "cameraSources": camera_sources,
        "videoSources": video_sources,
        "audioSources": audio_sources,
        "blankSources": blank_sources
    })

@bp_setup_api.route('/available-input-sources')
def get_available_input_sources():
    """Récupère les sources disponibles pour créer de nouveaux inputs dans vMix
       (différent des inputs déjà existants)"""
    import logging
    logger = logging.getLogger('setup_api')

    from .vmix_input_manager import get_vmix_manager
    vmix = get_vmix_manager()

    logger.info("Tentative de récupération des sources disponibles pour de nouveaux inputs")

    if not vmix.check_connection():
        logger.warning("vMix n'est pas connecté. Impossible de récupérer les sources.")
        return jsonify({
            "success": False,
            "message": "vMix n'est pas connecté. Veuillez vous connecter à vMix d'abord."
        }), 400

    try:
        # Récupérer les sources disponibles pour de nouveaux inputs
        sources = vmix.get_available_sources()

        logger.info(f"Sources pour nouveaux inputs récupérées: {len(sources['camera'])} caméras, " +
                   f"{len(sources['video'])} vidéos, {len(sources['audio'])} audio, " +
                   f"{len(sources['blank'])} blank")

        return jsonify({
            "success": True,
            "cameraSources": sources['camera'],
            "videoSources": sources['video'],
            "audioSources": sources['audio'],
            "blankSources": sources['blank']
        })
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des sources pour nouveaux inputs: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Erreur lors de la récupération des sources: {str(e)}"
        }), 500

@bp_setup_api.route('/add-vmix-input', methods=['POST'])
def add_vmix_input():
    """Ajoute un nouvel input directement dans vMix (caméra, fichier vidéo, etc.)"""
    import logging
    logger = logging.getLogger('setup_api')

    data = request.json
    if not data:
        return jsonify({"success": False, "message": "Aucune donnée reçue"}), 400

    from .vmix_input_manager import get_vmix_manager
    vmix = get_vmix_manager()

    if not vmix.check_connection():
        return jsonify({
            "success": False,
            "message": "vMix n'est pas connecté. Veuillez vous connecter à vMix d'abord."
        }), 400

    # Récupération des paramètres
    source_type = data.get('sourceType')
    source_id = data.get('sourceId')
    source_name = data.get('sourceName', '')

    if not source_type or not source_id:
        return jsonify({
            "success": False,
            "message": "Type de source et ID de source requis"
        }), 400

    logger.info(f"Tentative d'ajout d'input vMix: type={source_type}, id={source_id}, nom={source_name}")

    try:
        # Traitement selon le type de source
        result = False
        error_msg = ""

        if source_type == 'camera':
            # Ajout d'une caméra ou d'un périphérique de capture
            result, error_msg = vmix.add_capture_input(source_id, source_name)
        elif source_type == 'video':
            # Ajout d'un fichier vidéo
            result, error_msg = vmix.add_video_input(source_id, source_name)
        elif source_type == 'blank':
            # Ajout d'un input blank
            result, error_msg = vmix.add_blank_input(source_name)
        else:
            error_msg = f"Type de source non pris en charge: {source_type}"

        if result:
            logger.info(f"Input {source_type} ajouté avec succès: {source_name}")
            return jsonify({
                "success": True,
                "message": f"Input {source_name} ajouté avec succès dans vMix"
            })
        else:
            logger.error(f"Échec de l'ajout d'input {source_type}: {error_msg}")
            return jsonify({
                "success": False,
                "message": f"Échec de l'ajout de l'input: {error_msg}"
            }), 400

    except Exception as e:
        logger.exception(f"Erreur lors de l'ajout d'un input vMix: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erreur lors de l'ajout de l'input: {str(e)}"
        }), 500
