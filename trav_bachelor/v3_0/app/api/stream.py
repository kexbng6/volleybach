from flask import Blueprint, request, jsonify, current_app
import os
import json
from werkzeug.utils import secure_filename
import uuid
import logging

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('stream_api')

stream_bp = Blueprint('stream', __name__)

# Chemin pour les données de configuration
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'stream_config.json')
THUMBNAILS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'thumbnails')

# Créer les répertoires s'ils n'existent pas
os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
os.makedirs(THUMBNAILS_DIR, exist_ok=True)

# Initialiser le fichier de configuration s'il n'existe pas
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({
            'title': '',
            'service': 'custom',
            'quality': '1080p30',
            'rtmpUrl': '',
            'streamKey': '',
            'description': '',
            'autoStartRecording': False,
            'autoStartStreaming': False,
            'thumbnailUrl': None
        }, f, indent=2)

@stream_bp.route('/config', methods=['GET'])
def get_stream_config():
    """Récupérer la configuration du streaming"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

            # Ne pas renvoyer la clé de stream complète pour des raisons de sécurité
            if 'streamKey' in config and config['streamKey']:
                config['streamKey'] = '••••••••••••••••'

            return jsonify({"config": config})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la configuration du streaming: {str(e)}")
        return jsonify({"error": "Erreur lors de la récupération de la configuration"}), 500

@stream_bp.route('/config', methods=['POST'])
def save_stream_config():
    """Enregistrer la configuration du streaming"""
    try:
        # Récupérer la configuration existante
        with open(CONFIG_FILE, 'r') as f:
            existing_config = json.load(f)

        # Mettre à jour les champs simples
        for field in ['title', 'service', 'quality', 'rtmpUrl', 'description']:
            if field in request.form:
                existing_config[field] = request.form[field]

        # Traiter les booléens
        existing_config['autoStartRecording'] = 'autoStartRecording' in request.form and request.form['autoStartRecording'].lower() == 'true'
        existing_config['autoStartStreaming'] = 'autoStartStreaming' in request.form and request.form['autoStartStreaming'].lower() == 'true'

        # Traiter la clé de stream (ne pas écraser si vide)
        if 'streamKey' in request.form and request.form['streamKey'] and request.form['streamKey'] != '••••••••••••••••':
            existing_config['streamKey'] = request.form['streamKey']

        # Traiter la miniature si fournie
        if 'thumbnail' in request.files and request.files['thumbnail'].filename:
            thumbnail_file = request.files['thumbnail']

            # Sécuriser le nom de fichier
            filename = secure_filename(thumbnail_file.filename)
            # Ajouter un identifiant unique pour éviter les collisions
            unique_filename = f"{uuid.uuid4()}_{filename}"
            # Chemin complet
            filepath = os.path.join(THUMBNAILS_DIR, unique_filename)

            # Enregistrer le fichier
            thumbnail_file.save(filepath)

            # Mettre à jour l'URL dans la configuration
            existing_config['thumbnailUrl'] = f"/static/thumbnails/{unique_filename}"

            # Créer un lien symbolique vers le dossier static si nécessaire
            static_thumbnails_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'thumbnails')
            os.makedirs(static_thumbnails_dir, exist_ok=True)

            # Copier le fichier dans le dossier static
            import shutil
            shutil.copy2(filepath, os.path.join(static_thumbnails_dir, unique_filename))

        # Enregistrer la configuration mise à jour
        with open(CONFIG_FILE, 'w') as f:
            json.dump(existing_config, f, indent=2)

        return jsonify({
            "message": "Configuration du streaming enregistrée avec succès",
            "thumbnailUrl": existing_config.get('thumbnailUrl')
        })
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de la configuration du streaming: {str(e)}")
        return jsonify({"error": f"Erreur lors de l'enregistrement de la configuration: {str(e)}"}), 500

@stream_bp.route('/start', methods=['POST'])
def start_streaming():
    """Démarrer le streaming"""
    try:
        # Récupérer la configuration
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        # Importer le gestionnaire vMix
        from ..core.vmix_manager import VMixManager
        vmix_manager = VMixManager()

        # Vérifier la connexion à vMix
        if not vmix_manager.check_connection():
            return jsonify({"error": "Impossible de se connecter à vMix"}), 500

        # Démarrer le streaming
        success = vmix_manager.start_streaming()

        if success:
            return jsonify({"message": "Streaming démarré avec succès"})
        else:
            return jsonify({"error": "Erreur lors du démarrage du streaming"}), 500
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du streaming: {str(e)}")
        return jsonify({"error": f"Erreur lors du démarrage du streaming: {str(e)}"}), 500

@stream_bp.route('/stop', methods=['POST'])
def stop_streaming():
    """Arrêter le streaming"""
    try:
        # Importer le gestionnaire vMix
        from ..core.vmix_manager import VMixManager
        vmix_manager = VMixManager()

        # Vérifier la connexion à vMix
        if not vmix_manager.check_connection():
            return jsonify({"error": "Impossible de se connecter à vMix"}), 500

        # Arrêter le streaming
        success = vmix_manager.start_streaming("Stop")

        if success:
            return jsonify({"message": "Streaming arrêté avec succès"})
        else:
            return jsonify({"error": "Erreur lors de l'arrêt du streaming"}), 500
    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt du streaming: {str(e)}")
        return jsonify({"error": f"Erreur lors de l'arrêt du streaming: {str(e)}"}), 500

@stream_bp.route('/thumbnail/toggle', methods=['POST'])
def toggle_thumbnail():
    """Activer/désactiver la miniature du match"""
    try:
        data = request.json
        show = data.get('show', False)

        # Mettre à jour la configuration
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        config['thumbnailVisible'] = show

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

        # Importer le gestionnaire vMix
        from ..core.vmix_manager import VMixManager
        vmix_manager = VMixManager()

        # Récupérer l'input pour la miniature (par défaut, on utilise "Thumbnail")
        thumbnail_input = data.get('input', 'Thumbnail')
        overlay_number = data.get('overlay', 1)

        # Activer ou désactiver la miniature
        if show:
            success = vmix_manager.set_overlay(thumbnail_input, overlay_number, True)
            message = "Miniature activée"
        else:
            success = vmix_manager.set_overlay(thumbnail_input, overlay_number, False)
            message = "Miniature désactivée"

        if success:
            return jsonify({
                "success": True,
                "message": message
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Erreur lors de la {message.lower()}"
            }), 500
    except Exception as e:
        logger.error(f"Erreur lors de la manipulation de la miniature: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erreur: {str(e)}"
        }), 500

@stream_bp.route('/upload-thumbnail', methods=['POST'])
def upload_thumbnail():
    """Télécharger une miniature"""
    try:
        if 'thumbnail' not in request.files or not request.files['thumbnail'].filename:
            return jsonify({
                "success": False,
                "message": "Aucun fichier fourni"
            }), 400

        thumbnail_file = request.files['thumbnail']

        # Vérifier le type de fichier
        if not thumbnail_file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return jsonify({
                "success": False,
                "message": "Format de fichier non supporté. Utilisez PNG, JPG, JPEG ou GIF."
            }), 400

        # Récupérer la configuration existante
        with open(CONFIG_FILE, 'r') as f:
            existing_config = json.load(f)

        # Supprimer l'ancienne miniature si elle existe
        if 'thumbnailUrl' in existing_config and existing_config['thumbnailUrl']:
            try:
                old_filename = os.path.basename(existing_config['thumbnailUrl'])
                old_filepath = os.path.join(THUMBNAILS_DIR, old_filename)
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)

                # Supprimer également du dossier static
                static_thumbnails_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'thumbnails')
                old_static_filepath = os.path.join(static_thumbnails_dir, old_filename)
                if os.path.exists(old_static_filepath):
                    os.remove(old_static_filepath)
            except Exception as e:
                logger.warning(f"Erreur lors de la suppression de l'ancienne miniature: {str(e)}")

        # Sécuriser le nom de fichier
        filename = secure_filename(thumbnail_file.filename)
        # Ajouter un identifiant unique pour éviter les collisions
        unique_filename = f"{uuid.uuid4()}_{filename}"
        # Chemin complet
        filepath = os.path.join(THUMBNAILS_DIR, unique_filename)

        # Enregistrer le fichier
        thumbnail_file.save(filepath)

        # Mettre à jour l'URL dans la configuration
        existing_config['thumbnailUrl'] = f"/static/thumbnails/{unique_filename}"

        # Créer un lien symbolique vers le dossier static si nécessaire
        static_thumbnails_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'thumbnails')
        os.makedirs(static_thumbnails_dir, exist_ok=True)

        # Copier le fichier dans le dossier static
        import shutil
        shutil.copy2(filepath, os.path.join(static_thumbnails_dir, unique_filename))

        # Enregistrer la configuration mise à jour
        with open(CONFIG_FILE, 'w') as f:
            json.dump(existing_config, f, indent=2)

        return jsonify({
            "success": True,
            "message": "Miniature téléchargée avec succès",
            "thumbnailUrl": existing_config['thumbnailUrl']
        })
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement de la miniature: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erreur lors du téléchargement de la miniature: {str(e)}"
        }), 500

@stream_bp.route('/remove-thumbnail', methods=['POST'])
def remove_thumbnail():
    """Supprimer la miniature actuelle"""
    try:
        # Récupérer la configuration existante
        with open(CONFIG_FILE, 'r') as f:
            existing_config = json.load(f)

        # Vérifier si une miniature existe
        if 'thumbnailUrl' not in existing_config or not existing_config['thumbnailUrl']:
            return jsonify({
                "success": False,
                "message": "Aucune miniature à supprimer"
            }), 400

        # Supprimer le fichier
        try:
            filename = os.path.basename(existing_config['thumbnailUrl'])
            filepath = os.path.join(THUMBNAILS_DIR, filename)
            if os.path.exists(filepath):
                os.remove(filepath)

            # Supprimer également du dossier static
            static_thumbnails_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'thumbnails')
            static_filepath = os.path.join(static_thumbnails_dir, filename)
            if os.path.exists(static_filepath):
                os.remove(static_filepath)
        except Exception as e:
            logger.warning(f"Erreur lors de la suppression du fichier de miniature: {str(e)}")

        # Mettre à jour la configuration
        existing_config['thumbnailUrl'] = None
        existing_config['thumbnailVisible'] = False

        # Enregistrer la configuration mise à jour
        with open(CONFIG_FILE, 'w') as f:
            json.dump(existing_config, f, indent=2)

        # Désactiver la miniature dans vMix si elle était activée
        try:
            from ..core.vmix_manager import VMixManager
            vmix_manager = VMixManager()
            vmix_manager.set_overlay('Thumbnail', 1, False)
        except Exception as e:
            logger.warning(f"Erreur lors de la désactivation de la miniature dans vMix: {str(e)}")

        return jsonify({
            "success": True,
            "message": "Miniature supprimée avec succès"
        })
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de la miniature: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erreur lors de la suppression de la miniature: {str(e)}"
        }), 500

@stream_bp.route('/update-score', methods=['POST'])
def update_score():
    """Mettre à jour le score dans vMix"""
    try:
        data = request.json
        
        # Vérifier si les données nécessaires sont présentes
        if not data or 'teamA' not in data or 'teamB' not in data:
            return jsonify({"status": "error", "message": "Données incomplètes"}), 400
        
        # Récupérer les informations des équipes
        team_a = data['teamA']
        team_b = data['teamB']
        
        # Vérifier si vmix_manager est disponible dans l'application
        if not hasattr(current_app, 'vmix_manager'):
            from app.core.vmix_manager import VMixManager
            current_app.vmix_manager = VMixManager()
        
        vmix_manager = current_app.vmix_manager
        
        # Mettre à jour le scoreboard dans vMix
        # Le title_input est "scoreboard" pour scoreboard.gtzip
        result = vmix_manager.update_scoreboard(
            team_a_name=team_a.get('name', 'Équipe A'),
            team_b_name=team_b.get('name', 'Équipe B'),
            score_a=team_a.get('score', 0),
            score_b=team_b.get('score', 0),
            sets_a=team_a.get('sets', 0),
            sets_b=team_b.get('sets', 0),
            title_input="scoreboard"
        )
        
        if result:
            logger.info(f"Score mis à jour: {team_a.get('name')} {team_a.get('score')}-{team_b.get('score')} {team_b.get('name')}, sets: {team_a.get('sets')}-{team_b.get('sets')}")
            return jsonify({"status": "success", "message": "Score mis à jour avec succès"})
        else:
            logger.error("Échec de la mise à jour du score dans vMix")
            return jsonify({"status": "error", "message": "Échec de la mise à jour du score"}), 500
    
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du score: {str(e)}")
        return jsonify({"status": "error", "message": f"Erreur: {str(e)}"}), 500
