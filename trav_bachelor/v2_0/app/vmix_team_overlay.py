import json
import os
import logging
from .vmix_manager import VmixManager

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('vmix_team_overlay')

class VmixTeamOverlayManager:
    """Gestionnaire pour les overlays d'équipe et de joueurs dans vMix"""

    def __init__(self, vmix_manager):
        """
        Initialise le gestionnaire d'overlays d'équipe

        Args:
            vmix_manager: Instance de VmixManager pour communiquer avec vMix
        """
        self.vmix_manager = vmix_manager
        self.teams_file = os.path.join(os.path.dirname(__file__), "teams.json")
        # Dictionnaire associant les types d'overlay aux numéros d'inputs vMix correspondants
        self.overlay_inputs = {}
        self.detect_overlay_inputs()

    def detect_overlay_inputs(self):
        """Détecte les inputs de titre existants dans vMix qui peuvent servir d'overlays pour les équipes"""
        logger.info("Détection des inputs de titre pour les overlays d'équipe...")

        # Mots-clés pour identifier les inputs de titre pertinents
        keywords = {
            'team_name': ['equipe', 'team', 'nom_equipe', 'team_name'],
            'team_logo': ['logo', 'team_logo', 'equipe_logo'],
            'player_name': ['joueur', 'player', 'player_name', 'nom_joueur'],
            'player_number': ['numero', 'number', 'maillot', 'player_number'],
            'player_position': ['position', 'poste', 'player_position'],
            'player_stats': ['stats', 'statistiques', 'player_stats'],
            'team_roster': ['roster', 'effectif', 'liste', 'joueurs', 'players']
        }

        # Récupérer toutes les entrées
        all_inputs = self.vmix_manager.get_inputs()

        # Chercher les inputs de titre qui correspondent aux mots-clés
        for input_data in all_inputs:
            input_name = input_data.get('name', '').lower()
            input_id = input_data.get('id')
            input_type = input_data.get('type', '')

            # Vérifier si c'est un input de titre (GT)
            if 'title' in input_type.lower() or 'gt' in input_type.lower():
                # Chercher des correspondances avec nos mots-clés
                for overlay_type, kwords in keywords.items():
                    if any(kw in input_name for kw in kwords):
                        self.overlay_inputs[overlay_type] = input_id
                        logger.info(f"Input de titre détecté pour {overlay_type}: {input_name} (ID: {input_id})")

        logger.info(f"Détection terminée. {len(self.overlay_inputs)} inputs d'overlay trouvés.")

    def load_teams_data(self):
        """Charge les données des équipes depuis le fichier JSON"""
        try:
            if os.path.exists(self.teams_file):
                with open(self.teams_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données des équipes: {e}")
            return {}

    def update_team_overlay(self, team_id, overlay_type=None):
        """
        Met à jour les overlays d'une équipe spécifique

        Args:
            team_id: Identifiant de l'équipe
            overlay_type: Type d'overlay à mettre à jour (None pour tous)

        Returns:
            bool: Succès ou échec de la mise à jour
        """
        try:
            teams_data = self.load_teams_data()
            if team_id not in teams_data:
                logger.error(f"Équipe {team_id} non trouvée dans les données")
                return False

            team = teams_data[team_id]
            success = True

            # Mettre à jour le nom de l'équipe
            if overlay_type is None or overlay_type == 'team_name':
                if 'team_name' in self.overlay_inputs:
                    title_input = self.overlay_inputs['team_name']
                    result = self.vmix_manager.set_text(title_input, team['name'])
                    success = success and result
                    logger.info(f"Mise à jour du nom d'équipe: {team['name']}")
                else:
                    logger.warning("Aucun input de titre trouvé pour le nom d'équipe")

            # Mettre à jour le logo de l'équipe (si disponible)
            if overlay_type is None or overlay_type == 'team_logo':
                if 'team_logo' in self.overlay_inputs and 'logo_path' in team:
                    title_input = self.overlay_inputs['team_logo']
                    # Utiliser set_image pour mettre à jour l'image du logo
                    result = self.set_image(title_input, 'TeamLogo', team['logo_path'])
                    success = success and result
                    logger.info(f"Mise à jour du logo d'équipe: {team['logo_path']}")
                else:
                    logger.warning("Aucun input de titre trouvé pour le logo d'équipe ou pas de chemin logo")

            # Mettre à jour la liste des joueurs
            if overlay_type is None or overlay_type == 'team_roster':
                if 'team_roster' in self.overlay_inputs and 'players' in team:
                    title_input = self.overlay_inputs['team_roster']
                    # Formater la liste des joueurs pour l'affichage
                    roster_text = self.format_roster_text(team['players'])
                    result = self.vmix_manager.set_text(title_input, roster_text)
                    success = success and result
                    logger.info(f"Mise à jour de l'effectif de l'équipe: {len(team['players'])} joueurs")
                else:
                    logger.warning("Aucun input de titre trouvé pour l'effectif d'équipe ou pas de joueurs")
            return success

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des overlays d'équipe: {e}")
            return False

    def update_player_overlay(self, team_id, player_index, overlay_type=None):
        """
        Met à jour les overlays d'un joueur spécifique

        Args:
            team_id: Identifiant de l'équipe
            player_index: Index du joueur dans la liste
            overlay_type: Type d'overlay à mettre à jour (None pour tous)

        Returns:
            bool: Succès ou échec de la mise à jour
        """
        try:
            teams_data = self.load_teams_data()
            if team_id not in teams_data or 'players' not in teams_data[team_id]:
                logger.error(f"Équipe {team_id} ou joueurs non trouvés dans les données")
                return False

            players = teams_data[team_id]['players']
            if player_index >= len(players):
                logger.error(f"Index de joueur {player_index} hors limites")
                return False

            player = players[player_index]
            success = True

            # Mettre à jour le nom du joueur
            if overlay_type is None or overlay_type == 'player_name':
                if 'player_name' in self.overlay_inputs:
                    title_input = self.overlay_inputs['player_name']
                    player_name = f"{player.get('prenom', '')} {player.get('nom', '')}".strip()
                    result = self.vmix_manager.set_text(title_input, player_name)
                    success = success and result
                    logger.info(f"Mise à jour du nom du joueur: {player_name}")
                else:
                    logger.warning("Aucun input de titre trouvé pour le nom du joueur")

            # Mettre à jour le numéro du joueur
            if overlay_type is None or overlay_type == 'player_number':
                if 'player_number' in self.overlay_inputs and 'numero' in player:
                    title_input = self.overlay_inputs['player_number']
                    result = self.vmix_manager.set_text(title_input, player['numero'])
                    success = success and result
                    logger.info(f"Mise à jour du numéro du joueur: {player['numero']}")
                else:
                    logger.warning("Aucun input de titre trouvé pour le numéro du joueur ou pas de numéro")

            # Mettre à jour la position du joueur
            if overlay_type is None or overlay_type == 'player_position':
                if 'player_position' in self.overlay_inputs and 'position' in player:
                    title_input = self.overlay_inputs['player_position']
                    result = self.vmix_manager.set_text(title_input, player['position'])
                    success = success and result
                    logger.info(f"Mise à jour de la position du joueur: {player['position']}")
                else:
                    logger.warning("Aucun input de titre trouvé pour la position du joueur ou pas de position")

            # Vous pouvez ajouter d'autres types d'overlay ici...

            return success

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des overlays du joueur: {e}")
            return False

    def format_roster_text(self, players):
        """Formate la liste des joueurs pour l'affichage dans un titre vMix"""
        try:
            roster_lines = []
            for player in players:
                player_name = f"{player.get('prenom', '')} {player.get('nom', '')}".strip()
                player_number = player.get('numero', '')
                player_position = player.get('position', '')

                # Format: #numero - Nom Prenom (Position)
                line = ""
                if player_number:
                    line += f"#{player_number} - "
                line += player_name
                if player_position:
                    line += f" ({player_position})"

                roster_lines.append(line)

            # Joindre toutes les lignes avec des sauts de ligne
            return "\n".join(roster_lines)

        except Exception as e:
            logger.error(f"Erreur lors du formatage de la liste des joueurs: {e}")
            return "Erreur: liste des joueurs indisponible"

    def set_image(self, input_number, image_name, image_path):
        """
        Met à jour une image dans un titre GT

        Args:
            input_number: Numéro de l'input vMix
            image_name: Nom de l'image dans le titre GT (comme défini dans GT Designer)
            image_path: Chemin absolu vers l'image à utiliser

        Returns:
            bool: Succès ou échec de la mise à jour
        """
        try:
            # Convertir le chemin relatif en URL absolue si nécessaire
            if not image_path.startswith(('http://', 'https://')):
                # Construire le chemin absolu si c'est un chemin relatif
                if not os.path.isabs(image_path):
                    # Chemin relatif à l'application
                    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    image_path = os.path.join(app_dir, image_path)

                # Convertir en URL file://
                image_path = f"file://{image_path}"

            logger.info(f"Mise à jour de l'image {image_name} dans l'input {input_number} avec {image_path}")

            # Utiliser SetImageURL pour définir l'URL de l'image
            # Format: SetImageURL Input=1&SelectedName=MyImage&Value=http://...
            result = self.vmix_manager.send_command("SetImageURL",
                                                  Input=input_number,
                                                  SelectedName=image_name,
                                                  Value=image_path)

            return result

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'image: {e}")
            return False
