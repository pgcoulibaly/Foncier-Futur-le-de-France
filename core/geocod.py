import requests
from math import radians, sin, cos, sqrt, atan2
from sqlalchemy import text
import time
from typing import List, Dict
from fastapi import  HTTPException


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
    
    # Fonction optimisée pour calculer la distance avec filtrage SQL
def get_biens_proches(lat: float, lon: float, rayon_m: int,param: dict ) -> List[Dict]:
    """
    Récupération optimisée des biens avec filtrage géographique SQL
    """
    # Conversion du rayon en degrés approximatifs pour le pré-filtrage SQL
    # 1 degré ≈ 111 km, donc 1 km ≈ 0.009 degré
    rayon_deg = (rayon_m / 1000) * 0.009
    
    # Requête optimisée avec pré-filtrage géographique
    query = text("""
        SELECT 
            latitude, longitude, prix_m2, type_local, 
            date_mutation, surface_reelle_bati, id_mutation, 
            nombre_pieces_principales
        FROM valeurs_foncieres_idf_2024
        WHERE 
            latitude BETWEEN :lat_min AND :lat_max
            AND longitude BETWEEN :lon_min AND :lon_max
        ORDER BY 
            (latitude - :lat) * (latitude - :lat) + (longitude - :lon) * (longitude - :lon)
        LIMIT 1000
    """)
    params = {
        'lat': lat,
        'lon': lon,
        'lat_min': lat - rayon_deg,
        'lat_max': lat + rayon_deg,
        'lon_min': lon - rayon_deg,
        'lon_max': lon + rayon_deg
    }
    
    biens = []
    start_time = time.time()
    
    try:
        with param["engine"].connect() as conn:
            results = conn.execute(query, params)
            
            # Traitement des résultats avec calcul exact de distance
            for row in results:
                distance = haversine_distance(lat, lon, row.latitude, row.longitude)
                
                if distance <= rayon_m:
                    biens.append({
                        "latitude": float(row.latitude),
                        "longitude": float(row.longitude),
                        "prix_m2": float(row.prix_m2) ,
                        "type_local": row.type_local ,
                        "date_mutation": row.date_mutation ,
                        "surface_reelle_bati": float(row.surface_reelle_bati) ,
                        "id_mutation": row.id_mutation,
                        "nombre_pieces_principales": int(row.nombre_pieces_principales),
                        "distance_m": round(distance, 1)
                    })
            
            # Tri par distance
            biens.sort(key=lambda x: x['distance_m'])
            
        query_time = time.time() - start_time
        param["logger"].info(f"Requête DB exécutée en {query_time:.2f}s, {len(biens)} biens trouvés")
        
        return biens
        
    except Exception as e:
        param["logger"].error(f"Erreur lors de la requête DB: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche dans la base de données : {e}")


