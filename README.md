# **Proximmo**

Visualisez les statistiques des biens vendus autour d'une adresse et bénéficiez d'une analyse IA générative basée sur ces données.

## Structure du projet

```
proximmo/
├── .devcontainer/
│   └── devcontainer.json     # Configuration du conteneur de développement
├── frontend/
│   ├── app_front.py          # Frontend principal avec Streamlit
│   └── requirements.txt      # Dépendances du frontend
├── backend/
│   ├── app.py                # Point d'entrée de l'API backend
│   ├── requirements.txt      # Dépendances du backend
│   └── core/
│       ├── geocod.py         # Géocodage et recherche des biens à proximité
│       ├── stat_compute.py   # Calcul des statistiques immobilières
│       └── llm_assistant.py  # Assistant IA générative pour l'analyse des statistiques
├── start_app.py              # Script de démarrage des services frontend et backend
├── .gitignore                # Fichiers et dossiers ignorés par Git
└── README.md                 # Documentation du projet
```

## Description des composants

### Configuration et environnement
- **devcontainer/devcontainer.json** : définit l'environnement de développement conteneurisé.
- **.gitignore** : spécifie les fichiers et dossiers à exclure du version control Git
- **README.md** : documentation du projet

### Frontend
- **frontend/app_front.py** : interface utilisateur principale basée sur Streamlit.
- **frontend/requirements.txt** : liste des bibliothèques Python requises par le frontend.

### Backend
- **backend/app.py** : point d'entrée de l'API FastAPI, orchestre les appels aux fonctions de géocodage, de calcul de statistiques et d'analyse IA
- **backend/requirements.txt** : liste des dépendances Python du backend.

### Modules métier
- **backend/core/geocod.py** : module de géolocalisation incluant :
   - fonction de géocodage d'une adresse
   - calcul de la distance haversienne entre l'adresse et les biens vendus
   - recherche des biens à proximité dans le rayon choisi

- **backend/core/stat_compute.py** : calcule les statistiques (prix moyen, médian, volume) des biens vendus dans le rayon défini

- **backend/core/llm_assistant.py** : module d'analyse IA générative qui interprète les statistiques pour fournir des insights et recommandations

### Démarrage
- **start_app.py** : script principal pour lancer simultanément le backend (FastAPI) et le frontend (Streamlit) en local

## Configuration des variables d'environnement

Proximmo utilise :

- **Together** pour le traitement LLM et la génération d'analyses via `backend/core/llm_assistant.py`.
- **Neon** pour la base de données SQL des biens vendus, accessible dans `backend/core/stat_compute.py` et `geocod.py`.

Les accès sont gérés par les variables d'environnement :

- **TOGETHER_API_KEY** pour authentifier les appels à Together LLM
- **NEON_DATABASE_URL** pour se connecter à la base Neon SQL

## Fonctionnalités

L'application offre une expérience utilisateur complète pour l'analyse immobilière :

- L'utilisateur saisit une adresse et un rayon de recherche, puis déclenche la requête.
- Une carte interactive affiche les biens vendus situés dans le périmètre choisi.
- Des statistiques globales sont présentées pour l'ensemble des biens trouvés.
- Un tableau détaille les statistiques par type de bien.
- Un bouton permet de lancer une analyse LLM des statistiques, générant des insights et recommandations basés sur les données. 