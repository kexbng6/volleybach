from flask import Blueprint, request, jsonify, current_app
import logging
from . import vmix_manager
import inspect
import os
import importlib

# Code de débogage pour vérifier l'importation
module_path = inspect.getfile(vmix_manager)
print(f"\n\n============= DÉBOGAGE IMPORTATION =============")
print(f"Chemin du module vmix_manager: {module_path}")
print(f"Méthodes disponibles dans vmix_manager: {dir(vmix_manager)}")
print(f"Méthodes disponibles dans VmixManager: {dir(vmix_manager.VmixManager)}")
print(f"============= FIN DÉBOGAGE =============\n\n")

# Configuration du logger
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('broadcast_api')

bp_broadcast_api = Blueprint('broadcast_api', __name__)

# Initialiser le gestionnaire vMix avec les paramètres par défaut
# Réinitialisation de l'instance pour garantir qu'on utilise la dernière version du code
importlib.reload(vmix_manager)
vmix = vmix_manager.VmixManager()

# Débogage de l'instance après initialisation
print(f"\n\n============= DÉBOGAGE INSTANCE VMIX =============")
print(f"Méthodes disponibles dans l'instance vmix: {dir(vmix)}")
print(f"Type de l'instance vmix: {type(vmix)}")
if hasattr(vmix, 'set_replay_duration'):
    print("La méthode set_replay_duration existe dans l'instance vmix!")
else:
    print("La méthode set_replay_duration N'EXISTE PAS dans l'instance vmix!")

if hasattr(vmix, 'get_last_event_index'):
    print("La méthode get_last_event_index existe dans l'instance vmix!")
else:
    print("La méthode get_last_event_index N'EXISTE PAS dans l'instance vmix!")
print(f"============= FIN DÉBOGAGE INSTANCE =============\n\n")

@bp_broadcast_api.route('/api/broadcast/camera/cut', methods=['POST'])
def cut_to_camera():
    """Change l'entrée active en mode CUT"""
    try:
        data = request.json
        input_number = data.get('input')

        if not input_number:
            return jsonify({
                'success': False,
                'error': "Numéro d'input non fourni"
            }), 400

        success = vmix.cut_to_input(input_number)

        return jsonify({
            'success': success,
            'input': input_number
        })
    except Exception as e:
        logger.error(f"Erreur lors du changement d'input (CUT): {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp_broadcast_api.route('/api/broadcast/camera/transition', methods=['POST'])
def transition_to_camera():
    """Change l'entrée active avec une transition"""
    try:
        data = request.json
        input_number = data.get('input')
        duration = data.get('duration', 500)
        effect = data.get('effect', 'Fade')

        if not input_number:
            return jsonify({
                'success': False,
                'error': "Numéro d'input non fourni"
            }), 400

        success = vmix.transition_to_input(input_number, duration, effect)

        return jsonify({
            'success': success,
            'input': input_number,
            'duration': duration,
            'effect': effect
        })
    except Exception as e:
        logger.error(f"Erreur lors du changement d'input (transition): {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp_broadcast_api.route('/api/broadcast/audio/toggle', methods=['POST'])
def toggle_audio():
    """Active ou désactive l'audio d'une entrée"""
    try:
        data = request.json
        input_number = data.get('input')
        mute_state = data.get('mute')  # None, True ou False

        if not input_number:
            return jsonify({
                'success': False,
                'error': "Numéro d'input non fourni"
            }), 400

        success = vmix.toggle_audio(input_number, mute_state)

        return jsonify({
            'success': success,
            'input': input_number,
            'action': 'toggle' if mute_state is None else ('mute' if mute_state else 'unmute')
        })
    except Exception as e:
        logger.error(f"Erreur lors de la modification de l'état audio: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp_broadcast_api.route('/api/broadcast/audio/volume', methods=['POST'])
def adjust_volume():
    """Ajuste le volume d'une entrée audio"""
    try:
        data = request.json
        input_number = data.get('input')
        volume = data.get('volume')

        if not input_number or volume is None:
            return jsonify({
                'success': False,
                'error': "Numéro d'input ou volume non fourni"
            }), 400

        # S'assurer que volume est un nombre entre 0 et 100
        try:
            volume = float(volume)
            volume = max(0, min(100, volume))
        except ValueError:
            return jsonify({
                'success': False,
                'error': "Le volume doit être un nombre entre 0 et 100"
            }), 400

        success = vmix.adjust_audio_volume(input_number, volume)

        return jsonify({
            'success': success,
            'input': input_number,
            'volume': volume
        })
    except Exception as e:
        logger.error(f"Erreur lors de l'ajustement du volume: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp_broadcast_api.route('/api/broadcast/streaming', methods=['POST'])
def control_streaming():
    """Contrôle le streaming (Start/Stop)"""
    try:
        data = request.json
        action = data.get('action', 'Start')

        if action not in ['Start', 'Stop']:
            return jsonify({
                'success': False,
                'error': "Action invalide. Utilisez 'Start' ou 'Stop'."
            }), 400

        success = vmix.control_streaming(action)

        return jsonify({
            'success': success,
            'action': action
        })
    except Exception as e:
        logger.error(f"Erreur lors du contrôle du streaming: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Routes pour les fonctionnalités de replay
@bp_broadcast_api.route('/api/broadcast/replay/start', methods=['POST'])
def start_replay_recording():
    """Démarre l'enregistrement du replay"""
    try:
        data = request.json
        duration = data.get('duration', 8)

        # Démarrer directement l'enregistrement sans configurer la durée du buffer
        # pour éviter l'erreur 'VmixManager' object has no attribute 'set_replay_duration'
        success = vmix.start_recording_replay()

        # Essayer de configurer la durée du buffer si la méthode existe
        try:
            if hasattr(vmix, 'set_replay_duration'):
                vmix.set_replay_duration(duration)
            else:
                logger.warning("La méthode set_replay_duration n'existe pas dans l'objet vmix")
        except Exception as buffer_error:
            logger.warning(f"Impossible de configurer la durée du buffer: {buffer_error}")

        return jsonify({
            'success': success,
            'action': 'start_recording',
            'duration': duration
        })
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'enregistrement du replay: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp_broadcast_api.route('/api/broadcast/replay/stop', methods=['POST'])
def stop_replay_recording():
    """Arrête l'enregistrement du replay"""
    try:
        success = vmix.stop_recording_replay()
        
        return jsonify({
            'success': success,
            'action': 'stop_recording'
        })
    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt de l'enregistrement du replay: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp_broadcast_api.route('/api/broadcast/replay/play', methods=['POST'])
def play_replay():
    """Joue un replay avec la vitesse spécifiée"""
    try:
        data = request.json
        speed = data.get('speed', 100)
        timestamp = data.get('timestamp')

        # Si un timestamp est fourni, c'est un événement spécifique
        if timestamp:
            # Logique pour jouer un événement spécifique
            # Note: ceci est conceptuel, car vMix ne stocke pas les événements par timestamp
            # Dans une implémentation réelle, vous devriez stocker les événements et leurs index
            event_index = 0  # À remplacer par la logique pour trouver l'index de l'événement
            success = vmix.play_replay_event(event_index, speed)
        else:
            # Jouer le dernier replay
            success = vmix.play_last_replay(speed)

        return jsonify({
            'success': success,
            'action': 'play_replay',
            'speed': speed
        })
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du replay: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp_broadcast_api.route('/api/broadcast/replay/pause', methods=['POST'])
def pause_replay():
    """Met en pause la lecture du replay"""
    try:
        success = vmix.pause_replay()
        
        return jsonify({
            'success': success,
            'action': 'pause'
        })
    except Exception as e:
        logger.error(f"Erreur lors de la mise en pause du replay: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp_broadcast_api.route('/api/broadcast/replay/mark', methods=['POST'])
def mark_replay_event():
    """Marque un événement dans le replay"""
    try:
        data = request.json
        event_name = data.get('name', '')
        duration = data.get('duration', 8)  # Récupérer la durée du buffer
        speed = data.get('speed', 100)  # Récupérer la vitesse (par défaut 100%)

        # Marquer l'événement dans vMix en passant tous les paramètres
        success = vmix.mark_replay_event(event_name, duration=duration, speed=speed)
        
        # Récupérer l'index de l'événement
        event_index = vmix.get_last_event_index()

        # Envoyer une notification via SocketIO si disponible
        if hasattr(current_app, 'socketio'):
            event_data = {
                'name': event_name,
                'timestamp': data.get('timestamp'),
                'duration': duration,
                'speed': speed,
                'eventIndex': event_index
            }
            current_app.socketio.emit('replay_marked', event_data)

        return jsonify({
            'success': success,
            'action': 'mark_event',
            'name': event_name,
            'timestamp': data.get('timestamp'),
            'duration': duration,
            'speed': speed,
            'eventIndex': event_index
        })
    except Exception as e:
        logger.error(f"Erreur lors du marquage d'un événement replay: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp_broadcast_api.route('/api/broadcast/replay/duration', methods=['POST'])
def set_replay_duration():
    """Configure la durée du buffer de replay"""
    try:
        data = request.json
        duration = data.get('duration', 8)

        # Vérifier que la durée est dans une plage raisonnable
        if duration < 1 or duration > 60:
            return jsonify({
                'success': False,
                'error': "La durée doit être comprise entre 1 et 60 secondes"
            }), 400
            
        success = vmix.set_replay_duration(duration)

        return jsonify({
            'success': success,
            'action': 'set_duration',
            'duration': duration
        })
    except Exception as e:
        logger.error(f"Erreur lors de la configuration de la durée du replay: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp_broadcast_api.route('/api/broadcast/replays', methods=['GET'])
def get_replay_events():
    """Récupère la liste des événements de replay marqués"""
    try:
        # Dans une implémentation réelle, vous récupéreriez les événements depuis
        # une base de données ou un autre système de stockage
        events = vmix.get_replay_events()

        # Exemple de structure de réponse
        return jsonify({
            'success': True,
            'replays': events
        })
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des événements replay: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
