import requests
from math import radians, sin, cos, sqrt, atan2

def geocode_ban(adresse: str):
    """
    Géocode une adresse via l'API BAN.
    Retourne (latitude, longitude) ou (None, None) en cas d'erreur.
    """
    url = "https://api-adresse.data.gouv.fr/search/"
    params = {'q': adresse, 'limit': 1}
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get('features'):
            coords = data['features'][0]['geometry']['coordinates']
            return coords[1], coords[0]  # lat, lon
        else:
            print(f"Adresse introuvable : {adresse}")
            return None, None
        
    except requests.RequestException as e:
        print(f"Erreur réseau lors de la requête de géocodage : {e}")
        return None, None
    except ValueError as e:
        print(f"Erreur de parsing JSON : {e}")
        return None, None
    except (KeyError, IndexError) as e:
        print(f"Structure inattendue dans la réponse API : {e}")
        return None, None

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcule la distance en mètres entre deux points (Haversine).
    """
    try:
        R = 6371000  # rayon Terre en mètres
        phi1 = radians(lat1)
        phi2 = radians(lat2)
        dphi = radians(lat2 - lat1)
        dlambda = radians(lon2 - lon1)
        a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c
    except Exception as e:
        print(f"Erreur dans le calcul Haversine : {e}")
        return None
