import requests
from requests.exceptions import RequestException
import socket
from urllib.parse import urljoin # this import is used to construct URLs correctly
import xml.etree.ElementTree as ET
import logging

# Configuration du logger
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('vmix_manager')

class VmixManager:
    def __init__(self, host='127.0.0.1', port=8088):
        self.host = host
        self.port = port
        # S'assurer que l'URL est correctement formatée
        if host.startswith('http://') or host.startswith('https://'):
            # L'URL contient déjà le protocole
            self.base_url = f"{host}:{port}/api/"
        else:
            # Ajouter le protocole si absent
            self.base_url = f"http://{host}:{port}/api/"
        logger.info(f"VmixManager initialisé avec URL: {self.base_url}")
        # Entrées prédéfinies à utiliser (à configurer manuellement dans vMix)
        self.predefined_inputs = {
            'camera': [],      # Sera rempli avec les entrées de type caméra détectées
            'blank': [],       # Sera rempli avec les entrées de type blank détectées
            'video': [],       # Sera rempli avec les entrées de type vidéo détectées
            'audio': []        # Sera rempli avec les entrées de type audio détectées
        }
        # Essayer de détecter les entrées prédéfinies au démarrage
        self.refresh_predefined_inputs()

    def check_connection(self):
        try:
            response = requests.get(self.base_url, timeout=2)
            connected = response.status_code == 200
            logger.info(f"Connexion vMix testée: {'Réussie' if connected else 'Échouée'}")
            return connected
        except RequestException as e:
            logger.error(f"Erreur de connexion à vMix: {e}")
            return False

    def get_inputs(self):
        """Récupère la liste des entrées disponibles dans vMix"""
        try:
            logger.info("Récupération des entrées vMix avec une requête simple")

            # Utilisation de l'API de base vMix sans spécifier de fonction particulière
            # Cela renvoie l'état complet de vMix en XML
            url = f"http://{self.host}:{self.port}/api/"
            logger.info(f"URL de requête simple: {url}")

            response = requests.get(url, timeout=5)
            logger.info(f"Code de réponse: {response.status_code}")

            if response.status_code == 200:
                # Log de la réponse pour debug (limité aux premiers caractères)
                response_preview = response.text[:200] + "..." if len(response.text) > 200 else response.text
                logger.info(f"Contenu de la réponse (aperçu): {response_preview}")

                try:
                    # Analyser la réponse XML
                    root = ET.fromstring(response.text)
                    inputs = []

                    # Dans l'API vMix standard, les inputs sont directement sous le nœud racine "vmix"
                    # en tant qu'éléments "input"
                    for input_elem in root.findall('./inputs/input'):
                        # Récupérer les attributs avec gestion des valeurs par défaut
                        input_number = input_elem.get('number', '')
                        title = input_elem.get('title', '')

                        # Le type est parfois stocké comme attribut, parfois comme élément enfant
                        input_type = input_elem.get('type', '')
                        if not input_type and len(input_elem) > 0:
                            type_elem = input_elem.find('type')
                            if type_elem is not None and type_elem.text:
                                input_type = type_elem.text

                        if not title and len(input_elem) > 0:
                            title_elem = input_elem.find('title')
                            if title_elem is not None and title_elem.text:
                                title = title_elem.text

                        # Si nous n'avons toujours pas de titre, utilisez un titre par défaut
                        if not title:
                            title = f"Entrée {input_number}"

                        logger.info(f"Input détecté - Numéro: {input_number}, Titre: {title}, Type: {input_type}")

                        # Déterminer la catégorie principale de l'entrée en fonction de son type ou d'autres attributs
                        category = self._determine_input_category(input_elem, input_type)

                        input_data = {
                            'id': input_number,
                            'name': title,
                            'type': input_type,
                            'category': category,
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

    def _determine_input_category(self, input_elem, input_type):
        """Détermine la catégorie d'une entrée en fonction de son type et d'autres attributs"""
        input_type_lower = input_type.lower() if input_type else ''

        # Extraction du titre pour aider à la classification
        title = input_elem.get('title', '')
        title_lower = title.lower() if title else ''

        # Vérification spécifique pour les types courants dans vMix
        if input_type_lower == 'blank' or title_lower == 'blank':
            logger.info(f"Entrée {title} de type 'Blank' classifiée comme 'blank'")
            return 'blank'

        # Mots-clés pour détecter les caméras
        camera_keywords = ['camera', 'webcam', 'capture', 'video capture', 'cam', 'caméra', 'webcamera']

        # Mots-clés pour les vidéos
        video_keywords = ['video', 'movie', 'mp4', 'avi', 'mov', 'film', 'clip', 'vidéo']

        # Mots-clés pour l'audio
        audio_keywords = ['audio', 'sound', 'mic', 'microphone', 'son', 'micro']

        # Vérification des caméras basée sur le type
        if any(cam_type in input_type_lower for cam_type in camera_keywords):
            logger.info(f"Entrée {title} classifiée comme 'caméra' selon son type")
            return 'camera'

        # Vérification des caméras basée sur le titre
        if any(cam_type in title_lower for cam_type in camera_keywords):
            logger.info(f"Entrée {title} classifiée comme 'caméra' selon son titre")
            return 'camera'

        # Vérification des vidéos
        if any(vid_type in input_type_lower for vid_type in video_keywords):
            logger.info(f"Entrée {title} classifiée comme 'vidéo' selon son type")
            return 'video'

        # Vérification des vidéos basée sur le titre
        if any(vid_type in title_lower for vid_type in video_keywords):
            logger.info(f"Entrée {title} classifiée comme 'vidéo' selon son titre")
            return 'video'

        # Vérification des sources audio
        if any(audio_type in input_type_lower for audio_type in audio_keywords):
            logger.info(f"Entrée {title} classifiée comme 'audio' selon son type")
            return 'audio'

        # Vérification des sources audio basée sur le titre
        if any(audio_type in title_lower for audio_type in audio_keywords):
            logger.info(f"Entrée {title} classifiée comme 'audio' selon son titre")
            return 'audio'

        # Fallback sur d'autres indicateurs - vérification des attributs
        for attr_name, attr_value in input_elem.attrib.items():
            if attr_value and isinstance(attr_value, str):
                attr_value_lower = attr_value.lower()

                # Vérifier si un attribut contient des mots-clés
                if any(cam_type in attr_value_lower for cam_type in camera_keywords):
                    logger.info(f"Entrée {title} classifiée comme 'caméra' selon l'attribut {attr_name}")
                    return 'camera'
                elif any(vid_type in attr_value_lower for vid_type in video_keywords):
                    logger.info(f"Entrée {title} classifiée comme 'vidéo' selon l'attribut {attr_name}")
                    return 'video'
                elif any(audio_type in attr_value_lower for audio_type in audio_keywords):
                    logger.info(f"Entrée {title} classifiée comme 'audio' selon l'attribut {attr_name}")
                    return 'audio'

        # Par défaut pour les autres types
        logger.info(f"Entrée {title} de type {input_type} non reconnue, classifiée par défaut comme 'other'")
        return 'other'

    def set_overlay(self, input_number, overlay_number, state=True):
        """Contrôle les overlays vMix"""
        action = "SetOverlayOn" if state else "SetOverlayOff"
        logger.info(f"Configuration overlay: {action}, input={input_number}, overlay={overlay_number}")
        return self.send_command(action, input=input_number, overlay=overlay_number)

    def set_text(self, input_number, text, layer=0):
        """Modifie le texte d'un titre vMix"""
        logger.info(f"Modification texte: input={input_number}, layer={layer}, texte={text[:20]}...")
        return self.send_command("SetText", input=input_number, value=text, selectedIndex=layer)

    def control_streaming(self, action="Start"):
        """Contrôle le streaming (Start/Stop)"""
        logger.info(f"Contrôle streaming: {action}")
        return self.send_command(f"{action}Streaming")

    def send_command(self, function, **params):
        """Envoie une commande à l'API vMix avec les paramètres fournis"""
        url = urljoin(self.base_url, f"?Function={function}")

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

    def refresh_predefined_inputs(self):
        """Rafraîchit la liste des entrées prédéfinies en les détectant depuis vMix"""
        try:
            logger.info("Détection des entrées prédéfinies dans vMix...")

            # Réinitialiser les listes
            for category in self.predefined_inputs:
                self.predefined_inputs[category] = []

            # Récupérer toutes les entrées actuelles
            inputs = self.get_inputs()

            # Catégoriser les entrées
            for input_data in inputs:
                category = input_data.get('category', 'other')
                if category in self.predefined_inputs:
                    self.predefined_inputs[category].append(input_data)
                    logger.info(f"Entrée prédéfinie détectée: {input_data['name']} (Type: {category}, ID: {input_data['id']})")

            # Log du résultat
            for category, inputs_list in self.predefined_inputs.items():
                logger.info(f"Entrées prédéfinies de type '{category}': {len(inputs_list)}")

            return True

        except Exception as e:
            logger.error(f"Erreur lors de la détection des entrées prédéfinies: {e}", exc_info=True)
            return False

    def get_available_sources(self):
        """Récupère la liste des sources disponibles pour de nouveaux inputs dans vMix.
           Dans cette version adaptée, nous utilisons les entrées existantes au lieu d'essayer
           d'en ajouter de nouvelles.
        """
        # Rafraîchir les entrées prédéfinies
        self.refresh_predefined_inputs()

        # Créer la structure de retour compatible avec le code existant
        sources = {
            'camera': [],
            'video': [],
            'audio': [],
            'blank': []
        }

        # Ajouter les entrées prédéfinies aux sources disponibles
        for category in sources:
            if category in self.predefined_inputs:
                # Ajouter chaque entrée prédéfinie comme source disponible
                for input_data in self.predefined_inputs[category]:
                    sources[category].append({
                        'id': input_data['id'],
                        'name': input_data['name'],
                        'type': input_data['type'],
                        'source': 'predefined'
                    })

        # Si aucune entrée n'est trouvée dans vMix, ajouter des entrées fictives pour la compatibilité
        if not any(sources.values()):
            logger.warning("Aucune entrée détectée dans vMix. Ajout d'entrées fictives pour la compatibilité.")
            # Ajouter des entrées fictives qui indiqueront à l'utilisateur de créer des entrées manuellement
            sources['blank'].append({
                'id': 'manual_blank',
                'name': 'CRÉEZ UNE ENTRÉE BLANK DANS VMIX',
                'type': 'Blank',
                'source': 'manual'
            })
            sources['camera'].append({
                'id': 'manual_camera',
                'name': 'CRÉEZ UNE ENTRÉE CAMÉRA DANS VMIX',
                'type': 'Capture',
                'source': 'manual'
            })

        logger.info("Récupération des sources disponibles terminée")
        return sources

    def use_predefined_input(self, source_id, input_type='camera'):
        """Utilise une entrée prédéfinie au lieu d'en ajouter une nouvelle
        Args:
            source_id: Identifiant de l'entrée à utiliser
            input_type: Type d'entrée (pour la compatibilité avec le code existant)
        Returns:
            tuple: (succès, message d'erreur)
        """
        try:
            logger.info(f"Utilisation de l'entrée prédéfinie: {source_id}")

            # Vérifier que l'entrée existe
            all_inputs = self.get_inputs()
            input_exists = any(input_data['id'] == source_id for input_data in all_inputs)

            if input_exists:
                # L'entrée existe, nous pouvons la prévisualiser pour montrer qu'elle est sélectionnée
                response = requests.get(f"{self.base_url}?Function=PreviewInput&Input={source_id}", timeout=5)
                if response.status_code == 200:
                    logger.info(f"Entrée {source_id} prévisualisée avec succès")
                    return True, ""
                else:
                    return False, f"Erreur HTTP: {response.status_code}"
            else:
                logger.error(f"L'entrée {source_id} n'existe pas dans vMix")
                return False, f"L'entrée {source_id} n'existe pas dans vMix"

        except Exception as e:
            logger.error(f"Erreur lors de l'utilisation de l'entrée prédéfinie: {str(e)}", exc_info=True)
            return False, str(e)

    # Méthodes de compatibilité qui utilisent use_predefined_input à la place
    def add_capture_input(self, source_id, source_name=""):
        """Version compatible qui utilise use_predefined_input"""
        return self.use_predefined_input(source_id, 'camera')

    def add_video_input(self, source_id, source_name=""):
        """Version compatible qui utilise use_predefined_input"""
        return self.use_predefined_input(source_id, 'video')

    def add_blank_input(self, source_name="Blank"):
        """Version compatible qui utilise use_predefined_input pour la première entrée blank disponible"""
        if self.predefined_inputs['blank']:
            return self.use_predefined_input(self.predefined_inputs['blank'][0]['id'], 'blank')
        else:
            logger.error("Aucune entrée blank prédéfinie disponible")
            return False, "Aucune entrée blank prédéfinie disponible"

    def cut_to_input(self, input_number):
        """Change l'entrée active en mode CUT"""
        logger.info(f"Changement d'input (CUT): {input_number}")
        return self.send_command("Cut", input=input_number)

    def transition_to_input(self, input_number, duration=500, effect="Fade"):
        """Change l'entrée active avec une transition"""
        logger.info(f"Transition vers input {input_number} avec effet {effect} (durée: {duration}ms)")
        # Définir d'abord le type de transition et sa durée
        self.send_command("SetTransitionDuration", value=duration)
        self.send_command("SetTransitionEffect", value=effect)
        # Effectuer la transition
        return self.send_command("Transition", input=input_number)

    def toggle_audio(self, input_number, mute=None):
        """Active ou désactive l'audio d'une entrée spécifique.
        Si mute=None, inverse l'état actuel (toggle).
        Si mute=True, coupe l'audio.
        Si mute=False, active l'audio.
        """
        if mute is None:
            logger.info(f"Toggle audio pour input {input_number}")
            return self.send_command("AudioToggle", input=input_number)
        elif mute:
            logger.info(f"Mute audio pour input {input_number}")
            return self.send_command("AudioOff", input=input_number)
        else:
            logger.info(f"Unmute audio pour input {input_number}")
            return self.send_command("AudioOn", input=input_number)

    def adjust_audio_volume(self, input_number, volume):
        """Ajuste le volume d'une entrée audio (valeur entre 0 et 100)"""
        logger.info(f"Ajustement volume pour input {input_number} à {volume}%")
        # L'API vMix attend une valeur entre 0 et 100
        volume = max(0, min(100, volume))
        return self.send_command("SetVolume", input=input_number, value=volume)
        
    # Méthodes pour la gestion des replays
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