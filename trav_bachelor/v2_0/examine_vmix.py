import requests
import xml.dom.minidom
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('vmix_examiner')

# Configuration
vmix_api_url = "http://127.0.0.1:8088/api/"
save_xml_to = "vmix_structure.xml"
save_devices_to = "vmix_devices.xml"
save_json_to = "vmix_structure.json"

def pretty_xml(xml_string):
    """Formate un string XML de façon lisible"""
    try:
        dom = xml.dom.minidom.parseString(xml_string)
        return dom.toprettyxml()
    except Exception as e:
        logger.error(f"Erreur lors du formatage XML: {e}")
        return xml_string

def get_vmix_structure():
    """Récupère la structure complète de vMix et l'enregistre dans un fichier"""
    try:
        logger.info(f"Connexion à l'API vMix: {vmix_api_url}")
        response = requests.get(vmix_api_url, timeout=5)

        if response.status_code == 200:
            logger.info("Connexion réussie, récupération de la structure vMix")

            # Enregistrer le XML brut
            with open(save_xml_to, 'w', encoding='utf-8') as file:
                pretty = pretty_xml(response.text)
                file.write(pretty)
                logger.info(f"Structure XML enregistrée dans {save_xml_to}")

            # Tenter de convertir en JSON pour une analyse plus facile
            try:
                import xmltodict
                xml_dict = xmltodict.parse(response.text)
                with open(save_json_to, 'w', encoding='utf-8') as file:
                    json.dump(xml_dict, file, indent=2)
                    logger.info(f"Structure convertie en JSON et enregistrée dans {save_json_to}")
            except ImportError:
                logger.warning("Module xmltodict non trouvé, la conversion en JSON n'a pas été effectuée")
                logger.info("Vous pouvez l'installer avec: pip install xmltodict")
            except Exception as e:
                logger.error(f"Erreur lors de la conversion en JSON: {e}")
        else:
            logger.error(f"Erreur HTTP: {response.status_code}")
    except Exception as e:
        logger.error(f"Erreur: {str(e)}")

def get_vmix_devices():
    """Récupère la liste des périphériques disponibles"""
    try:
        url = f"{vmix_api_url}?Function=ListDevices"
        logger.info(f"Récupération des périphériques: {url}")
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            with open(save_devices_to, 'w', encoding='utf-8') as file:
                pretty = pretty_xml(response.text)
                file.write(pretty)
                logger.info(f"Liste des périphériques enregistrée dans {save_devices_to}")
        else:
            logger.error(f"Erreur HTTP: {response.status_code}")
    except Exception as e:
        logger.error(f"Erreur: {str(e)}")

def test_add_blank():
    """Teste différentes méthodes pour ajouter un blank input"""
    methods = [
        {"url": f"{vmix_api_url}?Function=AddInput&Value=Blank", "description": "Value=Blank"},
        {"url": f"{vmix_api_url}?Function=AddInput&Input=Blank", "description": "Input=Blank"},
        {"url": f"{vmix_api_url}?Function=AddInput&Value=Blank&Mix=0", "description": "Value=Blank avec Mix=0"},
        {"url": f"{vmix_api_url}?Function=AddInput&Type=Blank", "description": "Type=Blank"}
    ]

    logger.info("Test des différentes méthodes pour ajouter un input Blank")

    for method in methods:
        try:
            logger.info(f"Essai de la méthode: {method['description']}")
            logger.info(f"URL: {method['url']}")

            response = requests.get(method['url'], timeout=5)
            logger.info(f"Code de réponse: {response.status_code}")
            logger.info(f"Contenu: {response.text}")

            if response.status_code == 200:
                logger.info(f"SUCCÈS avec la méthode: {method['description']}")
                return method

        except Exception as e:
            logger.error(f"Erreur avec la méthode {method['description']}: {str(e)}")

    logger.error("Toutes les méthodes ont échoué")
    return None

def test_various_commands():
    """Teste différentes commandes API pour comprendre ce qui fonctionne et ce qui ne fonctionne pas"""
    commands = [
        {"url": f"{vmix_api_url}?Function=PreviewInput&Input=1", "description": "Prévisualisation de l'input 1"},
        {"url": f"{vmix_api_url}?Function=PreviewInput&Input=2", "description": "Prévisualisation de l'input 2"},
        {"url": f"{vmix_api_url}?Function=CutDirect&Input=1", "description": "Cut direct vers input 1"},
        {"url": f"{vmix_api_url}?Function=SetOutputFullscreen&Value=On", "description": "Activer plein écran"},
        {"url": f"{vmix_api_url}?Function=SetOutputFullscreen&Value=Off", "description": "Désactiver plein écran"},
        {"url": f"{vmix_api_url}?Function=OpenInput&Value=Blank", "description": "Ouvrir un input blank (alternative à AddInput)"},
        {"url": f"{vmix_api_url}?Function=AddInputBrowser&Value=https://www.google.com", "description": "Ajouter un navigateur web"},
        {"url": f"{vmix_api_url}?Function=AddInput&Input=VirtualSet", "description": "Ajouter un virtual set"}
    ]

    logger.info("\n=== Test des différentes commandes API vMix ===")
    results = {"success": [], "failure": []}

    for cmd in commands:
        try:
            logger.info(f"\nEssai de la commande: {cmd['description']}")
            logger.info(f"URL: {cmd['url']}")

            response = requests.get(cmd['url'], timeout=5)
            logger.info(f"Code de réponse: {response.status_code}")
            logger.info(f"Contenu: {response.text}")

            if response.status_code == 200 and "Invalid Parameters" not in response.text:
                logger.info(f"SUCCÈS: {cmd['description']}")
                results["success"].append(cmd)
            else:
                logger.info(f"ÉCHEC: {cmd['description']}")
                results["failure"].append(cmd)

        except Exception as e:
            logger.error(f"Erreur avec la commande {cmd['description']}: {str(e)}")
            results["failure"].append(cmd)

    # Afficher un résumé
    logger.info("\n=== Résumé des tests ===")
    logger.info(f"Commandes réussies: {len(results['success'])}")
    for cmd in results['success']:
        logger.info(f"  - {cmd['description']}")

    logger.info(f"\nCommandes échouées: {len(results['failure'])}")
    for cmd in results['failure']:
        logger.info(f"  - {cmd['description']}")

    return results

if __name__ == "__main__":
    print("=== Outil d'analyse de la structure vMix ===")
    print("Cet outil va examiner votre configuration vMix actuelle")
    print("et enregistrer les résultats dans des fichiers pour analyse.")
    print()

    choice = input("Que souhaitez-vous faire?\n"
                   "1. Examiner la structure complète de vMix\n"
                   "2. Récupérer la liste des périphériques\n"
                   "3. Tester différentes méthodes pour ajouter un input Blank\n"
                   "4. Tester diverses commandes API vMix\n"
                   "5. Tout faire\n"
                   "Votre choix (1-5): ")

    if choice == "1":
        get_vmix_structure()
    elif choice == "2":
        get_vmix_devices()
    elif choice == "3":
        test_add_blank()
    elif choice == "4":
        test_various_commands()
    elif choice == "5":
        get_vmix_structure()
        get_vmix_devices()
        test_add_blank()
        test_various_commands()
    else:
        print("Choix non reconnu")
