import os
import json
import time
import logging
from datetime import datetime
from .vmix_manager import VMixManager

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('replay_manager')

class ReplayManager:
    """
    Gestionnaire de replays pour vMix.
    Cette classe gère l'enregistrement, la lecture et le marquage des replays dans vMix.
    """

    def __init__(self):
        """Initialise le gestionnaire de replay."""
        self.vmix = VMixManager()

        # Chemins pour les fichiers de configuration et de données
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_file = os.path.join(self.base_path, 'data', 'replay_config.json')
        self.events_file = os.path.join(self.base_path, 'data', 'replay_events.json')

        # Créer les répertoires s'ils n'existent pas
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        # Charger ou initialiser la configuration
        self.load_config()

        # Charger ou initialiser les événements
        self.load_events()

        # État actuel du système de replay
        self.is_recording = False
        self.is_playing = False
        self.recording_start_time = None

    def load_config(self):
        """Charge la configuration des replays depuis le fichier JSON."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                # Configuration par défaut
                self.config = {
                    'duration': 8,
                    'speed': 50,
                    'enableAutoReplay': False,
                    'events': {
                        'point': True,
                        'set': True,
                        'match': True
                    }
                }
                # Sauvegarder la configuration par défaut
                self.save_config()

            logger.info(f"Configuration des replays chargée: {self.config}")
            return self.config
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration des replays: {str(e)}")
            # En cas d'erreur, utiliser une configuration par défaut
            self.config = {
                'duration': 8,
                'speed': 50,
                'enableAutoReplay': False,
                'events': {
                    'point': True,
                    'set': True,
                    'match': True
                }
            }
            return self.config

    def save_config(self):
        """Sauvegarde la configuration des replays dans le fichier JSON."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration des replays sauvegardée")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration des replays: {str(e)}")
            return False

    def load_events(self):
        """Charge les événements de replay depuis le fichier JSON."""
        try:
            if os.path.exists(self.events_file):
                with open(self.events_file, 'r') as f:
                    self.events = json.load(f)
            else:
                self.events = []
                # Sauvegarder la liste d'événements vide
                self.save_events()

            logger.info(f"Événements de replay chargés: {len(self.events)} événements")
            return self.events
        except Exception as e:
            logger.error(f"Erreur lors du chargement des événements de replay: {str(e)}")
            self.events = []
            return self.events

    def save_events(self):
        """Sauvegarde les événements de replay dans le fichier JSON."""
        try:
            with open(self.events_file, 'w') as f:
                json.dump(self.events, f, indent=2)
            logger.info(f"Événements de replay sauvegardés: {len(self.events)} événements")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des événements de replay: {str(e)}")
            return False

    def set_duration(self, duration):
        """
        Définit la durée du buffer de replay.

        Args:
            duration (int): Durée en secondes (5-60)

        Returns:
            bool: True si la durée a été définie avec succès, False sinon
        """
        try:
            # Vérifier que la durée est dans une plage raisonnable
            if not isinstance(duration, (int, float)) or duration < 5 or duration > 60:
                logger.error(f"Durée de replay invalide: {duration}")
                return False

            # Vérifier la connexion à vMix
            if not self.vmix.check_connection():
                logger.error("Impossible de se connecter à vMix")
                return False

            # Définir la durée du buffer dans vMix
            command = f"ReplaySetDuration Input={duration}"
            result = self.vmix.send_command(command)

            if result:
                # Mettre à jour la configuration
                self.config['duration'] = duration
                self.save_config()
                logger.info(f"Durée du buffer de replay définie à {duration} secondes")
                return True
            else:
                logger.error("Échec de la définition de la durée du buffer de replay")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de la définition de la durée du buffer de replay: {str(e)}")
            return False

    def start_recording(self):
        """
        Démarre l'enregistrement des replays.

        Returns:
            bool: True si l'enregistrement a démarré avec succès, False sinon
        """
        try:
            # Vérifier la connexion à vMix
            if not self.vmix.check_connection():
                logger.error("Impossible de se connecter à vMix")
                return False

            # Démarrer l'enregistrement dans vMix
            command = "ReplayStartRecording"
            result = self.vmix.send_command(command)

            if result:
                self.is_recording = True
                self.recording_start_time = datetime.now()
                logger.info("Enregistrement des replays démarré")
                return True
            else:
                logger.error("Échec du démarrage de l'enregistrement des replays")
                return False
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de l'enregistrement des replays: {str(e)}")
            return False

    def stop_recording(self):
        """
        Arrête l'enregistrement des replays.

        Returns:
            bool: True si l'enregistrement a été arrêté avec succès, False sinon
        """
        try:
            # Vérifier la connexion à vMix
            if not self.vmix.check_connection():
                logger.error("Impossible de se connecter à vMix")
                return False

            # Arrêter l'enregistrement dans vMix
            command = "ReplayStopRecording"
            result = self.vmix.send_command(command)

            if result:
                self.is_recording = False
                self.recording_start_time = None
                logger.info("Enregistrement des replays arrêté")
                return True
            else:
                logger.error("Échec de l'arrêt de l'enregistrement des replays")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt de l'enregistrement des replays: {str(e)}")
            return False

    def play_last_replay(self, speed=100):
        """
        Lit le dernier replay enregistré.

        Args:
            speed (int): Vitesse de lecture en pourcentage (25, 50, 75, 100)

        Returns:
            bool: True si la lecture a démarré avec succès, False sinon
        """
        try:
            # Vérifier que la vitesse est valide
            if speed not in [25, 50, 75, 100]:
                logger.error(f"Vitesse de replay invalide: {speed}")
                return False

            # Vérifier la connexion à vMix
            if not self.vmix.check_connection():
                logger.error("Impossible de se connecter à vMix")
                return False

            # Utiliser ReplayPlay au lieu de ReplayPlayLast
            # D'après les logs, ReplayPlayEvent fonctionne, donc essayons d'utiliser une commande similaire
            command = "ReplayPlay"
            params = {"Speed": speed}

            logger.info(f"Lecture du dernier replay à {speed}%")
            result = self.vmix.send_command(command, **params)

            if result:
                self.is_playing = True
                logger.info(f"Lecture du dernier replay à {speed}% réussie")
                return True
            else:
                logger.error("Échec de la lecture du dernier replay")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du dernier replay: {str(e)}")
            return False

    def pause_replay(self):
        """
        Met en pause la lecture du replay.

        Returns:
            bool: True si la pause a été activée avec succès, False sinon
        """
        try:
            # Vérifier la connexion à vMix
            if not self.vmix.check_connection():
                logger.error("Impossible de se connecter à vMix")
                return False

            # Mettre en pause le replay dans vMix
            command = "ReplayPause"
            result = self.vmix.send_command(command)

            if result:
                self.is_playing = False
                logger.info("Replay mis en pause")
                return True
            else:
                logger.error("Échec de la mise en pause du replay")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de la mise en pause du replay: {str(e)}")
            return False

    def mark_event(self, name, event_type="point"):
        """
        Marque un événement de replay.

        Args:
            name (str): Nom de l'événement
            event_type (str): Type d'événement ('point', 'set', 'match', etc.)

        Returns:
            tuple: (success, events_list)
        """
        try:
            # Vérifier la connexion à vMix
            if not self.vmix.check_connection():
                logger.error("Impossible de se connecter à vMix")
                return False, None

            # Générer un index d'événement unique pour vMix
            event_index = len(self.events)

            # Marquer le début de l'événement dans vMix avec ReplayMarkIn
            # On utilise la méthode send_command correctement avec les paramètres séparés
            result = self.vmix.send_command("ReplayMarkIn", Value=event_index)

            if not result:
                logger.error("Échec du marquage du début de l'événement (ReplayMarkIn)")
                return False, None

            # Récupérer la durée configurée pour l'événement
            replay_duration = self.config.get('duration', 8)  # Durée par défaut 8 secondes

            # Nettoyer le nom de l'événement
            event_name = name
            if isinstance(name, dict) or not isinstance(name, str):
                # Si c'est un objet ou non une chaîne, utiliser un nom par défaut
                event_name = f"Événement {len(self.events) + 1}"

            # Marquer la fin de l'événement dans vMix avec ReplayMarkOut
            # On utilise la méthode send_command correctement avec les paramètres séparés
            result = self.vmix.send_command("ReplayMarkOut", Value=event_index)

            if not result:
                logger.warning("Échec du marquage de la fin de l'événement (ReplayMarkOut)")
                # On continue car ReplayMarkIn a fonctionné et c'est le plus important

            # Définir le nom de l'événement dans vMix
            result = self.vmix.send_command("ReplayChangeEventName", Value=event_index, Name=event_name)

            # Créer et enregistrer l'événement
            event = {
                'name': event_name,
                'type': event_type,
                'timestamp': datetime.now().isoformat(),
                'index': event_index,
                'duration': replay_duration
            }
            self.events.append(event)
            self.save_events()

            logger.info(f"Événement marqué: {event['name']} (durée: {replay_duration}s, index: {event_index})")
            return True, self.events
        except Exception as e:
            logger.error(f"Erreur lors du marquage de l'événement: {str(e)}")
            return False, None

    def play_event(self, event_index, speed=100):
        """
        Lit un événement de replay spécifique.

        Selon la documentation vMix, la commande ReplayPlayEvent prend:
        - Value: l'index de l'événement (0-based)
        - Speed: la vitesse de lecture (25, 50, 75, 100)

        Args:
            event_index (int): Index de l'événement à lire
            speed (int): Vitesse de lecture en pourcentage (25, 50, 75, 100)

        Returns:
            bool: True si la lecture a démarré avec succès, False sinon
        """
        try:
            # Vérifier que l'index est valide
            if event_index < 0 or event_index >= len(self.events):
                logger.error(f"Index d'événement invalide: {event_index}")
                return False

            # Vérifier que la vitesse est valide
            if speed not in [25, 50, 75, 100]:
                logger.error(f"Vitesse de replay invalide: {speed}")
                return False

            # Vérifier la connexion à vMix
            if not self.vmix.check_connection():
                logger.error("Impossible de se connecter à vMix")
                return False

            # D'après la documentation vMix, l'index dans le buffer vMix peut être différent
            # de notre index local. Nous utilisons donc directement l'événement le plus récent.
            # Pour vMix, les événements sont numérotés de 0 (le plus récent) à N
            try:
                # D'abord, on essaie de lire avec notre index, au cas où vMix utilise le même ordre
                command = "ReplayPlayEvent"
                params = {
                    "Value": event_index,
                    "Speed": speed
                }

                logger.info(f"Tentative de lecture de l'événement {event_index} à {speed}%")
                result = self.vmix.send_command(command, **params)

                if result:
                    self.is_playing = True
                    logger.info(f"Lecture de l'événement {event_index} à {speed}% réussie")
                    return True

                # Si ça échoue, on peut essayer de convertir notre index
                # en index vMix (plus récent = plus petit index)
                vmix_index = len(self.events) - 1 - event_index
                if vmix_index >= 0:
                    command = "ReplayPlayEvent"
                    params = {
                        "Value": vmix_index,
                        "Speed": speed
                    }

                    logger.info(f"Tentative alternative: lecture de l'événement vMix {vmix_index} à {speed}%")
                    result = self.vmix.send_command(command, **params)

                    if result:
                        self.is_playing = True
                        logger.info(f"Lecture de l'événement {vmix_index} (converti) à {speed}% réussie")
                        return True

                # Si les deux approches échouent, on tente de lire le dernier événement
                command = "ReplayPlay"
                params = {"Speed": speed}
                logger.info(f"Tentative de lecture du dernier événement à {speed}%")
                result = self.vmix.send_command(command, **params)

                if result:
                    self.is_playing = True
                    logger.info(f"Lecture du dernier événement à {speed}% réussie (fallback)")
                    return True

                logger.error(f"Échec de toutes les tentatives de lecture de l'événement")
                return False

            except Exception as e:
                logger.error(f"Erreur lors de la lecture de l'événement: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"Erreur lors de la lecture de l'événement: {str(e)}")
            return False

    def delete_event(self, event_index):
        """
        Supprime un événement de replay de la liste locale.

        Note importante: L'API vMix ne fournit pas de méthode pour supprimer
        un événement spécifique de la liste des événements de replay.
        Cette méthode supprime uniquement l'événement de notre liste locale.

        Pour garder les listes synchronisées, nous pourrions:
        1. Recréer tous les événements restants dans vMix (pas idéal)
        2. Avertir l'utilisateur de cette limitation

        Args:
            event_index (int): Index de l'événement à supprimer

        Returns:
            tuple: (bool, list, str) - (Succès, Liste des événements mise à jour, Message d'avertissement)
        """
        try:
            # Vérifier que l'index est valide
            if event_index < 0 or event_index >= len(self.events):
                logger.error(f"Index d'événement invalide: {event_index}")
                return False, self.events, "Index d'événement invalide"

            # Supprimer l'événement de la liste locale
            deleted_event = self.events.pop(event_index)

            # Mettre à jour les indices des événements restants
            for i, event in enumerate(self.events):
                event['index'] = i

            # Sauvegarder la liste mise à jour
            self.save_events()

            logger.info(f"Événement supprimé de la liste locale: {deleted_event.get('name', f'Événement {event_index + 1}')}")

            # Message d'avertissement pour l'utilisateur
            warning_message = ("Attention: L'événement a été supprimé de la liste locale, "
                              "mais reste présent dans vMix car l'API vMix ne permet pas "
                              "de supprimer des événements spécifiques.")

            logger.warning(warning_message)

            return True, self.events, warning_message
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'événement: {str(e)}")
            return False, self.events, f"Erreur: {str(e)}"

    def get_status(self):
        """
        Récupère l'état actuel du système de replay.

        Returns:
            dict: État actuel du système de replay
        """
        return {
            'isRecording': self.is_recording,
            'isPlaying': self.is_playing,
            'recordingTime': (datetime.now() - self.recording_start_time).total_seconds() if self.is_recording and self.recording_start_time else 0,
            'events': len(self.events)
        }
