from fastapi import FastAPI, Query
from sqlalchemy import create_engine, text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from core.geocod import geocode_ban, haversine_distance

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React local
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connexion DB
DATABASE_URL = os.getenv("NEON_DB_URL")
engine = create_engine(DATABASE_URL)

# Endpoint 1: Géocodage

@app.get("/geocode_ban")
def api_geocode_ban(adresse: str = Query(..., description="Adresse en France")):
    lat, lon = geocode_ban(adresse)
    if lat is None:
        return JSONResponse(status_code=404, content={"error": "Adresse introuvable"})
    return {"latitude": lat, "longitude": lon}

# Endpoint 2: Biens proches
@app.get("/biens_proches")
def biens_proches(lat: float, lon: float, rayon_m: int = 500):
    query = text("""
        SELECT latitude, longitude, prix_m2, type_local, date_mutation, surface_reelle_bati,id_mutation,nombre_pieces_principales
        FROM valeurs_foncieres_idf_2024
    """)
    
    with engine.connect() as conn:
        results = conn.execute(query)
        biens = []
        for row in results:
            d = haversine_distance(lat, lon, row.latitude, row.longitude)
            if d <= rayon_m:
                biens.append({
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "prix_m2": row.prix_m2,
                    "type_local": row.type_local,
                    "date_mutation": row.date_mutation,
                    "surface_reele_batie":row.surface_reelle_bati,
                    "id_mutation":row.id_mutation,
                    'nombre_pieces_principales':row.nombre_pieces_principales,
                    "distance_m": d
                })
    return biens


