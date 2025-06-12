import requests

def geocode_ban(adresse):
    url = "https://api-adresse.data.gouv.fr/search/"
    params = {'q': adresse, 'limit': 1}
    response = requests.get(url, params=params).json()
    
    if response['features']:
        coords = response['features'][0]['geometry']['coordinates']
        return coords[1], coords[0]  # lat, lon
    return None, None


