#fonctionnalités à implémenter :
# -connexion vmix, -status de la connexion (websocket), -gestion des inputs (add, switch de cam, mute micros, replay)
# -gestion des overlays (-thumbnail, -liste équipe, -detail joueur, -score, -pub/sponsors)

import requests
from requests import RequestException
from urllib.parse import urljoin # this import is used to construct URLs correctly
import xml.etree.ElementTree as ET #todo source de cet import
import logging
# Configuration du logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('vmix_manager')


#var global
#host = '127.0.0.1'
#port = 8088

class VMixManager:
    def __init__(self, host='127.0.0.1', port=8088):
        """
        Initialise le gestionnaire vMix

        Args:
            host: Adresse IP du serveur vMix
            port: Port du serveur vMix
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/api/"
        logger.info(f"VMixManager initialized with base URL: {self.base_url}")

    def check_connection(self):
        """Vérifie la connexion à vMix"""
        try:
            response = requests.get(self.base_url, timeout=2)
            return response.status_code == 200
        except RequestException:
            logger.error("Failed to connect to vMix")
            return False

    def get_inputs(self):
        """Récupère la liste des inputs disponibles dans vMix"""
        try:
            logger.info("Récupération des entrées vMix")

            # Utilisation de l'API de base vMix sans spécifier de fonction particulière
            # Cela renvoie l'état complet de vMix en XML
            url = f"http://{self.host}:{self.port}/api/"
            logger.info(f"URL de requête: {url}")

            response = requests.get(url, timeout=5)
            logger.info(f"Code de réponse: {response.status_code}")

            if response.status_code == 200:
                try:
                    # Analyser la réponse XML
                    root = ET.fromstring(response.text)
                    inputs = []

                    # Dans l'API vMix standard, les inputs sont directement sous le nœud racine "vmix/inputs"
                    for input_elem in root.findall('./inputs/input'):
                        # Récupérer les attributs avec gestion des valeurs par défaut
                        input_number = input_elem.get('number', '')
                        title = input_elem.get('title', '')

                        # Le type est parfois stocké comme attribut, parfois comme élément enfant
                        input_type = input_elem.get('type', '')
                        state = input_elem.get('state', '')

                        if not title:
                            title = f"Input {input_number}"

                        logger.info(f"Input détecté - Numéro: {input_number}, Titre: {title}, Type: {input_type}")

                        # Déterminer la catégorie de l'input
                        category = self._determine_input_category(input_type, title)

                        input_data = {
                            'id': input_number,
                            'number': input_number,
                            'name': title,
                            'title': title,
                            'type': input_type,
                            'state': state,
                            'category': category
                        }
                        inputs.append(input_data)

                    logger.info(f"Récupération réussie: {len(inputs)} entrées trouvées")
                    return inputs
                except ET.ParseError as xml_err:
                    logger.error(f"Erreur de parsing XML: {str(xml_err)}")
            else:
                logger.warning(f"Échec de récupération des entrées: code {response.status_code}")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des entrées vMix: {str(e)}", exc_info=True)

        # Si tout échoue, retourner une liste vide
        logger.warning("Aucune entrée n'a pu être récupérée, retour d'une liste vide")
        return []

    def _determine_input_category(self, input_type, title):
        """Détermine la catégorie d'une entrée en fonction de son type et de son titre"""
        input_type_lower = input_type.lower() if input_type else ''
        title_lower = title.lower() if title else ''

        # Mots-clés pour détecter les caméras
        camera_keywords = ['camera', 'webcam', 'capture', 'video capture', 'cam', 'caméra', 'webcamera']

        # Mots-clés pour les vidéos
        video_keywords = ['video', 'movie', 'mp4', 'avi', 'mov', 'film', 'clip', 'vidéo']

        # Mots-clés pour l'audio
        audio_keywords = ['audio', 'sound', 'mic', 'microphone', 'son', 'micro', 'ambient', 'ambiance']

        # Vérification des types spéciaux
        if input_type_lower == 'blank' or title_lower == 'blank':
            return 'blank'

        # Vérification des caméras basée sur le type ou le titre
        if any(cam_type in input_type_lower for cam_type in camera_keywords) or \
           any(cam_type in title_lower for cam_type in camera_keywords):
            return 'camera'

        # Vérification des vidéos
        if any(vid_type in input_type_lower for vid_type in video_keywords) or \
           any(vid_type in title_lower for vid_type in video_keywords):
            return 'video'

        # Vérification de l'audio
        if any(audio_type in input_type_lower for audio_type in audio_keywords) or \
           any(audio_type in title_lower for audio_type in audio_keywords):
            return 'audio'

        # Si aucune correspondance n'est trouvée, retourner une catégorie par défaut
        if 'title' in input_type_lower:
            return 'title'

        return 'other'

    def send_roster_to_vmix(self, team_name, players):
        """
        Envoie les données d'un roster d'équipe vers vMix

        Args:
            team_name: Nom de l'équipe
            players: Liste des joueurs

        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            # Exemple d'implémentation - à adapter selon vos besoins
            # Supposons que vous utilisez un input de type "Title" avec un ID spécifique
            title_input = "TeamRoster"  # Nom ou numéro de l'input dans vMix

            # Construction des données à envoyer
            player_list = ""
            for i, player in enumerate(players):
                player_info = f"{player.get('numero', 'N/A')} - {player.get('prenom', '')} {player.get('nom', '').upper()}"
                player_list += f"{player_info}<br>"

            # Envoi des données à vMix
            params = {
                "Function": "SetText",
                "Input": title_input,
                "SelectedName": "TeamName",
                "Value": team_name
            }
            response1 = requests.get(self.base_url, params=params, timeout=2)

            params = {
                "Function": "SetText",
                "Input": title_input,
                "SelectedName": "PlayerList",
                "Value": player_list
            }
            response2 = requests.get(self.base_url, params=params, timeout=2)

            return response1.status_code == 200 and response2.status_code == 200
        except RequestException as e:
            logger.error(f"Error sending roster to vMix: {e}")
            return False

    def show_player_details(self, player, team_name=None):
        """
        Affiche les détails d'un joueur dans vMix

        Args:
            player: Dictionnaire contenant les données du joueur
            team_name: Nom de l'équipe (optionnel)

        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            # Exemple d'implémentation - à adapter selon vos besoins
            title_input = "PlayerDetails"  # Nom ou numéro de l'input dans vMix

            # Envoi des données à vMix
            responses = []

            # Nom du joueur
            params = {
                "Function": "SetText",
                "Input": title_input,
                "SelectedName": "PlayerName",
                "Value": f"{player.get('prenom', '')} {player.get('nom', '').upper()}"
            }
            responses.append(requests.get(self.base_url, params=params, timeout=2))

            # Numéro du joueur
            params = {
                "Function": "SetText",
                "Input": title_input,
                "SelectedName": "PlayerNumber",
                "Value": player.get('numero', 'N/A')
            }
            responses.append(requests.get(self.base_url, params=params, timeout=2))

            # Position du joueur
            params = {
                "Function": "SetText",
                "Input": title_input,
                "SelectedName": "Position",
                "Value": player.get('position', 'Non spécifiée')
            }
            responses.append(requests.get(self.base_url, params=params, timeout=2))

            # Taille du joueur
            params = {
                "Function": "SetText",
                "Input": title_input,
                "SelectedName": "Height",
                "Value": f"{player.get('taille', 'N/A')} cm" if player.get('taille') else "Non spécifiée"
            }
            responses.append(requests.get(self.base_url, params=params, timeout=2))

            # Équipe du joueur (si fournie)
            if team_name:
                params = {
                    "Function": "SetText",
                    "Input": title_input,
                    "SelectedName": "TeamName",
                    "Value": team_name
                }
                responses.append(requests.get(self.base_url, params=params, timeout=2))

            # Vérifier que toutes les requêtes ont réussi
            return all(response.status_code == 200 for response in responses)
        except RequestException as e:
            logger.error(f"Error showing player details in vMix: {e}")
            return False

    def set_title_text(self, input_name, field_name, value):
        """
        Définit le texte d'un champ dans un titre vMix

        Args:
            input_name: Nom ou numéro de l'input
            field_name: Nom du champ
            value: Valeur à définir

        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            params = {
                "Function": "SetText",
                "Input": input_name,
                "SelectedName": field_name,
                "Value": value
            }
            response = requests.get(self.base_url, params=params, timeout=2)
            return response.status_code == 200
        except RequestException as e:
            logger.error(f"Error setting title text in vMix: {e}")
            return False

    def update_title_multiple(self, input_name, field_values):
        """
        Met à jour plusieurs champs dans un titre vMix

        Args:
            input_name: Nom ou numéro de l'input
            field_values: Dictionnaire {nom_champ: valeur}

        Returns:
            bool: True si toutes les opérations ont réussi, False sinon
        """
        try:
            results = []
            for field_name, value in field_values.items():
                result = self.set_title_text(input_name, field_name, value)
                results.append(result)

            return all(results)
        except Exception as e:
            logger.error(f"Error updating multiple fields in vMix title: {e}")
            return False

    def set_image(self, input_name, field_name, image_path):
        """
        Définit une image dans un champ d'un titre vMix

        Args:
            input_name: Nom ou numéro de l'input
            field_name: Nom du champ
            image_path: Chemin vers l'image

        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            params = {
                "Function": "SetImage",
                "Input": input_name,
                "SelectedName": field_name,
                "Value": image_path
            }
            response = requests.get(self.base_url, params=params, timeout=2)
            return response.status_code == 200
        except RequestException as e:
            logger.error(f"Error setting image in vMix: {e}")
            return False

    def send_command(self, function, **params):
        """
        Envoie une commande à l'API vMix

        Args:
            function (str): Nom de la fonction vMix à appeler
            **params: Paramètres additionnels à passer à la fonction

        Returns:
            bool: True si réussi, False sinon
        """
        # Construire l'URL de la commande
        url = self.base_url + f"?Function={function}"

        # Ajouter les paramètres à l'URL
        for key, value in params.items():
            url += f"&{key}={value}"

        try:
            logger.info(f"Envoi commande vMix: {function} avec paramètres: {params}")
            response = requests.get(url, timeout=3)

            if response.status_code == 200:
                logger.info("Commande exécutée avec succès")
                return True
            else:
                logger.warning(f"Échec de la commande: code {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la commande: {str(e)}")
            return False

    ######### title cmd #########

    def set_title_text(self, input_id, field_name, text):
        """
        Met à jour un champ texte d'un titre vMix

        Args:
            input_id (str): L'ID de l'entrée titre
            field_name (str): Le nom du champ à mettre à jour
            text (str): Le texte à insérer dans le champ

        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Construire les paramètres pour la fonction SetText
            params = {
                'Function': 'SetText',
                'Input': input_id,
                'SelectedName': field_name,
                'Value': text
            }

            # Envoyer la requête à l'API vMix
            url = self.base_url
            response = requests.get(url, params=params, timeout=3)

            if response.status_code == 200:
                logger.info(f"Texte mis à jour: Input={input_id}, Champ={field_name}, Valeur={text}")
                return True
            else:
                logger.error(f"Échec de mise à jour du texte: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du texte: {e}")
            return False

    def update_title_multiple(self, input_id, field_values):
        """
        Met à jour plusieurs champs d'un titre vMix en une seule fois

        Args:
            input_id (str): L'ID de l'entrée titre
            field_values (dict): Dictionnaire de paires {nom_champ: valeur}

        Returns:
            bool: True si toutes les mises à jour ont réussi, False sinon
        """
        success = True
        for field_name, value in field_values.items():
            result = self.set_title_text(input_id, field_name, str(value))
            if not result:
                success = False
                logger.error(f"Échec de mise à jour pour le champ {field_name}")
        return success

    def update_scoreboard(self, team_a_name, team_b_name, score_a, score_b, sets_a, sets_b, title_input="Scoreboard"):
        """
        Met à jour le scoreboard dans vMix avec les informations du match

        Args:
            team_a_name: Nom de l'équipe A
            team_b_name: Nom de l'équipe B
            score_a: Score de l'équipe A
            score_b: Score de l'équipe B
            sets_a: Sets gagnés par l'équipe A
            sets_b: Sets gagnés par l'équipe B
            title_input: Nom ou ID de l'input du scoreboard dans vMix

        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            # Nettoyage et validation des scores
            score_a_str = '0' if not str(score_a).strip() or str(score_a).strip() == '-' else str(score_a)
            score_b_str = '0' if not str(score_b).strip() or str(score_b).strip() == '-' else str(score_b)
            sets_a_str = '0' if not str(sets_a).strip() or str(sets_a).strip() == '-' else str(sets_a)
            sets_b_str = '0' if not str(sets_b).strip() or str(sets_b).strip() == '-' else str(sets_b)

            # Construction des URLs pour mettre à jour les scores et sets avec les noms de champs spécifiés
            score_a_url = f'http://{self.host}:{self.port}/API/?Function=SetText&Input={title_input}&SelectedName=scoreTeamA&Value={score_a_str}'
            score_b_url = f'http://{self.host}:{self.port}/API/?Function=SetText&Input={title_input}&SelectedName=scoreTeamB&Value={score_b_str}'
            sets_a_url = f'http://{self.host}:{self.port}/API/?Function=SetText&Input={title_input}&SelectedName=setTeamA&Value={sets_a_str}'
            sets_b_url = f'http://{self.host}:{self.port}/API/?Function=SetText&Input={title_input}&SelectedName=setTeamB&Value={sets_b_str}'

            # Mettre à jour les noms d'équipes si fournis
            team_a_url = None
            team_b_url = None
            if team_a_name:
                team_a_url = f'http://{self.host}:{self.port}/API/?Function=SetText&Input={title_input}&SelectedName=teamNameA&Value={team_a_name}'
            if team_b_name:
                team_b_url = f'http://{self.host}:{self.port}/API/?Function=SetText&Input={title_input}&SelectedName=teamNameB&Value={team_b_name}'

            # Envoi des requêtes à vMix
            logger.info(f"Mise à jour du scoreboard dans vMix: {score_a_str}-{score_b_str} Sets: {sets_a_str}-{sets_b_str}")

            requests.get(score_a_url, timeout=3)
            requests.get(score_b_url, timeout=3)
            requests.get(sets_a_url, timeout=3)
            requests.get(sets_b_url, timeout=3)

            # Mise à jour des noms d'équipes si spécifiés
            if team_a_url:
                requests.get(team_a_url, timeout=3)
            if team_b_url:
                requests.get(team_b_url, timeout=3)

            logger.info(f"Scoreboard mis à jour avec succès: {team_a_name} {score_a_str}-{score_b_str} {team_b_name}, sets: {sets_a_str}-{sets_b_str}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du scoreboard: {str(e)}")
            return False

    def set_image(self, input_id, field_name, image_path):
        """
        Met à jour un champ image d'un titre vMix

        Args:
            input_id (str): L'ID de l'entrée titre
            field_name (str): Le nom du champ à mettre à jour
            image_path (str): Le chemin vers l'image à utiliser

        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Construire les paramètres pour la fonction SetImage
            params = {
                'Function': 'SetImage',
                'Input': input_id,
                'SelectedName': field_name,
                'Value': image_path
            }

            # Envoyer la requête à l'API vMix
            url = self.base_url
            response = requests.get(url, params=params, timeout=3)

            if response.status_code == 200:
                logger.info(f"Image mise à jour: Input={input_id}, Champ={field_name}, Image={image_path}")
                return True
            else:
                logger.error(f"Échec de mise à jour de l'image: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'image: {e}")
            return False

    def find_title_input_by_name(self, name_pattern):
        """
        Trouve un input de type titre par son nom (recherche partielle)

        Args:
            name_pattern (str): Motif à rechercher dans le nom de l'input

        Returns:
            str: ID de l'input trouvé ou None si non trouvé
        """
        inputs = self.get_inputs()
        for input_item in inputs:
            if ('title' in input_item.get('type', '').lower() or 'gt' in input_item.get('type', '').lower()) and \
               name_pattern.lower() in input_item.get('name', '').lower():
                return input_item['id']
        return None

    def start_streaming(self, channel=0):
        """
        Démarre le streaming sur un canal spécifique

        Args:
            channel (int): Numéro du canal de streaming (0 = tous les canaux, 1-5 = canal spécifique)

        Returns:
            bool: True si réussi, False sinon
        """
        logger.info(f"Démarrage du streaming sur le canal {channel if channel else 'par défaut'}")
        try:
            # Si un canal spécifique est demandé (1-5)
            if 1 <= channel <= 5:
                response = requests.get(f"{self.base_url}?Function=StartStreaming&Value={channel}", timeout=3)
            else:
                # Utiliser le canal par défaut (généralement le 1)
                response = requests.get(f"{self.base_url}?Function=StartStreaming", timeout=3)

            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du streaming: {str(e)}")
            return False

    def stop_streaming(self, channel=0):
        """
        Arrête le streaming sur un canal spécifique

        Args:
            channel (int): Numéro du canal de streaming (0 = tous les canaux, 1-5 = canal spécifique)

        Returns:
            bool: True si réussi, False sinon
        """
        logger.info(f"Arrêt du streaming sur le canal {channel if channel else 'par défaut'}")
        try:
            # Si un canal spécifique est demandé (1-5)
            if 1 <= channel <= 5:
                response = requests.get(f"{self.base_url}?Function=StopStreaming&Value={channel}", timeout=3)
            else:
                # Arrêter tous les canaux
                response = requests.get(f"{self.base_url}?Function=StopStreaming", timeout=3)

            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du streaming: {str(e)}")
            return False

    def get_streaming_status(self, channel=1):
        """
        Récupère le statut du streaming pour un canal spécifique

        Args:
            channel (int): Numéro du canal de streaming (1-5)

        Returns:
            bool: True si le streaming est actif, False sinon
        """
        try:
            # Récupérer l'état général de vMix
            response = requests.get(f"{self.base_url}?Function=GetStatus", timeout=3)
            if response.status_code != 200:
                return False

            # Analyser le XML pour trouver l'état du streaming
            root = ET.fromstring(response.text)

            # Rechercher l'état du canal spécifique
            if 1 <= channel <= 5:
                streaming_element = root.find(f"./Streaming[@channel='{channel}']")
                if streaming_element is not None:
                    return streaming_element.text.lower() == "true"

            # Rechercher l'état général du streaming
            streaming_element = root.find("./Streaming")
            if streaming_element is not None:
                return streaming_element.text.lower() == "true"

            return False
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut du streaming: {str(e)}")
            return False

    def get_recording_status(self):
        """
        Récupère le statut de l'enregistrement

        Returns:
            bool: True si l'enregistrement est actif, False sinon
        """
        try:
            # Récupérer l'état général de vMix
            response = requests.get(f"{self.base_url}?Function=GetStatus", timeout=3)
            if response.status_code != 200:
                return False

            # Analyser le XML pour trouver l'état de l'enregistrement
            root = ET.fromstring(response.text)
            recording_element = root.find("./Recording")

            if recording_element is not None:
                return recording_element.text.lower() == "true"

            return False
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut de l'enregistrement: {str(e)}")
            return False

    def start_recording(self):
        """
        Démarre l'enregistrement

        Returns:
            bool: True si réussi, False sinon
        """
        logger.info("Démarrage de l'enregistrement")
        try:
            response = requests.get(f"{self.base_url}?Function=StartRecording", timeout=3)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de l'enregistrement: {str(e)}")
            return False

    def stop_recording(self):
        """
        Arrête l'enregistrement

        Returns:
            bool: True si réussi, False sinon
        """
        logger.info("Arrêt de l'enregistrement")
        try:
            response = requests.get(f"{self.base_url}?Function=StopRecording", timeout=3)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt de l'enregistrement: {str(e)}")
            return False

    def toggle_audio(self, input_number, mute=None):
        """
        Active ou désactive l'audio d'une entrée spécifique.

        Args:
            input_number: Numéro ou nom de l'input
            mute: Si None, inverse l'état actuel (toggle).
                 Si True, coupe l'audio.
                 Si False, active l'audio.

        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            function = None
            if mute is None:
                function = "AudioToggle"
                logger.info(f"Toggle audio pour input {input_number}")
            elif mute:
                function = "AudioOff"
                logger.info(f"Mute audio pour input {input_number}")
            else:
                function = "AudioOn"
                logger.info(f"Unmute audio pour input {input_number}")

            params = {
                "Function": function,
                "Input": input_number
            }
            response = requests.get(self.base_url, params=params, timeout=2)
            return response.status_code == 200
        except RequestException as e:
            logger.error(f"Error toggling audio in vMix: {e}")
            return False

    def adjust_audio_volume(self, input_number, volume):
        """
        Ajuste le volume d'une entrée audio

        Args:
            input_number: Numéro ou nom de l'input
            volume: Valeur du volume (entre 0 et 100)

        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            # S'assurer que le volume est entre 0 et 100
            volume = max(0, min(100, volume))

            params = {
                "Function": "SetVolume",
                "Input": input_number,
                "Value": volume
            }
            logger.info(f"Ajustement volume pour input {input_number} à {volume}%")
            response = requests.get(self.base_url, params=params, timeout=2)
            return response.status_code == 200
        except RequestException as e:
            logger.error(f"Error adjusting volume in vMix: {e}")
            return False

    def get_audio_status(self, input_number=None):
        """
        Récupère le statut audio des entrées vMix

        Args:
            input_number: Si spécifié, retourne uniquement le statut de cet input

        Returns:
            dict: Statut audio des entrées ou None en cas d'erreur
        """
        try:
            response = requests.get(self.base_url, timeout=2)
            if response.status_code == 200:
                root = ET.fromstring(response.text)

                audio_statuses = {}
                for input_elem in root.findall('.//inputs/input'):
                    input_id = input_elem.get('number')

                    # Si un input_number spécifique est demandé, ne traiter que celui-là
                    if input_number and input_id != str(input_number):
                        continue

                    # Récupérer les informations audio
                    audio_status = {
                        'id': input_id,
                        'title': input_elem.get('title', ''),
                        'muted': input_elem.get('muted', 'False').lower() == 'true',
                        'volume': input_elem.get('volume', '100'),
                        'balance': input_elem.get('balance', '0'),
                        'audiobusses': input_elem.get('audiobusses', '')
                    }

                    audio_statuses[input_id] = audio_status

                return audio_statuses if not input_number else (audio_statuses.get(str(input_number), None))

            return None
        except Exception as e:
            logger.error(f"Error getting audio status from vMix: {e}")
            return None

    ######### handle overlay #########

    def set_overlay(self, input_name, overlay_number, state=True):
        """Contrôle les overlays vMix"""
        action = "SetOverlayOn" if state else "SetOverlayOff"
        logger.info(f"Configuration overlay: {action}, input={input_name}, overlay={overlay_number}")
        try:
            response = requests.get(f"{self.base_url}?Function={action}&Input={input_name}&Value={overlay_number}", timeout=3)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erreur lors de la configuration de l'overlay: {str(e)}")
            return False

    def show_score_overlay(self, overlay_number=1):
        """Affiche l'overlay du score"""
        logger.info(f"Affichage de l'overlay de score n°{overlay_number}")
        return self.set_overlay(overlay_number, 1, True)

    def show_player_stats(self, player_id, overlay_number=2):
        """Affiche les statistiques d'un joueur spécifique"""
        logger.info(f"Affichage des stats du joueur {player_id} sur l'overlay n°{overlay_number}")
        # D'abord définir les données du joueur dans l'overlay
        # Puis afficher l'overlay
        return self.set_overlay(overlay_number, 2, True)

    def show_match_thumbnail(self, thumbnail_input, overlay_number=3):
        """Affiche la miniature du match comme overlay"""
        logger.info(f"Affichage de la miniature du match depuis l'entrée {thumbnail_input}")
        # Configurer l'overlay pour utiliser l'entrée de la miniature
        self.send_command("SetOverlayInput1", input=overlay_number, value=thumbnail_input)
        # Afficher l'overlay
        return self.set_overlay(overlay_number, 3, True)

    ######### Méthodes pour la gestion des replays #########

    def create_replay_event(self, event_name=None, duration=10):
        """Crée un nouvel événement de replay avec une durée spécifiée"""
        logger.info(f"Création d'un événement replay de {duration} secondes")
        params = {"duration": duration}
        if event_name:
            params["value"] = event_name
        return self.send_command("ReplayPlayEventToOutput", **params)

    def start_recording_replay(self):
        """Démarre l'enregistrement du replay"""
        logger.info("Démarrage de l'enregistrement du replay")
        return self.send_command("ReplayStartRecording")

    def stop_recording_replay(self):
        """Arrête l'enregistrement du replay"""
        logger.info("Arrêt de l'enregistrement du replay")
        return self.send_command("ReplayStopRecording")

    def play_last_replay(self, speed=100):
        """Joue le dernier replay enregistré à la vitesse spécifiée (en pourcentage)"""
        logger.info(f"Lecture du dernier replay à {speed}% de la vitesse normale")

        # Vérifier que la vitesse est une valeur valide (généralement 25%, 50% ou 100%)
        valid_speeds = [25, 50, 75, 100]
        if speed not in valid_speeds:
            speed = 100  # Valeur par défaut

        return self.send_command("ReplayPlay", speed=speed)

    def pause_replay(self):
        """Met en pause la lecture du replay"""
        logger.info("Mise en pause du replay")
        return self.send_command("ReplayPause")

    def mark_replay_event(self, event_name=""):
        """Marque un événement dans le replay avec un nom optionnel"""
        logger.info(f"Marquage d'événement replay: {event_name}")
        if event_name:
            return self.send_command("ReplayMarkIn", value=event_name)
        else:
            return self.send_command("ReplayMarkIn")

    def get_replay_events(self):
        """Récupère la liste des événements de replay marqués"""
        logger.info("Récupération des événements de replay")
        # Cette fonction est conceptuelle - l'API vMix actuelle ne permet pas directement
        # de récupérer la liste des événements. Vous devrez peut-être implémenter une
        # solution personnalisée en utilisant les événements marqués dans votre application.
        return []

    def play_replay_event(self, event_index, speed=100):
        """Joue un événement de replay spécifique à la vitesse spécifiée"""
        logger.info(f"Lecture de l'événement replay {event_index} à {speed}% de la vitesse")

        # Vérifier que la vitesse est une valeur valide
        valid_speeds = [25, 50, 75, 100]
        if speed not in valid_speeds:
            speed = 100  # Valeur par défaut

        return self.send_command("ReplayPlayEvent", value=event_index, speed=speed)

    def set_replay_duration(self, seconds=8):
        """Configure la durée du buffer de replay en secondes"""
        logger.info(f"Configuration de la durée du buffer de replay à {seconds} secondes")
        return self.send_command("ReplaySetDuration", value=seconds)

    def start_recording(self):
        """Démarre l'enregistrement"""
        logger.info("Démarrage de l'enregistrement")
        return self.send_command("StartRecording")

    def stop_recording(self):
        """Arrête l'enregistrement"""
        logger.info("Arrêt de l'enregistrement")
        return self.send_command("StopRecording")

    def pause_recording(self):
        """Met en pause l'enregistrement"""
        logger.info("Mise en pause de l'enregistrement")
        return self.send_command("PauseRecording")

    def load_preset(self, preset_name):
        """Charge un preset vMix enregistré"""
        logger.info(f"Chargement du preset {preset_name}")
        return self.send_command("OpenPreset", value=preset_name)

    def save_preset(self, preset_name):
        """Enregistre l'état actuel de vMix comme un preset"""
        logger.info(f"Enregistrement du preset {preset_name}")
        return self.send_command("SavePreset", value=preset_name)

    def execute_script(self, script_name):
        """Exécute un script vMix"""
        logger.info(f"Exécution du script {script_name}")
        return self.send_command("ScriptStart", value=script_name)

    ####### get vMix status #########
    def get_streaming_status(self):
        """Récupère l'état actuel du streaming"""
        try:
            response = requests.get(self.base_url, timeout=3)
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                streaming = root.find('streaming')
                if streaming is not None:
                    return streaming.text == 'True'
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut de streaming: {str(e)}")
            return False

    def get_recording_status(self):
        """Récupère l'état actuel de l'enregistrement"""
        try:
            response = requests.get(self.base_url, timeout=3)
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                recording = root.find('recording')
                if recording is not None:
                    return recording.text == 'True'
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut d'enregistrement: {str(e)}")
            return False

    def get_active_input(self):
        """Récupère l'entrée actuellement active dans vMix"""
        try:
            response = requests.get(self.base_url, timeout=3)
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                active = root.find('active')
                if active is not None:
                    return active.text
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'entrée active: {str(e)}")
            return None


    #### méthode pour le voleyball ####
    # todo to move into a specific file/module
    def update_score(self, home_score, away_score, input_number, layer_home=0, layer_away=1):
        """Met à jour le score du match"""
        logger.info(f"Mise à jour du score: {home_score}-{away_score}")
        self.set_text(input_number, str(home_score), layer_home)
        return self.set_text(input_number, str(away_score), layer_away)

    def update_set_scores(self, sets_score, input_number, layer=2):
        """Met à jour le score des sets (par exemple '2-1')"""
        logger.info(f"Mise à jour du score des sets: {sets_score}")
        return self.set_text(input_number, sets_score, layer)

    def show_timeout_graphic(self, team, duration=30, overlay_number=4):
        """Affiche un graphique de timeout pour une équipe spécifiée"""
        logger.info(f"Affichage du graphique de timeout pour l'équipe {team}")
        # Configuration du graphique de timeout
        self.set_text(overlay_number, f"TIMEOUT {team}", 0)
        # Affichage de l'overlay
        result = self.set_overlay(overlay_number, 4, True)
        # Programmation de la disparition après la durée spécifiée
        # Notez que ceci est conceptuel - vous devrez implémenter la temporisation ailleurs
        return result

    #### websocket connection ####
    #todo to move into a specific file
    def setup_websocket_monitoring(self, callback):
        """
        Configure une connexion WebSocket pour surveiller les changements d'état de vMix
        Cette fonction est conceptuelle et nécessiterait une implémentation spécifique
        """
        logger.info("Configuration de la surveillance WebSocket vMix")
        # La mise en œuvre dépendrait de la façon dont vMix expose ses événements WebSocket
        # Cette fonction servirait de point d'entrée pour cette fonctionnalité

    def set_text(self, input_id, value, selected_name=0):
        """
        Envoie une commande SetText à un titre vMix.

        Args:
            input_id: ID ou nom de l'input titre
            value: texte à définir
            selected_name: nom du champ (ou index) dans le titre

        Returns:
            bool: True si la commande a réussi
        """
        try:
            params = {
                'Function': 'SetText',
                'Input': input_id,
                'SelectedName': str(selected_name),
                'Value': value
            }
            response = requests.get(self.base_url, params=params, timeout=3)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de SetText: {e}")
            return False

    def update_scoreboard(self, team_a_name, team_b_name, score_a, score_b, sets_a, sets_b, title_input="scoreboard"):
        """
        Met à jour le scoreboard vMix avec les informations du match

        Args:
            team_a_name: Nom de l'équipe A
            team_b_name: Nom de l'équipe B
            score_a: Score de l'équipe A
            score_b: Score de l'équipe B
            sets_a: Sets gagnés par l'équipe A
            sets_b: Sets gagnés par l'équipe B
            title_input: Nom ou ID de l'input du scoreboard dans vMix

        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        logger.info(f"Mise à jour du scoreboard: {team_a_name} {score_a}-{score_b} {team_b_name}, sets: {sets_a}-{sets_b}")

        try:
            # Format basé sur le code v1_0/vmix_score_updater.py
            # Utilisation des noms de champs txt*.Text
            # Nettoyage et validation des scores
            score_a_str = '0' if not str(score_a).strip() or str(score_a).strip() == '-' else str(score_a)
            score_b_str = '0' if not str(score_b).strip() or str(score_b).strip() == '-' else str(score_b)
            sets_a_str = '0' if not str(sets_a).strip() or str(sets_a).strip() == '-' else str(sets_a)
            sets_b_str = '0' if not str(sets_b).strip() or str(sets_b).strip() == '-' else str(sets_b)

            # Mise à jour des scores et sets
            fields_to_update = {
                "txtScoreTeamA.Text": score_a_str,
                "txtScoreTeamB.Text": score_b_str,
                "txtSetTeamA.Text": sets_a_str,
                "txtSetTeamB.Text": sets_b_str
            }

            # Mise à jour des noms d'équipes si fournis
            if team_a_name:
                fields_to_update["txtTeamA.Text"] = team_a_name
            if team_b_name:
                fields_to_update["txtTeamB.Text"] = team_b_name

            # Essayer toutes les variantes possibles des noms de champs
            all_fields = {}
            all_fields.update(fields_to_update)

            # Variantes sans le .Text
            for field, value in fields_to_update.items():
                field_without_text = field.replace(".Text", "")
                all_fields[field_without_text] = value

            # Variantes sans le txt
            for field, value in fields_to_update.items():
                field_without_txt = field.replace("txt", "")
                all_fields[field_without_txt] = value
                field_without_both = field.replace("txt", "").replace(".Text", "")
                all_fields[field_without_both] = value

            # Variantes avec les noms standard
            standard_fields = {
                "teamNameA": team_a_name,
                "teamNameB": team_b_name,
                "scoreTeamA": score_a_str,
                "scoreTeamB": score_b_str,
                "setTeamA": sets_a_str,
                "setTeamB": sets_b_str
            }
            all_fields.update(standard_fields)

            # Envoi direct des requêtes à vMix (méthode de v1_0)
            success = True
            for field_name, value in all_fields.items():
                try:
                    url = f"{self.base_url}?Function=SetText&Input={title_input}&SelectedName={field_name}&Value={value}"
                    response = requests.get(url, timeout=3)
                    if response.status_code == 200:
                        logger.info(f"Texte mis à jour: Input={title_input}, Champ={field_name}, Valeur={value}")
                    else:
                        success = False
                        logger.warning(f"Échec de mise à jour pour le champ {field_name}: {response.status_code}")
                except Exception as e:
                    success = False
                    logger.error(f"Erreur lors de la mise à jour pour le champ {field_name}: {e}")

            return success

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du scoreboard: {e}")
            return False

    def update_scoreboard(self, team_a_name, team_b_name, score_a, score_b, sets_a, sets_b, title_input="scoreboard"):
        """
        Met à jour le scoreboard dans vMix.

        Args:
            team_a_name (str): Nom de l'équipe A
            team_b_name (str): Nom de l'équipe B
            score_a (int): Score de l'équipe A
            score_b (int): Score de l'équipe B
            sets_a (int): Sets gagnés par l'équipe A
            sets_b (int): Sets gagnés par l'équipe B
            title_input (str): Nom de l'entrée title vMix à mettre à jour (par défaut: "scoreboard")

        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        try:
            # Vérifier la connexion à vMix
            if not self.check_connection():
                logger.error("Impossible de se connecter à vMix pour mettre à jour le scoreboard")
                return False

            # Mettre à jour le nom de l'équipe A
            params_team_a = {
                "Function": "SetText",
                "Input": title_input,
                "SelectedName": "teamNameA",
                "Value": str(team_a_name)
            }
            response_team_a = requests.get(self.base_url, params=params_team_a, timeout=2)

            # Mettre à jour le nom de l'équipe B
            params_team_b = {
                "Function": "SetText",
                "Input": title_input,
                "SelectedName": "teamNameB",
                "Value": str(team_b_name)
            }
            response_team_b = requests.get(self.base_url, params=params_team_b, timeout=2)

            # Mettre à jour le score de l'équipe A
            params_score_a = {
                "Function": "SetText",
                "Input": title_input,
                "SelectedName": "scoreTeamA",
                "Value": str(score_a)
            }
            response_score_a = requests.get(self.base_url, params=params_score_a, timeout=2)

            # Mettre à jour le score de l'équipe B
            params_score_b = {
                "Function": "SetText",
                "Input": title_input,
                "SelectedName": "scoreTeamB",
                "Value": str(score_b)
            }
            response_score_b = requests.get(self.base_url, params=params_score_b, timeout=2)

            # Mettre à jour les sets de l'équipe A
            params_sets_a = {
                "Function": "SetText",
                "Input": title_input,
                "SelectedName": "setTeamA",
                "Value": str(sets_a)
            }
            response_sets_a = requests.get(self.base_url, params=params_sets_a, timeout=2)

            # Mettre à jour les sets de l'équipe B
            params_sets_b = {
                "Function": "SetText",
                "Input": title_input,
                "SelectedName": "setTeamB",
                "Value": str(sets_b)
            }
            response_sets_b = requests.get(self.base_url, params=params_sets_b, timeout=2)

            # Vérifier si toutes les requêtes ont réussi
            success = (
                response_team_a.status_code == 200 and
                response_team_b.status_code == 200 and
                response_score_a.status_code == 200 and
                response_score_b.status_code == 200 and
                response_sets_a.status_code == 200 and
                response_sets_b.status_code == 200
            )

            if success:
                logger.info(f"Scoreboard mis à jour avec succès: {team_a_name} {score_a}-{score_b} {team_b_name}, sets: {sets_a}-{sets_b}")
            else:
                logger.error("Échec de la mise à jour du scoreboard")

            return success

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du scoreboard: {str(e)}")
            return False

