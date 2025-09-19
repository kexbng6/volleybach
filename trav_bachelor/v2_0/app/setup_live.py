from flask import jsonify, request
from .routes import bp
from .vmix_team_updater import update_vmix_team

@bp.route('/api/vmix/load-teams', methods=['POST'])
def load_teams_to_vmix():
    data=request.json
    team_a_id = data.get('team_a_id')
    team_b_id = data.get('team_b_id')

    result_a = update_vmix_team(team_a_id, 'A')
    result_b = update_vmix_team(team_b_id, 'B')

    if result_a and result_b:
        return jsonify({
            "success": True,
            "message": "Équipes mises à jour avec succès",
            "team_a": result_a,
            "team_b": result_b
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": "Erreur lors de la mise à jour des équipes"
        }), 400

@bp.route('/api/vmix/load-thumbnail', methods=['POST'])
def load_thumbnail():
    """Charge la miniature du match dans vMix"""
    try:
        # URL de l'API vMix
        vmix_url = "http://localhost:8088/api/"

        # Supposons que l'overlay de la miniature est l'input 1
        # et que le flux du match est l'input 2
        request.get(f"{vmix_url}?Function=OverlayInput1In") # Todo change to the correct input number

        return jsonify({
            "success": True,
            "message": "Miniature chargée avec succès"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erreur lors du chargement de la miniature: {str(e)}"
        }), 500

@bp.route('/api/vmix/toggle-thumbnail', methods=['POST'])
def toggle_thumbnail():
    try:
        data = request.json
        show_thumbnail = data.get('show')

        # URL de l'API vMix
        vmix_url = "http://localhost:8088/api/"

        # Supposons que l'overlay de la miniature est l'input 1
        # et que le flux du match est l'input 2
        if show_thumbnail:
            # Afficher la miniature
            request.get(f"{vmix_url}?Function=OverlayInput1In") # Todo change to the correct input number
        else:
            # Masquer la miniature
            request.get(f"{vmix_url}?Function=OverlayInput1Out") # Todo change to the correct input number

        return jsonify({
            "success": True,
            "message": "État de la miniature mis à jour"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erreur lors de la mise à jour de la miniature: {str(e)}"
        }), 500


#def camera_switcher():

#def mute_audio():

#def replay_video():