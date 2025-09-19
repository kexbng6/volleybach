#fonctionnalités à implémenter :
# -gestion des overlays vMix (titres), -contrôle d'affichage des overlays
# -mise à jour du contenu des overlays (scores, équipes, joueurs, etc.)

import os
import logging
import json
from v3_0.app.core.vmix_manager import Vmix_manager

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('overlay_manager')

class OverlayManager:
    """
    Gestionnaire pour les overlays vMix (titres, scores, équipes, etc.)
    """
    
    def __init__(self, vmix_manager=None, data_dir=None):
        """
        Initialise le gestionnaire d'overlays
        
        Args:
            vmix_manager: Instance de Vmix_manager à utiliser
            data_dir: Répertoire pour les configurations d'overlays
        """
        # Si aucun répertoire n'est spécifié, utiliser le répertoire courant
        if data_dir is None:
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        else:
            self.data_dir = data_dir
            
        # Créer le répertoire s'il n'existe pas
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Fichier JSON pour stocker les configurations d'overlays
        self.overlay_config_file = os.path.join(self.data_dir, "overlay_config.json")
        
        # Utiliser l'instance vmix_manager fournie ou en créer une nouvelle
        self.vmix = vmix_manager if vmix_manager else Vmix_manager()
        
        # Dictionnaire pour stocker les références aux overlays détectés
        self.overlay_inputs = {}
        
        # Charger la configuration des overlays
        self.config = self.load_config()
        
        # Détecter les overlays disponibles dans vMix
        self.detect_overlays()
        
    def load_config(self):
        """
        Charge la configuration des overlays depuis le fichier JSON
        
        Returns:
            dict: Configuration des overlays
        """
        try:
            if os.path.exists(self.overlay_config_file):
                with open(self.overlay_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Configuration par défaut si le fichier n'existe pas
                default_config = {
                    "overlays": {
                        "score": {
                            "name": "Score",
                            "overlay_number": 1,
                            "fields": {
                                "HomeScore": "0",
                                "AwayScore": "0",
                                "HomeName": "Équipe A",
                                "AwayName": "Équipe B",
                                "SetScores": "0-0",
                                "Period": "Set 1"
                            }
                        },
                        "team_roster": {
                            "name": "Roster d'équipe",
                            "overlay_number": 2,
                            "fields": {
                                "TeamName": "Nom de l'équipe",
                                "Player1Name": "",
                                "Player1Number": "",
                                "Player1Position": ""
                                # ... autres joueurs
                            }
                        },
                        "player_detail": {
                            "name": "Détail joueur",
                            "overlay_number": 3,
                            "fields": {
                                "PlayerName": "",
                                "PlayerNumber": "",
                                "PlayerPosition": "",
                                "PlayerHeight": "",
                                "PlayerAge": "",
                                "TeamName": ""
                            }
                        },
                        "sponsor": {
                            "name": "Sponsor",
                            "overlay_number": 4,
                            "fields": {
                                "SponsorName": "",
                                "SponsorLogo": ""
                            }
                        }
                    }
                }
                # Sauvegarder la configuration par défaut
                self.save_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration des overlays: {e}")
            return {"overlays": {}}
            
    def save_config(self, config=None):
        """
        Sauvegarde la configuration des overlays dans le fichier JSON
        
        Args:
            config (dict, optional): Configuration à sauvegarder. Si None, utilise self.config.
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            config_to_save = config if config is not None else self.config
            with open(self.overlay_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=4)
            logger.info(f"Configuration des overlays sauvegardée dans {self.overlay_config_file}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration des overlays: {e}")
            return False
            
    def detect_overlays(self):
        """
        Détecte les overlays disponibles dans vMix et met à jour self.overlay_inputs
        
        Returns:
            dict: Dictionnaire des overlays détectés
        """
        try:
            # Vider le dictionnaire existant
            self.overlay_inputs = {}
            
            # Récupérer tous les inputs
            all_inputs = self.vmix.get_inputs()
            
            # Catégoriser les overlays en fonction de leur nom
            # Ces motifs de recherche sont basés sur les noms typiques dans vMix
            overlay_patterns = {
                "score": ["score", "scoreboard", "points", "résultat"],
                "team_roster": ["roster", "équipe", "team", "lineup", "players"],
                "player_detail": ["player", "joueur", "détail", "detail", "stats"],
                "timeout": ["timeout", "temps mort"],
                "sponsor": ["sponsor", "partenaire", "pub", "ad"],
                "logo": ["logo", "emblem"],
                "lower_third": ["lower third", "tiers inférieur", "nom", "name tag"],
                "match_info": ["match", "game", "info", "information"]
            }
            
            # Rechercher les overlays correspondant aux motifs
            for input_item in all_inputs:
                input_name = input_item.get('name', '').lower()
                input_id = input_item.get('id')
                input_type = input_item.get('type', '').lower()
                
                # Ne considérer que les inputs de type titre/GT
                if 'title' in input_type or 'gt' in input_type:
                    # Chercher à quelle catégorie correspond cet overlay
                    for overlay_type, patterns in overlay_patterns.items():
                        for pattern in patterns:
                            if pattern in input_name:
                                self.overlay_inputs[overlay_type] = input_id
                                logger.info(f"Overlay de type '{overlay_type}' détecté: {input_name} (ID: {input_id})")
                                break
            
            # Mettre à jour la configuration avec les overlays détectés
            for overlay_type, input_id in self.overlay_inputs.items():
                if overlay_type in self.config.get("overlays", {}):
                    # Mettre à jour l'ID de l'input dans la configuration
                    self.config["overlays"][overlay_type]["input_id"] = input_id
            
            # Sauvegarder la configuration mise à jour
            self.save_config()
            
            return self.overlay_inputs
        except Exception as e:
            logger.error(f"Erreur lors de la détection des overlays: {e}")
            return {}
            
    def show_overlay(self, overlay_type, enable=True):
        """
        Affiche ou masque un overlay spécifique
        
        Args:
            overlay_type (str): Type d'overlay ('score', 'team_roster', etc.)
            enable (bool): True pour afficher, False pour masquer
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Vérifier si l'overlay est configuré
            if overlay_type not in self.config.get("overlays", {}):
                logger.error(f"Overlay de type '{overlay_type}' non configuré")
                return False
                
            # Récupérer les informations de l'overlay
            overlay_config = self.config["overlays"][overlay_type]
            overlay_number = overlay_config.get("overlay_number", 0)
            
            # Vérifier si l'overlay a un ID
            if "input_id" not in overlay_config and overlay_type not in self.overlay_inputs:
                logger.error(f"Overlay de type '{overlay_type}' non détecté dans vMix")
                return False
                
            # Récupérer l'ID de l'input
            input_id = overlay_config.get("input_id", self.overlay_inputs.get(overlay_type))
            
            # Activer ou désactiver l'overlay
            if enable:
                # S'assurer que l'overlay est configuré pour l'entrée correcte
                self.vmix.send_command(f"SetOverlayInput{overlay_number}", Value=input_id)
                # Activer l'overlay
                result = self.vmix.send_command(f"OverlayInput{overlay_number}In")
                action = "affiché"
            else:
                # Désactiver l'overlay
                result = self.vmix.send_command(f"OverlayInput{overlay_number}Out")
                action = "masqué"
                
            if result:
                logger.info(f"Overlay '{overlay_type}' {action} avec succès")
            else:
                logger.error(f"Échec de l'action sur l'overlay '{overlay_type}'")
                
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage/masquage de l'overlay: {e}")
            return False
            
    def toggle_overlay(self, overlay_type):
        """
        Bascule l'état d'un overlay (affiche s'il est masqué, masque s'il est affiché)
        
        Args:
            overlay_type (str): Type d'overlay ('score', 'team_roster', etc.)
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Vérifier si l'overlay est configuré
            if overlay_type not in self.config.get("overlays", {}):
                logger.error(f"Overlay de type '{overlay_type}' non configuré")
                return False
                
            # Récupérer les informations de l'overlay
            overlay_config = self.config["overlays"][overlay_type]
            overlay_number = overlay_config.get("overlay_number", 0)
            
            # Basculer l'état de l'overlay
            result = self.vmix.send_command(f"OverlayInput{overlay_number}")
            
            if result:
                logger.info(f"État de l'overlay '{overlay_type}' basculé avec succès")
            else:
                logger.error(f"Échec du basculement de l'état de l'overlay '{overlay_type}'")
                
            return result
        except Exception as e:
            logger.error(f"Erreur lors du basculement de l'état de l'overlay: {e}")
            return False
            
    def update_overlay_fields(self, overlay_type, fields):
        """
        Met à jour les champs d'un overlay
        
        Args:
            overlay_type (str): Type d'overlay ('score', 'team_roster', etc.)
            fields (dict): Dictionnaire des champs à mettre à jour {nom_champ: valeur}
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Vérifier si l'overlay est configuré
            if overlay_type not in self.config.get("overlays", {}):
                logger.error(f"Overlay de type '{overlay_type}' non configuré")
                return False
                
            # Récupérer les informations de l'overlay
            overlay_config = self.config["overlays"][overlay_type]
            
            # Vérifier si l'overlay a un ID
            if "input_id" not in overlay_config and overlay_type not in self.overlay_inputs:
                logger.error(f"Overlay de type '{overlay_type}' non détecté dans vMix")
                return False
                
            # Récupérer l'ID de l'input
            input_id = overlay_config.get("input_id", self.overlay_inputs.get(overlay_type))
            
            # Mettre à jour les champs dans vMix
            result = self.vmix.update_title_multiple(input_id, fields)
            
            if result:
                # Mettre à jour les champs dans la configuration
                if "fields" not in overlay_config:
                    overlay_config["fields"] = {}
                for field_name, value in fields.items():
                    overlay_config["fields"][field_name] = value
                    
                # Sauvegarder la configuration mise à jour
                self.save_config()
                
                logger.info(f"Champs de l'overlay '{overlay_type}' mis à jour avec succès")
            else:
                logger.error(f"Échec de la mise à jour des champs de l'overlay '{overlay_type}'")
                
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des champs de l'overlay: {e}")
            return False
            
    def update_score(self, home_score, away_score, home_name=None, away_name=None, set_scores=None, period=None):
        """
        Met à jour l'overlay de score
        
        Args:
            home_score (str): Score de l'équipe à domicile
            away_score (str): Score de l'équipe visiteuse
            home_name (str, optional): Nom de l'équipe à domicile
            away_name (str, optional): Nom de l'équipe visiteuse
            set_scores (str, optional): Score des sets (ex: "2-1")
            period (str, optional): Période actuelle (ex: "Set 3")
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Préparer les champs à mettre à jour
            fields = {
                "HomeScore": str(home_score),
                "AwayScore": str(away_score)
            }
            
            # Ajouter les champs optionnels s'ils sont fournis
            if home_name is not None:
                fields["HomeName"] = home_name
            if away_name is not None:
                fields["AwayName"] = away_name
            if set_scores is not None:
                fields["SetScores"] = set_scores
            if period is not None:
                fields["Period"] = period
                
            # Mettre à jour l'overlay de score
            return self.update_overlay_fields("score", fields)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du score: {e}")
            return False
            
    def update_team_roster(self, team_name, players):
        """
        Met à jour l'overlay de roster d'équipe
        
        Args:
            team_name (str): Nom de l'équipe
            players (list): Liste des joueurs [{"name": "...", "number": "...", "position": "..."}, ...]
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Préparer les champs à mettre à jour
            fields = {
                "TeamName": team_name
            }
            
            # Ajouter les joueurs (jusqu'à 14 joueurs maximum)
            for i, player in enumerate(players[:14], 1):
                fields[f"Player{i}Name"] = player.get("name", "")
                fields[f"Player{i}Number"] = player.get("number", "")
                fields[f"Player{i}Position"] = player.get("position", "")
                
            # Mettre à jour l'overlay de roster
            return self.update_overlay_fields("team_roster", fields)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du roster d'équipe: {e}")
            return False
            
    def update_player_detail(self, player, team_name=None):
        """
        Met à jour l'overlay de détail de joueur
        
        Args:
            player (dict): Données du joueur {"name": "...", "number": "...", "position": "...", ...}
            team_name (str, optional): Nom de l'équipe
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Préparer les champs à mettre à jour
            fields = {
                "PlayerName": player.get("name", ""),
                "PlayerNumber": player.get("number", ""),
                "PlayerPosition": player.get("position", ""),
                "PlayerHeight": player.get("height", ""),
                "PlayerAge": player.get("age", "")
            }
            
            # Ajouter le nom de l'équipe s'il est fourni
            if team_name is not None:
                fields["TeamName"] = team_name
                
            # Mettre à jour l'overlay de détail de joueur
            return self.update_overlay_fields("player_detail", fields)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du détail de joueur: {e}")
            return False
            
    def update_sponsor(self, sponsor_name, logo_path=None):
        """
        Met à jour l'overlay de sponsor
        
        Args:
            sponsor_name (str): Nom du sponsor
            logo_path (str, optional): Chemin vers le logo du sponsor
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Préparer les champs à mettre à jour
            fields = {
                "SponsorName": sponsor_name
            }
            
            # Mettre à jour l'overlay de sponsor
            result = self.update_overlay_fields("sponsor", fields)
            
            # Mettre à jour le logo si un chemin est fourni
            if logo_path is not None and result:
                # Vérifier si l'overlay a un ID
                if "sponsor" in self.overlay_inputs:
                    input_id = self.overlay_inputs["sponsor"]
                    result = self.vmix.set_image(input_id, "SponsorLogo", logo_path)
                    
                    if result:
                        # Mettre à jour le chemin du logo dans la configuration
                        self.config["overlays"]["sponsor"]["fields"]["SponsorLogo"] = logo_path
                        self.save_config()
                        
                        logger.info(f"Logo du sponsor mis à jour avec succès: {logo_path}")
                    else:
                        logger.error(f"Échec de la mise à jour du logo du sponsor")
                else:
                    logger.error("Overlay de sponsor non détecté dans vMix")
                    result = False
                    
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du sponsor: {e}")
            return False
            
    def show_timeout(self, team_name, duration=30):
        """
        Affiche un overlay de timeout pour une équipe spécifique
        
        Args:
            team_name (str): Nom de l'équipe
            duration (int, optional): Durée du timeout en secondes
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Vérifier si l'overlay de timeout est configuré
            if "timeout" not in self.config.get("overlays", {}) and "timeout" not in self.overlay_inputs:
                logger.error("Overlay de timeout non configuré/détecté")
                return False
                
            # Mettre à jour le texte du timeout
            fields = {
                "TeamName": team_name,
                "TimeoutText": f"TIMEOUT {team_name}"
            }
            
            # Mettre à jour l'overlay de timeout
            result = self.update_overlay_fields("timeout", fields)
            
            # Afficher l'overlay si la mise à jour a réussi
            if result:
                result = self.show_overlay("timeout", True)
                
                # Programmation de la disparition après la durée spécifiée
                # Note: Cette partie est conceptuelle - dans une implémentation réelle,
                # vous utiliseriez un timer ou une tâche planifiée
                import threading
                def hide_timeout():
                    import time
                    time.sleep(duration)
                    self.show_overlay("timeout", False)
                    
                # Démarrer un thread pour masquer l'overlay après la durée spécifiée
                threading.Thread(target=hide_timeout, daemon=True).start()
                
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage du timeout: {e}")
            return False
            
    def create_overlay_preset(self, name, overlay_types):
        """
        Crée un preset pour activer/désactiver plusieurs overlays en une seule fois
        
        Args:
            name (str): Nom du preset
            overlay_types (list): Liste des types d'overlays à inclure dans le preset
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Vérifier si les overlays existent
            for overlay_type in overlay_types:
                if overlay_type not in self.config.get("overlays", {}):
                    logger.error(f"Overlay de type '{overlay_type}' non configuré")
                    return False
                    
            # Créer le preset
            if "presets" not in self.config:
                self.config["presets"] = {}
                
            self.config["presets"][name] = overlay_types
            
            # Sauvegarder la configuration
            self.save_config()
            
            logger.info(f"Preset '{name}' créé avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la création du preset: {e}")
            return False
            
    def apply_overlay_preset(self, name, enable=True):
        """
        Applique un preset pour activer/désactiver plusieurs overlays en une seule fois
        
        Args:
            name (str): Nom du preset
            enable (bool): True pour afficher les overlays, False pour les masquer
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Vérifier si le preset existe
            if name not in self.config.get("presets", {}):
                logger.error(f"Preset '{name}' non configuré")
                return False
                
            # Récupérer les types d'overlays du preset
            overlay_types = self.config["presets"][name]
            
            # Appliquer l'action sur chaque overlay
            success = True
            for overlay_type in overlay_types:
                if not self.show_overlay(overlay_type, enable):
                    success = False
                    
            if success:
                action = "affichés" if enable else "masqués"
                logger.info(f"Preset '{name}' appliqué avec succès, overlays {action}")
            else:
                logger.error(f"Échec de l'application du preset '{name}'")
                
            return success
        except Exception as e:
            logger.error(f"Erreur lors de l'application du preset: {e}")
            return False
