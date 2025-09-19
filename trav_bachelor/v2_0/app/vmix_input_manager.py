from flask import current_app
import requests
from .vmix_manager import VmixManager

def get_vmix_manager():
    """Récupère ou crée une instance de VmixManager"""
    if hasattr(current_app, 'vmix_manager'):
        return current_app.vmix_manager
    else:
        # Utiliser une configuration par défaut
        return VmixManager(host='127.0.0.1', port=8088)



def create_vmix_input(input_type, source):
    """
    Crée un nouvel input dans vMix
    Args:
        input_type: Type d'input (Video, Audio, Image, etc.)
        source: Chemin ou URL de la source
    """
    vmix_url = 'http://127.0.0.1:8088/api'
    params = {
        'Function': 'AddInput',
        'Value': source,
        'Input': input_type
    }
    try:
        response = requests.get(vmix_url, params=params)
        return {"success": response.status_code == 200}
    except Exception as e:
        return {"success": False, "message": str(e)}