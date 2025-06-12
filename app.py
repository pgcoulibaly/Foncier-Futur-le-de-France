import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Chargement de la variable d’environnement
load_dotenv()
db_url = os.getenv("NEON_DB_URL")
engine = create_engine(db_url)

# Titre
st.title("Carte de 1000 biens immobiliers aléatoires en Île-de-France (2024)")

# Requête SQL sécurisée : tirage aléatoire
random_query = """
    SELECT latitude, longitude, type_local, prix_m2
    FROM valeurs_foncieres_idf_2024
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 1000
"""

@st.cache_data
def load_random_data():
    with engine.connect() as conn:
        return pd.read_sql(text(random_query), conn)

# Chargement des données
df = load_random_data()

# Création de la carte centrée sur Paris
m = folium.Map(location=[48.85, 2.35], zoom_start=10)

# Ajout des points
for _, row in df.iterrows():
    popup = f"{row['type_local']} - {int(row['prix_m2'])} €/m²"
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=4,
        popup=popup,
        color="blue",
        fill=True,
    ).add_to(m)

# Affichage Streamlit
st_folium(m, width=800, height=600)
