#fonctionnalités à implémenter :
# -gestion des inputs vMix, -ajout/suppression d'inputs, -transitions entre inputs
# -contrôle des propriétés des inputs (audio, couleur, etc.)

import os
import logging
from v3_0.app.core.vmix_manager import Vmix_manager

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('input_manager')

class InputManager:
    """
    Gestionnaire pour les inputs vMix (sources vidéo, audio, titres, etc.)
    """
    
    def __init__(self, vmix_manager=None):
        """
        Initialise le gestionnaire d'inputs
        
        Args:
            vmix_manager: Instance de Vmix_manager à utiliser
        """
        # Utiliser l'instance vmix_manager fournie ou en créer une nouvelle
        self.vmix = vmix_manager if vmix_manager else Vmix_manager()
        
        # Dictionnaire pour stocker les inputs par catégorie
        self.categorized_inputs = {
            'camera': [],      # Entrées de type caméra
            'video': [],       # Fichiers vidéo
            'audio': [],       # Sources audio
            'title': [],       # Titres et overlays
            'image': [],       # Images statiques
            'replay': [],      # Entrées de replay
            'stream': [],      # Flux de streaming (RTMP, SRT, etc.)
            'other': []        # Autres types d'entrées
        }
        
        # Rafraîchir la liste des inputs au démarrage
        self.refresh_inputs()
        
    def refresh_inputs(self):
        """
        Rafraîchit la liste des inputs depuis vMix et les catégorise
        
        Returns:
            dict: Dictionnaire des inputs catégorisés
        """
        try:
            # Vider les listes existantes
            for category in self.categorized_inputs:
                self.categorized_inputs[category] = []
                
            # Récupérer tous les inputs
            all_inputs = self.vmix.get_inputs()
            
            # Catégoriser chaque input
            for input_item in all_inputs:
                input_type = input_item.get('type', '').lower()
                
                # Déterminer la catégorie en fonction du type
                if 'camera' in input_type or 'cam' in input_type:
                    self.categorized_inputs['camera'].append(input_item)
                elif 'video' in input_type or 'movie' in input_type:
                    self.categorized_inputs['video'].append(input_item)
                elif 'audio' in input_type or 'sound' in input_type:
                    self.categorized_inputs['audio'].append(input_item)
                elif 'title' in input_type or 'gt' in input_type:
                    self.categorized_inputs['title'].append(input_item)
                elif 'image' in input_type or 'photo' in input_type or 'pic' in input_type:
                    self.categorized_inputs['image'].append(input_item)
                elif 'replay' in input_type:
                    self.categorized_inputs['replay'].append(input_item)
                elif 'stream' in input_type or 'rtmp' in input_type or 'srt' in input_type:
                    self.categorized_inputs['stream'].append(input_item)
                else:
                    self.categorized_inputs['other'].append(input_item)
                    
            # Loguer le nombre d'inputs trouvés par catégorie
            for category, inputs in self.categorized_inputs.items():
                if inputs:
                    logger.info(f"Catégorie '{category}': {len(inputs)} entrées trouvées")
                    
            return self.categorized_inputs
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement des inputs: {e}")
            return self.categorized_inputs
            
    def get_inputs_by_category(self, category):
        """
        Récupère les inputs d'une catégorie spécifique
        
        Args:
            category (str): Nom de la catégorie ('camera', 'video', etc.)
            
        Returns:
            list: Liste des inputs de cette catégorie
        """
        if category in self.categorized_inputs:
            return self.categorized_inputs[category]
        else:
            logger.warning(f"Catégorie '{category}' non reconnue")
            return []
            
    def get_input_by_id(self, input_id):
        """
        Récupère un input par son ID
        
        Args:
            input_id (str): ID de l'input
            
        Returns:
            dict: Données de l'input ou None si non trouvé
        """
        for category, inputs in self.categorized_inputs.items():
            for input_item in inputs:
                if input_item.get('id') == str(input_id):
                    return input_item
        return None
        
    def get_input_by_name(self, name, partial_match=True):
        """
        Récupère un input par son nom
        
        Args:
            name (str): Nom de l'input
            partial_match (bool): Si True, recherche partielle dans le nom
            
        Returns:
            dict: Données de l'input ou None si non trouvé
        """
        for category, inputs in self.categorized_inputs.items():
            for input_item in inputs:
                input_name = input_item.get('name', '').lower()
                search_name = name.lower()
                
                if (partial_match and search_name in input_name) or (not partial_match and search_name == input_name):
                    return input_item
        return None
        
    def switch_input(self, input_id):
        """
        Change l'entrée active dans vMix (coupe direct)
        
        Args:
            input_id (str): ID de l'input à activer
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            result = self.vmix.send_command("CutDirect", Input=input_id)
            if result:
                logger.info(f"Changement réussi vers l'input {input_id}")
            else:
                logger.error(f"Échec du changement vers l'input {input_id}")
            return result
        except Exception as e:
            logger.error(f"Erreur lors du changement d'input: {e}")
            return False
            
    def transition_to_input(self, input_id, transition_type="Fade", duration=500):
        """
        Effectue une transition vers un input spécifié
        
        Args:
            input_id (str): ID de l'input à activer
            transition_type (str): Type de transition ('Fade', 'Wipe', 'Slide', etc.)
            duration (int): Durée de la transition en millisecondes
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            result = self.vmix.send_command(f"{transition_type}", Input=input_id, Duration=duration)
            if result:
                logger.info(f"Transition {transition_type} réussie vers l'input {input_id} en {duration}ms")
            else:
                logger.error(f"Échec de la transition vers l'input {input_id}")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la transition: {e}")
            return False
            
    def add_input(self, input_type, path_or_url, title=None):
        """
        Ajoute un nouvel input à vMix
        
        Args:
            input_type (str): Type d'input ('Video', 'Camera', 'Image', etc.)
            path_or_url (str): Chemin du fichier ou URL
            title (str, optional): Nom à donner à l'input
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Si aucun titre n'est spécifié, utiliser un titre générique
            if not title:
                # Extraire un nom de fichier du chemin si possible
                if os.path.exists(path_or_url):
                    title = os.path.basename(path_or_url)
                else:
                    title = f"Nouvel input {input_type}"
                    
            result = self.vmix.send_command("AddInput", Type=input_type, Value=path_or_url, Title=title)
            if result:
                logger.info(f"Ajout réussi d'un input {input_type}: {title}")
                # Rafraîchir la liste des inputs
                self.refresh_inputs()
            else:
                logger.error(f"Échec de l'ajout d'un input {input_type}")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout d'un input: {e}")
            return False
            
    def remove_input(self, input_id):
        """
        Supprime un input de vMix
        
        Args:
            input_id (str): ID de l'input à supprimer
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            result = self.vmix.send_command("RemoveInput", Input=input_id)
            if result:
                logger.info(f"Suppression réussie de l'input {input_id}")
                # Rafraîchir la liste des inputs
                self.refresh_inputs()
            else:
                logger.error(f"Échec de la suppression de l'input {input_id}")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la suppression d'un input: {e}")
            return False
            
    def toggle_audio(self, input_id, mute=None):
        """
        Active ou désactive l'audio d'un input
        
        Args:
            input_id (str): ID de l'input
            mute (bool, optional): Si True, coupe l'audio. Si False, active l'audio.
                                   Si None, inverse l'état actuel.
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            if mute is None:
                # Toggle (inverser l'état actuel)
                result = self.vmix.send_command("AudioToggle", Input=input_id)
                action = "basculé"
            elif mute:
                # Couper l'audio
                result = self.vmix.send_command("AudioOff", Input=input_id)
                action = "coupé"
            else:
                # Activer l'audio
                result = self.vmix.send_command("AudioOn", Input=input_id)
                action = "activé"
                
            if result:
                logger.info(f"Audio {action} pour l'input {input_id}")
            else:
                logger.error(f"Échec de l'action audio pour l'input {input_id}")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'action audio: {e}")
            return False
            
    def set_audio_volume(self, input_id, volume):
        """
        Définit le volume audio d'un input
        
        Args:
            input_id (str): ID de l'input
            volume (int): Niveau de volume (0-100)
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # S'assurer que le volume est dans la plage valide
            volume = max(0, min(100, volume))
            
            result = self.vmix.send_command("SetVolume", Input=input_id, Value=volume)
            if result:
                logger.info(f"Volume défini à {volume}% pour l'input {input_id}")
            else:
                logger.error(f"Échec de la définition du volume pour l'input {input_id}")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la définition du volume: {e}")
            return False
            
    def set_input_position(self, input_id, x=0, y=0, width=None, height=None):
        """
        Définit la position et la taille d'un input
        
        Args:
            input_id (str): ID de l'input
            x (int): Position X
            y (int): Position Y
            width (int, optional): Largeur
            height (int, optional): Hauteur
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Définir la position
            position_result = self.vmix.send_command("SetPosition", Input=input_id, X=x, Y=y)
            
            # Définir la taille si spécifiée
            size_result = True
            if width is not None and height is not None:
                size_result = self.vmix.send_command("SetSize", Input=input_id, Width=width, Height=height)
                
            result = position_result and size_result
            if result:
                logger.info(f"Position/taille mise à jour pour l'input {input_id}")
            else:
                logger.error(f"Échec de la mise à jour de la position/taille pour l'input {input_id}")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la position/taille: {e}")
            return False
            
    def get_active_input(self):
        """
        Récupère l'input actuellement actif dans vMix
        
        Returns:
            dict: Données de l'input actif ou None si non trouvé
        """
        try:
            active_id = self.vmix.get_active_input()
            if active_id:
                return self.get_input_by_id(active_id)
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'input actif: {e}")
            return None
            
    def list_cameras(self):
        """
        Liste toutes les caméras disponibles
        
        Returns:
            list: Liste des inputs de type caméra
        """
        return self.get_inputs_by_category('camera')
        
    def list_videos(self):
        """
        Liste tous les fichiers vidéo disponibles
        
        Returns:
            list: Liste des inputs de type vidéo
        """
        return self.get_inputs_by_category('video')
        
    def list_titles(self):
        """
        Liste tous les titres disponibles
        
        Returns:
            list: Liste des inputs de type titre
        """
        return self.get_inputs_by_category('title')
        
    def list_all_inputs(self):
        """
        Liste tous les inputs disponibles, toutes catégories confondues
        
        Returns:
            list: Liste de tous les inputs
        """
        all_inputs = []
        for category, inputs in self.categorized_inputs.items():
            all_inputs.extend(inputs)
        return all_inputs
        
    def set_overlay(self, overlay_number, input_id, enable=True):
        """
        Configure un overlay dans vMix
        
        Args:
            overlay_number (int): Numéro de l'overlay (1-4)
            input_id (str): ID de l'input à utiliser comme overlay
            enable (bool): Si True, active l'overlay, sinon le désactive
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            if enable:
                # Définir l'input à utiliser pour cet overlay
                self.vmix.send_command(f"SetOverlayInput{overlay_number}", Value=input_id)
                # Activer l'overlay
                result = self.vmix.send_command(f"OverlayInput{overlay_number}In")
            else:
                # Désactiver l'overlay
                result = self.vmix.send_command(f"OverlayInput{overlay_number}Out")
                
            if result:
                action = "activé" if enable else "désactivé"
                logger.info(f"Overlay {overlay_number} {action} avec l'input {input_id}")
            else:
                logger.error(f"Échec de la configuration de l'overlay {overlay_number}")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la configuration de l'overlay: {e}")
            return False
