from fastapi import FastAPI, Query
from sqlalchemy import create_engine, text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from core.geocod import geocode_ban, haversine_distance
from core.llm_assistant import analyse_biens_par_llm
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connexion DB
DATABASE_URL = os.getenv("NEON_DB_URL")
engine = create_engine(DATABASE_URL)
#together api key
TOGETHER_API_KEY =os.getenv("TOGETHER_API_KEY")



# Endpoint : Biens proches
@app.get("/biens_proches")
def biens_proches(adresse: str = Query(..., description="Adresse en ile de France"), rayon_m: int = 500):
    query = text("""
        SELECT latitude, longitude, prix_m2, type_local, date_mutation, surface_reelle_bati, id_mutation, nombre_pieces_principales
        FROM valeurs_foncieres_idf_2024
    """)
    lat, lon = geocode_ban(adresse)
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
                    "surface_reelle_bati": row.surface_reelle_bati,
                    "id_mutation": row.id_mutation,
                    "nombre_pieces_principales": row.nombre_pieces_principales,
                    "distance_m": d
                })
    
    # Appel de ta fonction d'analyse importée
    analyse = analyse_biens_par_llm(biens, rayon_m,TOGETHER_API_KEY)

    return {
        "biens_proches": biens,
        "analyse": analyse
    }
