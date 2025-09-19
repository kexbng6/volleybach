from flask_socketio import SocketIO, emit
import json

# TODO: vérifier comment fonctionne Flask-SocketIO

#Initialisation de l'extension
socketio = SocketIO()


def init_app(app):
    """Initialise l'extension SocketIO avec l'application Flask"""
    socketio.init_app(app, cors_allowed_origins="*")

    # Définir les gestionnaires d'événements WebSocket ici
    @socketio.on('connect')
    def handle_connect():
        """Gère la connexion d'un client WebSocket"""
        print("Client connecté au WebSocket")
        emit('status', {'connected': True})

    @socketio.on('disconnect')
    def handle_disconnect():
        """Gère la déconnexion d'un client WebSocket"""
        print("Client déconnecté du WebSocket")

    @socketio.on('subscribe_score_updates')
    def handle_score_subscription(data):
        """Gère les abonnements aux mises à jour de score"""
        # Vous pourriez utiliser un ID de match ou une autre référence
        match_id = data.get('match_id', 'default')
        print(f"Client abonné aux mises à jour du match {match_id}")
        # Joindre une "room" spécifique au match
        join_room(match_id)

    # Exemple d'autres événements que vous pourriez implémenter
    @socketio.on('vmix_status_request')
    def handle_vmix_status_request():
        """Envoie l'état actuel de la connexion vMix"""
        # Accéder à votre état global ou vérifier vMix directement
        from .api import app_state
        emit('vmix_status_update', {
            'connected': app_state.get('vmix_connected', False)
        })


def send_score_update(match_id, score_data):
    """Envoie une mise à jour de score à tous les clients abonnés"""
    socketio.emit('score_update', score_data, room=match_id)


def send_vmix_status_update(is_connected):
    """Envoie une mise à jour de statut vMix à tous les clients"""
    socketio.emit('vmix_status_update', {
        'connected': is_connected
    })


def send_inputs_update(inputs_data):
    """Envoie une mise à jour des inputs configurés"""
    socketio.emit('inputs_update', inputs_data)
