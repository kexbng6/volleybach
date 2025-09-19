#fonctionnalités à implémenter :
# -structurer les données des équipes, -opérations cRUD ?
# -persistance des équipes

import json
import os
import csv
import uuid
import logging
from werkzeug.utils import secure_filename

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('team_manager')

class TeamManager:
    def __init__(self, vmix_manager=None, data_dir=None):
        """
        Initialise le gestionnaire d'équipes

        Args:
            vmix_manager: Instance de VMixManager à utiliser
            data_dir: Répertoire pour les données persistantes
        """
        # Configuration des chemins
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.data_dir = data_dir or os.path.join(self.base_dir, '..', 'data')
        self.teams_file = os.path.join(self.data_dir, 'teams.json')
        self.logos_dir = os.path.join(self.data_dir, 'team_logos')
        self.vmix_manager = vmix_manager

        # Créer les répertoires s'ils n'existent pas
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.logos_dir, exist_ok=True)

        # Initialiser le fichier des équipes s'il n'existe pas
        if not os.path.exists(self.teams_file):
            with open(self.teams_file, 'w') as f:
                json.dump([], f)

        # Configuration de match actuelle
        self.current_match = {
            'team_a': None,
            'team_b': None
        }

    def get_all_teams(self):
        """
        Récupère toutes les équipes enregistrées

        Returns:
            list: Liste des équipes
        """
        try:
            with open(self.teams_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.error("Erreur lors de la lecture du fichier teams.json")
            return []

    def get_team(self, team_id):
        """
        Récupère une équipe spécifique par son ID

        Args:
            team_id: ID de l'équipe

        Returns:
            dict: Données de l'équipe ou None si non trouvée
        """
        teams = self.get_all_teams()
        for team in teams:
            if team['id'] == team_id:
                return team
        return None

    def create_team(self, name, logo=None, players=None):
        """
        Crée une nouvelle équipe

        Args:
            name: Nom de l'équipe
            logo: Chemin vers le logo de l'équipe
            players: Liste des joueurs

        Returns:
            str: ID de l'équipe créée
        """
        teams = self.get_all_teams()
        team_id = str(uuid.uuid4())

        new_team = {
            'id': team_id,
            'name': name,
            'logo': logo,
            'players': players or []
        }

        teams.append(new_team)

        try:
            with open(self.teams_file, 'w') as f:
                json.dump(teams, f, indent=4)
            logger.info(f"Équipe '{name}' créée avec succès (ID: {team_id})")
            return team_id
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'équipe '{name}': {e}")
            return None

    def update_team(self, team_id, name=None, logo=None, players=None):
        """
        Met à jour une équipe existante

        Args:
            team_id: ID de l'équipe
            name: Nouveau nom de l'équipe (optionnel)
            logo: Nouveau logo de l'équipe (optionnel)
            players: Nouvelle liste de joueurs (optionnel)

        Returns:
            bool: True si mise à jour réussie, False sinon
        """
        teams = self.get_all_teams()
        for i, team in enumerate(teams):
            if team['id'] == team_id:
                if name:
                    team['name'] = name
                if logo:
                    team['logo'] = logo
                if players:
                    team['players'] = players

                try:
                    with open(self.teams_file, 'w') as f:
                        json.dump(teams, f, indent=2)
                    logger.info(f"Équipe mise à jour avec succès: {team['name']}")
                    return True
                except Exception as e:
                    logger.error(f"Erreur lors de la mise à jour de l'équipe: {str(e)}")
                    return False

        logger.warning(f"Équipe non trouvée pour mise à jour: {team_id}")
        return False

    def delete_team(self, team_id):
        """
        Supprime une équipe

        Args:
            team_id: ID de l'équipe

        Returns:
            bool: True si suppression réussie, False sinon
        """
        teams = self.get_all_teams()
        team_found = False

        for i, team in enumerate(teams):
            if team['id'] == team_id:
                # Supprimer le logo si nécessaire
                if team.get('logo') and os.path.exists(team['logo']):
                    try:
                        os.remove(team['logo'])
                    except Exception as e:
                        logger.warning(f"Impossible de supprimer le logo: {str(e)}")

                teams.pop(i)
                team_found = True
                break

        if team_found:
            try:
                with open(self.teams_file, 'w') as f:
                    json.dump(teams, f, indent=2)
                logger.info(f"Équipe supprimée avec succès: {team_id}")
                return True
            except Exception as e:
                logger.error(f"Erreur lors de la suppression de l'équipe: {str(e)}")
                return False

        logger.warning(f"Équipe non trouvée pour suppression: {team_id}")
        return False

    def get_team_players(self, team_id):
        """
        Récupère les joueurs d'une équipe

        Args:
            team_id: ID de l'équipe

        Returns:
            list: Liste des joueurs de l'équipe ou None si équipe non trouvée
        """
        team = self.get_team(team_id)
        if team:
            return team.get('players', [])
        return None

    def save_team_logo(self, logo_file):
        """
        Sauvegarde le logo d'une équipe

        Args:
            logo_file: Fichier logo uploadé

        Returns:
            str: Chemin vers le fichier sauvegardé
        """
        if not logo_file:
            return None

        # Sécuriser le nom de fichier
        filename = secure_filename(logo_file.filename)
        # Ajouter un identifiant unique pour éviter les collisions
        unique_filename = f"{uuid.uuid4()}_{filename}"
        # Chemin complet
        filepath = os.path.join(self.logos_dir, unique_filename)

        # Enregistrer le fichier
        try:
            logo_file.save(filepath)
            logger.info(f"Logo enregistré avec succès: {filepath}")

            # Créer un lien symbolique vers le dossier static si nécessaire
            static_logos_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'media', 'team_logos')
            os.makedirs(static_logos_dir, exist_ok=True)

            # Copier le fichier dans le dossier static
            import shutil
            static_filepath = os.path.join(static_logos_dir, unique_filename)
            shutil.copy2(filepath, static_filepath)

            # Retourner le chemin relatif pour l'URL
            return f"/static/media/team_logos/{unique_filename}"
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du logo: {str(e)}")
            return None

    def parse_players_csv(self, csv_file):
        """
        Parse un fichier CSV pour obtenir la liste des joueurs

        Args:
            csv_file: Fichier CSV uploadé

        Returns:
            list: Liste des joueurs
        """
        if not csv_file:
            return []

        players = []
        try:
            # Lire le contenu du fichier
            content = csv_file.read().decode('utf-8')

            # Créer un lecteur CSV
            csv_reader = csv.reader(content.splitlines(), delimiter=',')

            # Parser les lignes
            header = next(csv_reader, None)
            if header:
                # Déterminer les indices des colonnes
                indices = {
                    'numero': header.index('numero') if 'numero' in header else None,
                    'nom': header.index('nom') if 'nom' in header else None,
                    'prenom': header.index('prenom') if 'prenom' in header else None,
                    'position': header.index('position') if 'position' in header else None,
                    'taille': header.index('taille') if 'taille' in header else None,
                    'date_naissance': header.index('date_naissance') if 'date_naissance' in header else None
                }

                # Si aucun en-tête n'est trouvé, utiliser l'ordre par défaut
                if all(idx is None for idx in indices.values()):
                    indices = {
                        'numero': 0,
                        'nom': 1,
                        'prenom': 2,
                        'position': 3,
                        'taille': 4,
                        'date_naissance': 5
                    }
            else:
                # Si aucun en-tête n'est trouvé, utiliser l'ordre par défaut
                indices = {
                    'numero': 0,
                    'nom': 1,
                    'prenom': 2,
                    'position': 3,
                    'taille': 4,
                    'date_naissance': 5
                }
                # Réinitialiser le fichier pour le relire
                csv_file.seek(0)
                content = csv_file.read().decode('utf-8')
                csv_reader = csv.reader(content.splitlines(), delimiter=',')

            # Parser les joueurs
            for row in csv_reader:
                if len(row) >= 3:  # Au moins numéro, nom, prénom
                    player = {}

                    for field, idx in indices.items():
                        if idx is not None and idx < len(row):
                            player[field] = row[idx]

                    players.append(player)

            logger.info(f"Fichier CSV parsé avec succès: {len(players)} joueurs trouvés")
            return players
        except Exception as e:
            logger.error(f"Erreur lors du parsing du fichier CSV: {str(e)}")
            return []

    def set_match_teams(self, team_a_id, team_b_id):
        """
        Configure les équipes pour le match actuel

        Args:
            team_a_id: ID de l'équipe A
            team_b_id: ID de l'équipe B

        Returns:
            bool: True si configuration réussie, False sinon
        """
        team_a = self.get_team(team_a_id)
        team_b = self.get_team(team_b_id)

        if not team_a or not team_b:
            logger.error("Équipes non trouvées pour la configuration du match")
            return False

        self.current_match = {
            'team_a': team_a,
            'team_b': team_b
        }

        # Enregistrer la configuration dans un fichier
        match_config_file = os.path.join(self.data_dir, 'current_match.json')
        try:
            with open(match_config_file, 'w') as f:
                json.dump(self.current_match, f, indent=2)
            logger.info(f"Configuration du match enregistrée: {team_a['name']} vs {team_b['name']}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de la configuration du match: {str(e)}")
            return False

    def get_current_match(self):
        """
        Récupère la configuration du match actuel

        Returns:
            dict: Configuration du match actuel
        """
        # Essayer de charger depuis le fichier si nécessaire
        if not self.current_match['team_a'] or not self.current_match['team_b']:
            match_config_file = os.path.join(self.data_dir, 'current_match.json')
            if os.path.exists(match_config_file):
                try:
                    with open(match_config_file, 'r') as f:
                        self.current_match = json.load(f)
                except Exception as e:
                    logger.error(f"Erreur lors du chargement de la configuration du match: {str(e)}")

        return self.current_match
