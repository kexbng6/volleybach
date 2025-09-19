#fonctionnalités à implémenter :
# -contrôle du streaming, -gestion des configurations de streaming, -enregistrement
# -surveillance de l'état du streaming

import os
import json
import time
import logging
from v3_0.app.core.vmix_manager import VMixManager

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('stream_manager')

class StreamManager:
    """
    Gestionnaire pour les fonctionnalités de streaming dans vMix
    """

    def __init__(self, vmix_manager=None, data_dir=None):
        """
        Initialise le gestionnaire de streaming

        Args:
            vmix_manager: Instance de VMixManager à utiliser
            data_dir: Répertoire où stocker les configurations de streaming
        """
        # Si aucun répertoire n'est spécifié, utiliser le répertoire courant
        if data_dir is None:
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        else:
            self.data_dir = data_dir

        # Créer le répertoire s'il n'existe pas
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Fichier JSON pour stocker les configurations de streaming
        self.config_file = os.path.join(self.data_dir, "stream_config.json")

        # Utiliser l'instance vmix_manager fournie ou en créer une nouvelle
        self.vmix = vmix_manager if vmix_manager else VMixManager()

        # Initialiser la configuration par défaut si elle n'existe pas
        if not os.path.exists(self.config_file):
            self._create_default_config()
        
        # État actuel du streaming
        self.streaming_state = {
            'is_streaming': False,
            'is_recording': False,
            'stream_start_time': None,
            'recording_start_time': None
        }
        
        # Charger la configuration
        self.config = self.load_config()
        
        # Vérifier l'état initial du streaming
        self._update_streaming_state()

    def _create_default_config(self):
        """Crée une configuration de streaming par défaut"""
        default_config = {
            'title': '',
            'service': 'custom',
            'quality': '1080p30',
            'rtmpUrl': '',
            'streamKey': '',
            'description': '',
            'autoStartRecording': False,
            'autoStartStreaming': False,
            'thumbnailUrl': None
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
    
    def load_config(self):
        """Charge la configuration du streaming depuis le fichier"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
            return self._create_default_config()
    
    def save_config(self, config):
        """Sauvegarde la configuration du streaming"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.config = config
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration: {str(e)}")
            return False
    
    def _update_streaming_state(self):
        """Met à jour l'état actuel du streaming depuis vMix"""
        if self.vmix.check_connection():
            streaming_status = self.vmix.get_streaming_status()
            recording_status = self.vmix.get_recording_status()
            
            # Mettre à jour l'état du streaming
            if streaming_status and not self.streaming_state['is_streaming']:
                self.streaming_state['is_streaming'] = True
                self.streaming_state['stream_start_time'] = time.time()
            elif not streaming_status:
                self.streaming_state['is_streaming'] = False
                self.streaming_state['stream_start_time'] = None
            
            # Mettre à jour l'état de l'enregistrement
            if recording_status and not self.streaming_state['is_recording']:
                self.streaming_state['is_recording'] = True
                self.streaming_state['recording_start_time'] = time.time()
            elif not recording_status:
                self.streaming_state['is_recording'] = False
                self.streaming_state['recording_start_time'] = None
    
    def get_streaming_state(self):
        """
        Récupère l'état actuel du streaming
        
        Returns:
            dict: État actuel du streaming avec les durées
        """
        self._update_streaming_state()
        
        current_time = time.time()
        state = self.streaming_state.copy()
        
        # Calculer les durées
        if state['stream_start_time']:
            state['streaming_duration'] = int(current_time - state['stream_start_time'])
        else:
            state['streaming_duration'] = 0
            
        if state['recording_start_time']:
            state['recording_duration'] = int(current_time - state['recording_start_time'])
        else:
            state['recording_duration'] = 0
            
        return state
    
    def start_streaming(self):
        """
        Démarre le streaming dans vMix
        
        Returns:
            bool: True si le streaming a démarré avec succès
        """
        if not self.vmix.check_connection():
            logger.error("Impossible de démarrer le streaming : vMix non connecté")
            return False
            
        success = self.vmix.start_streaming()
        if success:
            self.streaming_state['is_streaming'] = True
            self.streaming_state['stream_start_time'] = time.time()
            logger.info("Streaming démarré avec succès")
        return success
    
    def stop_streaming(self):
        """
        Arrête le streaming dans vMix
        
        Returns:
            bool: True si le streaming a été arrêté avec succès
        """
        if not self.vmix.check_connection():
            logger.error("Impossible d'arrêter le streaming : vMix non connecté")
            return False
            
        success = self.vmix.start_streaming("Stop")  # La méthode accepte "Stop" comme paramètre
        if success:
            self.streaming_state['is_streaming'] = False
            self.streaming_state['stream_start_time'] = None
            logger.info("Streaming arrêté avec succès")
        return success
    
    def start_recording(self):
        """
        Démarre l'enregistrement dans vMix
        
        Returns:
            bool: True si l'enregistrement a démarré avec succès
        """
        if not self.vmix.check_connection():
            logger.error("Impossible de démarrer l'enregistrement : vMix non connecté")
            return False
            
        success = self.vmix.start_recording()
        if success:
            self.streaming_state['is_recording'] = True
            self.streaming_state['recording_start_time'] = time.time()
            logger.info("Enregistrement démarré avec succès")
        return success
    
    def stop_recording(self):
        """
        Arrête l'enregistrement dans vMix
        
        Returns:
            bool: True si l'enregistrement a été arrêté avec succès
        """
        if not self.vmix.check_connection():
            logger.error("Impossible d'arrêter l'enregistrement : vMix non connecté")
            return False
            
        success = self.vmix.stop_recording()
        if success:
            self.streaming_state['is_recording'] = False
            self.streaming_state['recording_start_time'] = None
            logger.info("Enregistrement arrêté avec succès")
        return success
    
    def toggle_thumbnail(self, show=True, input_name="Thumbnail", overlay_number=1):
        """
        Active ou désactive la miniature du match
        
        Args:
            show (bool): True pour afficher, False pour masquer
            input_name (str): Nom de l'input de la miniature dans vMix
            overlay_number (int): Numéro de l'overlay à utiliser
        
        Returns:
            bool: True si l'opération a réussi
        """
        if not self.vmix.check_connection():
            logger.error("Impossible de gérer la miniature : vMix non connecté")
            return False
        
        success = self.vmix.set_overlay(input_name, overlay_number, show)
        if success:
            logger.info(f"Miniature {'activée' if show else 'désactivée'} avec succès")
        return success
