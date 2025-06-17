from fastapi import FastAPI, Query, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from functools import lru_cache
from typing import  Tuple
import time
from concurrent.futures import ThreadPoolExecutor
from core.geocod import geocode_ban, get_biens_proches
from core.llm_assistant import analyse_biens_par_llm
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="API Immobilier Optimisée", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"],
)
param ={}

# Configuration optimisée de la base de données
DATABASE_URL = os.getenv("NEON_DB_URL")
param["engine"] = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Nombre de connexions dans le pool
    max_overflow=20,  # Connexions supplémentaires si nécessaire
    pool_pre_ping=True,  # Vérification de la connexion
    pool_recycle=3600,  # Recyclage des connexions toutes les heures
    echo=False  # Désactiver les logs SQL en production
)

logging.basicConfig(level=logging.INFO)
param["logger"] = logging.getLogger(__name__)

# Cache pour le géocodage (évite les appels répétés)
@lru_cache(maxsize=1000)
def geocode_cached(adresse: str) -> Tuple[float, float]:
    """Géocodage avec cache pour éviter les appels répétés"""
    try:
        lat, lon = geocode_ban(adresse)
        return lat, lon
    except Exception as e:
        param["logger"].error(f"Erreur géocodage pour {adresse}: {e}")
        raise HTTPException(status_code=400, detail=f"Impossible de géocoder l'adresse: {adresse}")

#Endpoint optimisé
@app.get("/biens_proches")
async def biens_proches(
    adresse: str = Query(..., description="Adresse en Île-de-France"),
    rayon_m: int = Query(500, ge=100, le=10000, description="Rayon en mètres")
):
    """
    Endpoint optimisé pour récupérer les biens immobiliers proches
    """
    start_time = time.time()
    
    try:
        # 1. Géocodage avec cache
        lat, lon = geocode_cached(adresse)
        param["logger"].info(f"Géocodage: {adresse} -> ({lat}, {lon})")
        
        # 2. Recherche des biens (optimisée)
        biens = get_biens_proches(lat, lon, rayon_m,param)
        
        if not biens:
            return {
                "biens_proches": [],
                "analyse": "Aucun bien trouvé dans ce rayon.",
                "stats": {
                    "nb_biens": 0,
                    "temps_execution": round(time.time() - start_time, 2)
                }
            }
        
       # 3. Analyse LLM en parallèle 
        with ThreadPoolExecutor(max_workers=1) as executor:
            future_analyse = executor.submit(analyse_biens_par_llm, biens, rayon_m, param)  
            
            stats = {
                "nb_biens": len(biens),
                "prix_moyen": round(sum(b["prix_m2"] for b in biens if b["prix_m2"]) / len([b for b in biens if b["prix_m2"]]),2) if biens else 0,
                "surface_moyenne": round(sum(b["surface_reelle_bati"] for b in biens if b["surface_reelle_bati"]) / len([b for b in biens if b["surface_reelle_bati"]]),2) if biens else 0,
                "distance_max": max(b["distance_m"] for b in biens) if biens else 0,
                "temps_execution": round(time.time() - start_time, 2)
            }
            
            # Récupération de l'analyse (avec timeout)
            try:
                analyse = future_analyse.result(timeout=10)  # Timeout de 10 secondes
                param["logger"].info(" Analyse LLM réussie")
            except Exception as e:
                param["logger"].warning(f" Timeout ou erreur analyse LLM: {e}")
                analyse = "Analyse en cours... Veuillez rafraîchir dans quelques instants."
               
                
        total_time = time.time() - start_time
        param["logger"].info(f"Requête complète exécutée en {total_time:.2f}s")
        
        
        return {
            "biens_proches": biens,
            "analyse": analyse,  
            "stats": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        param["logger"].error(f"Erreur inattendue: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

# Endpoint pour nettoyer le cache
@app.post("/clear_cache")
async def clear_cache():
    """Nettoie le cache de géocodage"""
    geocode_cached.cache_clear()
    return {"message": "Cache nettoyé avec succès"}

# Gestion des erreurs
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    param["logger"].error(f"Erreur globale: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Erreur interne du serveur"}
    )
    
    

