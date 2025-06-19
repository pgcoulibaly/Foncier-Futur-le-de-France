from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from functools import lru_cache
from typing import Tuple
import time
import json
from concurrent.futures import ThreadPoolExecutor
from core.geocod import geocode_ban, get_biens_proches
from core.llm_assistant import analyse_biens_par_llm_stream  # Version streaming
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="API Immobilier Optimisée", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"],
)

param = {}

# Configuration optimisée de la base de données
DATABASE_URL = os.getenv("NEON_DB_URL")
param["engine"] = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

logging.basicConfig(level=logging.INFO)
param["logger"] = logging.getLogger(__name__)

@lru_cache(maxsize=1000)
def geocode_cached(adresse: str) -> Tuple[float, float]:
    """Géocodage avec cache pour éviter les appels répétés"""
    try:
        lat, lon = geocode_ban(adresse)
        return lat, lon
    except Exception as e:
        param["logger"].error(f"Erreur géocodage pour {adresse}: {e}")
        raise HTTPException(status_code=400, detail=f"Impossible de géocoder l'adresse: {adresse}")

# Endpoint pour les données de base (sans analyse LLM)
@app.get("/biens_proches")
async def biens_proches(
    adresse: str = Query(..., description="Adresse en Île-de-France"),
    rayon_m: int = Query(500, ge=100, le=10000, description="Rayon en mètres")
):
    """
    Endpoint pour récupérer les biens immobiliers proches (données de base uniquement)
    """
    start_time = time.time()
    
    try:
        # 1. Géocodage avec cache
        lat, lon = geocode_cached(adresse)
        param["logger"].info(f"Géocodage: {adresse} -> ({lat}, {lon})")
        
        # 2. Recherche des biens
        biens = get_biens_proches(lat, lon, rayon_m, param)
        
        if not biens:
            return {
                "biens_proches": [],
                "stats": {
                    "nb_biens": 0,
                    "temps_execution": round(time.time() - start_time, 2)
                }
            }
        
        # 3. Calcul des statistiques de base
        stats = {
            "nb_biens": len(biens),
            "prix_moyen": round(sum(b["prix_m2"] for b in biens if b["prix_m2"]) / len([b for b in biens if b["prix_m2"]]),2) if biens else 0,
            "surface_moyenne": round(sum(b["surface_reelle_bati"] for b in biens if b["surface_reelle_bati"]) / len([b for b in biens if b["surface_reelle_bati"]]),2) if biens else 0,
            "distance_max": max(b["distance_m"] for b in biens) if biens else 0,
            "temps_execution": round(time.time() - start_time, 2)
        }
        
        return {
            "biens_proches": biens,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        param["logger"].error(f"Erreur inattendue: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

# Nouveau endpoint pour l'analyse LLM en streaming
@app.get("/analyse_stream")
async def analyse_stream(
    adresse: str = Query(..., description="Adresse en Île-de-France"),
    rayon_m: int = Query(500, ge=100, le=1000, description="Rayon en mètres")
):
    """
    Endpoint pour l'analyse LLM en streaming
    """
    try:
        # Récupération des biens (réutilise la logique existante)
        lat, lon = geocode_cached(adresse)
        biens = get_biens_proches(lat, lon, rayon_m, param)
        
        if not biens:
            async def empty_stream():
                error_message = "Aucun bien trouvé"
                yield f"data: {json.dumps({'type': 'error', 'content': error_message})}\n\n"
            
            return StreamingResponse(
                empty_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                }
            )
        
        # Générateur pour le streaming
        async def generate_analysis():
            try:
                start_message = "Reflexion..."
                yield f"data: {json.dumps({'type': 'start', 'content': start_message})}\n\n"
                
                # Appel de la fonction d'analyse streaming
                async for chunk in analyse_biens_par_llm_stream(biens, rayon_m, param):
                    if chunk:
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                
                end_message = "Analyse terminée"
                yield f"data: {json.dumps({'type': 'end', 'content': end_message})}\n\n"
                
            except Exception as e:
                param["logger"].error(f"Erreur analyse streaming: {e}")
                error_message = "Erreur lors de l'analyse"
                yield f"data: {json.dumps({'type': 'error', 'content': error_message})}\n\n"
        
        return StreamingResponse(
            generate_analysis(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
        
    except Exception as e:
        param["logger"].error(f"Erreur inattendue streaming: {e}")
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