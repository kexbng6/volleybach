from flask import Blueprint, request, jsonify
import os
import json
import logging
from ..core.replay_manager import ReplayManager

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('replay_api')

replay_bp = Blueprint('replay', __name__)

# Instance du gestionnaire de replay
replay_manager = ReplayManager()

@replay_bp.route('/config', methods=['GET'])
def get_replay_config():
    """Récupérer la configuration des replays"""
    try:
        config = replay_manager.load_config()
        return jsonify({"config": config})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la configuration des replays: {str(e)}")
        return jsonify({"error": "Erreur lors de la récupération de la configuration"}), 500

@replay_bp.route('/set-duration', methods=['POST'])
def set_replay_duration():
    """Définir la durée du buffer de replay"""
    try:
        data = request.json

        # Valider les données
        if not data or 'duration' not in data:
            return jsonify({"error": "La durée du buffer est requise"}), 400

        duration = int(data['duration'])

        # Vérifier la plage
        if duration < 5 or duration > 60:
            return jsonify({"error": "La durée doit être entre 5 et 60 secondes"}), 400

        # Définir la durée
        result = replay_manager.set_duration(duration)

        if result:
            return jsonify({"status": "success", "message": f"Durée du buffer définie à {duration} secondes"})
        else:
            return jsonify({"error": "Erreur lors de la définition de la durée du buffer"}), 500
    except Exception as e:
        logger.error(f"Erreur lors de la définition de la durée du buffer: {str(e)}")
        return jsonify({"error": f"Erreur lors de la définition de la durée du buffer: {str(e)}"}), 500

@replay_bp.route('/start-recording', methods=['POST'])
def start_replay_recording():
    """Démarrer l'enregistrement des replays"""
    try:
        # Démarrer l'enregistrement
        result = replay_manager.start_recording()

        if result:
            return jsonify({"status": "success", "message": "Enregistrement des replays démarré"})
        else:
            return jsonify({"error": "Erreur lors du démarrage de l'enregistrement des replays"}), 500
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'enregistrement des replays: {str(e)}")
        return jsonify({"error": f"Erreur lors du démarrage de l'enregistrement des replays: {str(e)}"}), 500

@replay_bp.route('/stop-recording', methods=['POST'])
def stop_replay_recording():
    """Arrêter l'enregistrement des replays"""
    try:
        # Arrêter l'enregistrement
        result = replay_manager.stop_recording()

        if result:
            return jsonify({"status": "success", "message": "Enregistrement des replays arrêté"})
        else:
            return jsonify({"error": "Erreur lors de l'arrêt de l'enregistrement des replays"}), 500
    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt de l'enregistrement des replays: {str(e)}")
        return jsonify({"error": f"Erreur lors de l'arrêt de l'enregistrement des replays: {str(e)}"}), 500

@replay_bp.route('/play-last', methods=['POST'])
def play_last_replay():
    """Lire le dernier replay enregistré"""
    try:
        data = request.json

        # Vitesse par défaut
        speed = 100

        # Si une vitesse est spécifiée
        if data and 'speed' in data:
            speed = int(data['speed'])

            # Vérifier la validité de la vitesse
            if speed not in [25, 50, 75, 100]:
                return jsonify({"error": "La vitesse doit être l'une des valeurs suivantes: 25, 50, 75, 100"}), 400

        # Lire le dernier replay
        result = replay_manager.play_last_replay(speed)

        if result:
            return jsonify({"status": "success", "message": f"Lecture du dernier replay à {speed}%"})
        else:
            return jsonify({"error": "Erreur lors de la lecture du dernier replay"}), 500
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du dernier replay: {str(e)}")
        return jsonify({"error": f"Erreur lors de la lecture du dernier replay: {str(e)}"}), 500

@replay_bp.route('/pause', methods=['POST'])
def pause_replay():
    """Mettre en pause la lecture du replay"""
    try:
        # Mettre en pause le replay
        result = replay_manager.pause_replay()

        if result:
            return jsonify({"status": "success", "message": "Replay mis en pause"})
        else:
            return jsonify({"error": "Erreur lors de la mise en pause du replay"}), 500
    except Exception as e:
        logger.error(f"Erreur lors de la mise en pause du replay: {str(e)}")
        return jsonify({"error": f"Erreur lors de la mise en pause du replay: {str(e)}"}), 500

@replay_bp.route('/mark', methods=['POST'])
def mark_replay_event():
    """Marquer un événement de replay"""
    try:
        data = request.json

        # Valeurs par défaut
        name = ""
        event_type = "custom"

        # Si un nom est spécifié
        if data and 'name' in data:
            name = data['name']

        # Si un type est spécifié
        if data and 'type' in data:
            event_type = data['type']

        # Marquer l'événement
        result, events = replay_manager.mark_event(name, event_type)

        if result:
            return jsonify({
                "status": "success",
                "message": "Événement marqué avec succès",
                "events": events
            })
        else:
            return jsonify({"error": "Erreur lors du marquage de l'événement"}), 500
    except Exception as e:
        logger.error(f"Erreur lors du marquage de l'événement: {str(e)}")
        return jsonify({"error": f"Erreur lors du marquage de l'événement: {str(e)}"}), 500

@replay_bp.route('/play-event', methods=['POST'])
def play_replay_event():
    """Lire un événement de replay spécifique"""
    try:
        data = request.json

        # Valider les données
        if not data or 'eventIndex' not in data:
            return jsonify({"error": "L'index de l'événement est requis"}), 400

        event_index = int(data['eventIndex'])

        # Vitesse par défaut
        speed = 100

        # Si une vitesse est spécifiée
        if 'speed' in data:
            speed = int(data['speed'])

            # Vérifier la validité de la vitesse
            if speed not in [25, 50, 75, 100]:
                return jsonify({"error": "La vitesse doit être l'une des valeurs suivantes: 25, 50, 75, 100"}), 400

        # Lire l'événement
        result = replay_manager.play_event(event_index, speed)

        if result:
            return jsonify({"status": "success", "message": f"Lecture de l'événement {event_index} à {speed}%"})
        else:
            return jsonify({"error": "Erreur lors de la lecture de l'événement"}), 500
    except Exception as e:
        logger.error(f"Erreur lors de la lecture de l'événement: {str(e)}")
        return jsonify({"error": f"Erreur lors de la lecture de l'événement: {str(e)}"}), 500

@replay_bp.route('/events', methods=['GET'])
def get_replay_events():
    """Récupérer la liste des événements de replay"""
    try:
        events = replay_manager.load_events()
        return jsonify({"events": events})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des événements de replay: {str(e)}")
        return jsonify({"error": "Erreur lors de la récupération des événements"}), 500

@replay_bp.route('/status', methods=['GET'])
def get_replay_status():
    """Récupérer l'état actuel du système de replay"""
    try:
        status = replay_manager.get_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut des replays: {str(e)}")
        return jsonify({"error": "Erreur lors de la récupération du statut"}), 500

@replay_bp.route('/delete-event', methods=['POST'])
def delete_replay_event():
    """Supprimer un événement de replay spécifique"""
    try:
        data = request.json

        # Valider les données
        if not data or 'eventIndex' not in data:
            return jsonify({"error": "L'index de l'événement est requis"}), 400

        event_index = int(data['eventIndex'])

        # Supprimer l'événement
        success, events, warning = replay_manager.delete_event(event_index)

        if success:
            return jsonify({
                "status": "success",
                "message": "Événement supprimé avec succès",
                "warning": warning,  # Message d'avertissement pour l'interface utilisateur
                "events": events
            })
        else:
            return jsonify({"error": warning}), 500
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'événement: {str(e)}")
        return jsonify({"error": f"Erreur lors de la suppression de l'événement: {str(e)}"}), 500
