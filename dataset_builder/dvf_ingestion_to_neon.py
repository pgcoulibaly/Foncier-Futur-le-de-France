import pandas as pd
import duckdb
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
load_dotenv()

# Récupérer l'URL depuis le .env
neon_url = os.getenv("NEON_DB_URL")

# Paramètres de base
departements_idf = ['75', '92', '93', '94', '95', '78', '91', '77']
annee = 2024
base_url = f"https://files.data.gouv.fr/geo-dvf/latest/csv/{annee}/departements"

# Chargement des données pour chaque département
df_list = []

for dep in departements_idf:
    url = f"{base_url}/{dep}.csv.gz"
    print(f"Chargement : {url}")
    
    try:
        df = pd.read_csv(url, sep=',', compression='gzip', low_memory=False)
        df['departement'] = dep
        df_list.append(df)
    except Exception as e:
        print(f"Erreur lors du chargement du département {dep} : {e}")

# Fusion des DataFrames
df_idf = pd.concat(df_list, ignore_index=True)

# Sélection des colonnes utiles
features = [
    'surface_reelle_bati',
    'nombre_pieces_principales',
    'type_local',
    'code_postal',
    'longitude',
    'latitude',
    'nature_mutation',
    'date_mutation',
    'valeur_fonciere',
    'id_mutation'
]

df_idf = df_idf[features]

# Filtrage : uniquement ventes de maisons et appartements
query_1 = '''
    SELECT *
    FROM df_idf
    WHERE type_local IN ('Appartement', 'Maison') 
    AND nature_mutation = 'Vente'
'''
df_idf = duckdb.query(query_1).df()

# Suppression des lignes avec valeurs manquantes
df_idf.dropna(inplace=True)

# Calcul du prix au mètre carré
query_2 = '''
    WITH prix_par_m2 AS (
        SELECT 
            id_mutation, 
            MAX(valeur_fonciere) / SUM(surface_reelle_bati) AS prix_m2
        FROM df_idf
        GROUP BY id_mutation
    )
    SELECT df_idf.*, prix_par_m2.prix_m2
    FROM df_idf
    LEFT JOIN prix_par_m2 USING(id_mutation)
'''
df_idf = duckdb.query(query_2).df()

# Filtrage : valeurs cohérentes du prix au m²
query_3 = '''
    SELECT *
    FROM df_idf
    WHERE prix_m2 BETWEEN 1000 AND 25000
'''
df_idf = duckdb.query(query_3).df()

# Suppression des colonnes devenues inutiles
df_idf.drop(['valeur_fonciere', 'nature_mutation'], axis=1, inplace=True)

print("Dataset final prêt :", df_idf.shape)




# Colle ici l'URL obtenue depuis Neon
neon_url = os.getenv("NEON_DB_URL")
engine = create_engine(neon_url)

# Envoi du DataFrame dans Neon
df_idf.to_sql("valeurs_foncieres_idf_2024", engine, if_exists="replace", index=False)
