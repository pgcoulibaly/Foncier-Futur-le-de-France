import streamlit as st
import requests
from streamlit_folium import st_folium
import folium
import plotly.express as px
import pandas as pd

# Configuration de la page avec un thème personnalisé
st.set_page_config(
    page_title="Immobilier Île-de-France", 
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🏠"
)

# CSS personnalisé pour l'esthétique
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    
    .search-container {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border: 1px solid #e9ecef;
    }
    
    .analysis-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-top: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #28a745;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Correction de l'espacement */
    .element-container {
        margin-bottom: 1rem !important;
    }
    
    /* Réduction des marges par défaut de Streamlit */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Espacement des sections */
    .stMarkdown {
        margin-bottom: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# En-tête principal
st.markdown("""
<div class="main-header">
    <h1>Immobilier Île-de-France</h1>
    <p>Découvrez les biens immobiliers autour de vous avec notre analyse IA</p>
</div>
""", unsafe_allow_html=True)

# Sidebar pour les paramètres
with st.sidebar:
    st.header("Paramètres de recherche")
    
    # Formulaire dans la sidebar
    adresse = st.text_input(
        "Adresse", 
        placeholder="Ex: 1 Place de la République, Paris",
        help="Saisissez une adresse en Île-de-France"
    )
    
    rayon = st.slider(
        "Rayon de recherche (mètres)", 
        min_value=100, 
        max_value=1000, 
        value=500, 
        step=100,
        help="Définissez le périmètre de recherche"
    )
    
    st.markdown("---")
    
    # Bouton de recherche stylisé
    rechercher = st.button("Lancer la recherche", use_container_width=True)
    
    # Informations sur l'app
    st.markdown("---")
    st.markdown("""
    ### À propos
    Cette application vous permet de :
    - Visualiser les biens sur une carte
    - Analyser le marché local
    - Obtenir une analyse IA personnalisée
    """)

# Initialisation des états de session
if "biens" not in st.session_state:
    st.session_state.biens = []
if "analyse" not in st.session_state:
    st.session_state.analyse = ""

# Logique de recherche
if rechercher:
    if not adresse:
        st.warning("Veuillez saisir une adresse pour commencer la recherche.")
    else:
        with st.spinner("Recherche en cours..."):
            try:
                res = requests.get("http://localhost:8000/biens_proches", params={
                    "adresse": adresse,
                    "rayon_m": rayon
                })
                res.raise_for_status()
                data = res.json()

                biens = data.get("biens_proches", [])
                analyse = data.get("analyse", "Aucune analyse fournie.")

                st.session_state.biens = biens
                st.session_state.analyse = analyse

                if not biens:
                    st.info("Aucun bien trouvé dans ce rayon. Essayez d'augmenter le périmètre de recherche.")
                else:
                    st.success(f"{len(biens)} bien(s) trouvé(s) !")

            except Exception as e:
                st.error(f"Erreur lors de la requête : {e}")

# Affichage des résultats
if st.session_state.biens:
    
    # Métriques principales
    st.subheader("Aperçu du marché")
    
    # Calcul des statistiques
    df_biens = pd.DataFrame(st.session_state.biens)
    prix_moyen = df_biens['prix_m2'].mean()
    surface_moyenne = df_biens['surface_reelle_bati'].mean()
    nb_pieces_moyen = df_biens['nombre_pieces_principales'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Prix moyen/m²",
            value=f"{prix_moyen:,.0f} €",
            delta=f"{len(st.session_state.biens)} biens"
        )
    
    with col2:
        st.metric(
            label="Surface moyenne",
            value=f"{surface_moyenne:.0f} m²"
        )
    
    with col3:
        st.metric(
            label="Pièces moyennes",
            value=f"{nb_pieces_moyen:.1f}"
        )
    
    with col4:
        st.metric(
            label="Rayon",
            value=f"{rayon} m"
        )
    
    # Carte et graphiques
    col_map, col_chart = st.columns([2, 1])
    
    with col_map:
        st.subheader("Localisation des biens")
        
        # Calcul du centre basé sur l'adresse recherchée (moyenne des coordonnées)
        center_lat = sum(bien["latitude"] for bien in st.session_state.biens) / len(st.session_state.biens)
        center_lon = sum(bien["longitude"] for bien in st.session_state.biens) / len(st.session_state.biens)
        
        # Calcul du zoom optimal basé sur le rayon
        if rayon <= 500:
            zoom_level = 16
        elif rayon <= 1000:
            zoom_level = 15
        elif rayon <= 2000:
            zoom_level = 14
        else:
            zoom_level = 13
        
        # Carte Folium
        m = folium.Map(
            location=[center_lat, center_lon], 
            zoom_start=zoom_level,
            tiles='CartoDB positron',
            max_zoom=18,
            zoom_control=True,
            scrollWheelZoom=True,
            doubleClickZoom=False,
            dragging=True
        )
        
        # Point central de l'adresse recherchée (en rouge/orange)
        folium.Marker(
            [center_lat, center_lon],
            popup=folium.Popup(f"""
            <div style="font-family: Arial; width: 180px; text-align: center;">
                <h4 style="color: #ff6b35; margin-bottom: 10px;">Adresse recherchée</h4>
                <p><strong>Rayon:</strong> {rayon} m</p>
                <p style="color: #666; font-size: 12px;">{adresse}</p>
            </div>
            """, max_width=200),
            icon=folium.Icon(color='orange', icon='star', prefix='fa'),
            tooltip="Point de recherche"
        ).add_to(m)
        
        # Cercle de rayon parfaitement centré avec marge de sécurité
        rayon_reel = rayon + 100  # Ajout de 100m de marge
        folium.Circle(
            location=[center_lat, center_lon],
            radius=rayon_reel,
            color='#ff6b35',
            weight=2,
            fill=True,
            fillColor='#ff6b35',
            fillOpacity=0.1,
            popup=f"Zone de recherche: {rayon}m )",
            tooltip=f"Rayon affiché: {rayon}m "
        ).add_to(m)
        
        # Groupement des biens par coordonnées pour gérer les doublons
        biens_groupes = {}
        for i, bien in enumerate(st.session_state.biens):
            coord_key = f"{bien['latitude']:.6f},{bien['longitude']:.6f}"
            if coord_key not in biens_groupes:
                biens_groupes[coord_key] = []
            biens_groupes[coord_key].append((i, bien))
        
        # Ajout des marqueurs avec gestion des biens multiples
        for coord_key, biens_list in biens_groupes.items():
            if len(biens_list) == 1:
                # Cas simple : un seul bien à cette adresse
                i, bien = biens_list[0]
                
                # Couleur selon le prix
                if bien["prix_m2"] > prix_moyen * 1.2:
                    color = 'red'
                    icon = 'arrow-up'
                    price_status = "Prix élevé"
                elif bien["prix_m2"] < prix_moyen * 0.8:
                    color = 'green'
                    icon = 'arrow-down'
                    price_status = "Prix attractif"
                else:
                    color = 'blue'
                    icon = 'home'
                    price_status = "Prix moyen"
                
                folium.Marker(
                    [bien["latitude"], bien["longitude"]],
                    popup=folium.Popup(f"""
                    <div style="font-family: Arial; width: 220px;">
                        <h4 style="color: #667eea; margin-bottom: 8px;">{bien["type_local"]} #{i+1}</h4>
                        <div style="background: #f8f9fa; padding: 8px; border-radius: 5px; margin: 5px 0;">
                            <p style="margin: 2px 0;"><strong>Prix:</strong> {bien["prix_m2"]:,} €/m² <em>({price_status})</em></p>
                            <p style="margin: 2px 0;"><strong>Surface:</strong> {bien["surface_reelle_bati"]} m²</p>
                            <p style="margin: 2px 0;"><strong>Pièces:</strong> {bien["nombre_pieces_principales"]}</p>
                            <p style="margin: 2px 0;"><strong>Distance:</strong> {round(bien["distance_m"])} m</p>
                        </div>
                    </div>
                    """, max_width=250),
                    icon=folium.Icon(color=color, icon=icon, prefix='fa'),
                    tooltip=f"{bien['type_local']} - {bien['prix_m2']:,}€/m²"
                ).add_to(m)
                
            else:
                # Cas complexe : plusieurs biens à la même adresse
                lat, lon = float(coord_key.split(',')[0]), float(coord_key.split(',')[1])
                
                # Calcul du prix moyen pour cette adresse
                prix_moyens_adresse = sum(bien["prix_m2"] for _, bien in biens_list) / len(biens_list)
                
                # Couleur du marqueur principal basée sur le prix moyen
                if prix_moyens_adresse > prix_moyen * 1.2:
                    main_color = 'red'
                elif prix_moyens_adresse < prix_moyen * 0.8:
                    main_color = 'green'
                else:
                    main_color = 'blue'
                
                # Création du popup détaillé pour tous les biens
                popup_content = f"""
                <div style="font-family: Arial; width: 280px;">
                    <h4 style="color: #667eea; margin-bottom: 8px; text-align: center;">
                        {len(biens_list)} biens à cette adresse
                    </h4>
                    <div style="background: #e3f2fd; padding: 8px; border-radius: 5px; margin: 5px 0; text-align: center;">
                        <strong>Prix moyen: {prix_moyens_adresse:,.0f} €/m²</strong>
                    </div>
                """
                
                for j, (i, bien) in enumerate(biens_list):
                    if bien["prix_m2"] > prix_moyens_adresse * 1.1:
                        price_indicator = "🔴"
                    elif bien["prix_m2"] < prix_moyens_adresse * 0.9:
                        price_indicator = "🟢"
                    else:
                        price_indicator = "🔵"
                    
                    popup_content += f"""
                    <div style="background: #f8f9fa; padding: 6px; border-radius: 3px; margin: 3px 0; border-left: 3px solid {'#ff4444' if bien['prix_m2'] > prix_moyens_adresse * 1.1 else '#44ff44' if bien['prix_m2'] < prix_moyens_adresse * 0.9 else '#4444ff'};">
                        <p style="margin: 1px 0; font-weight: bold;">{price_indicator} {bien["type_local"]} #{i+1}</p>
                        <p style="margin: 1px 0; font-size: 12px;"><strong>Prix:</strong> {bien["prix_m2"]:,} €/m²</p>
                        <p style="margin: 1px 0; font-size: 12px;"><strong>Surface:</strong> {bien["surface_reelle_bati"]} m² | <strong>Pièces:</strong> {bien["nombre_pieces_principales"]}</p>
                    </div>
                    """
                
                popup_content += "</div>"
                
                # Marqueur principal avec icône spéciale pour les groupes
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    icon=folium.Icon(
                        color=main_color, 
                        icon='building', 
                        prefix='fa'
                    ),
                    tooltip=f"{len(biens_list)} biens - {prix_moyens_adresse:,.0f}€/m² moy."
                ).add_to(m)
                
                # Ajout de petits marqueurs décalés pour chaque bien individuel
                import math
                
                # Rayon du cercle adapté au nombre de biens
                if len(biens_list) <= 3:
                    radius_offset = 0.0002  # Cercle plus petit pour peu de biens
                elif len(biens_list) <= 6:
                    radius_offset = 0.0003  # Cercle moyen
                elif len(biens_list) <= 10:
                    radius_offset = 0.0004  # Cercle plus grand
                else:
                    radius_offset = 0.0005  # Très grand cercle pour beaucoup de biens
                
                for j, (i, bien) in enumerate(biens_list):
                    # Calcul du décalage en cercle autour du point principal
                    angle = (2 * math.pi * j) / len(biens_list)
                    offset_lat = lat + (radius_offset * math.cos(angle))
                    offset_lon = lon + (radius_offset * math.sin(angle))
                    
                    # Couleur selon le prix individuel
                    if bien["prix_m2"] > prix_moyen * 1.2:
                        color = 'red'
                        icon = 'arrow-up'
                    elif bien["prix_m2"] < prix_moyen * 0.8:
                        color = 'green' 
                        icon = 'arrow-down'
                    else:
                        color = 'blue'
                        icon = 'home'
                    
                    folium.CircleMarker(
                        [offset_lat, offset_lon],
                        radius=6,
                        popup=folium.Popup(f"""
                        <div style="font-family: Arial; width: 180px;">
                            <h5 style="color: #667eea; margin-bottom: 5px;">{bien["type_local"]} #{i+1}</h5>
                            <p style="margin: 1px 0; font-size: 11px;"><strong>Prix:</strong> {bien["prix_m2"]:,} €/m²</p>
                            <p style="margin: 1px 0; font-size: 11px;"><strong>Surface:</strong> {bien["surface_reelle_bati"]} m²</p>
                            <p style="margin: 1px 0; font-size: 11px;"><strong>Pièces:</strong> {bien["nombre_pieces_principales"]}</p>
                        </div>
                        """, max_width=200),
                        color=color,
                        fillColor=color,
                        fillOpacity=0.7,
                        weight=2,
                        tooltip=f"{bien['type_local']} - {bien['prix_m2']:,}€/m²"
                    ).add_to(m)
        
        # Affichage de la carte
        map_data = st_folium(
            m, 
            width=700, 
            height=500,
            returned_objects=["last_object_clicked"],
            key="main_map"
        )
        
        st.info(f"Zone fixée sur {rayon}m  autour de: {adresse[:50]}{'...' if len(adresse) > 50 else ''}")
    
    with col_chart:
        st.subheader("Analyse des prix")
        
        # Graphique en barres des prix
        fig_prix = px.histogram(
            df_biens, 
            x='prix_m2', 
            nbins=10,
            title="Distribution des prix/m²",
            labels={'prix_m2': 'Prix/m² (€)', 'count': 'Nombre de biens'},
            color_discrete_sequence=['#667eea']
        )
        fig_prix.update_layout(
            showlegend=False,
            height=300,
            font=dict(size=10)
        )
        st.plotly_chart(fig_prix, use_container_width=True)
        
        # Graphique surfaces vs prix
        fig_scatter = px.scatter(
            df_biens, 
            x='surface_reelle_bati', 
            y='prix_m2',
            size='nombre_pieces_principales',
            color='type_local',
            title="Surface vs Prix/m²",
            labels={
                'surface_reelle_bati': 'Surface (m²)', 
                'prix_m2': 'Prix/m² (€)'
            }
        )
        fig_scatter.update_layout(height=300, font=dict(size=10))
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Analyse IA - CORRECTION ICI : suppression du markdown "---" qui créait l'espace
    st.markdown("""
    <div class="analysis-card">
        <h3>Analyse IA du marché local</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(st.session_state.analyse)
    
    # Tableau des données
    with st.expander("Voir le détail des biens"):
        df_display = df_biens.copy()
        df_display['distance_m'] = df_display['distance_m'].round(0)
        df_display['prix_m2'] = df_display['prix_m2'].round(0)
        
        st.dataframe(
            df_display[['type_local', 'prix_m2', 'surface_reelle_bati', 
                       'nombre_pieces_principales', 'distance_m']],
            use_container_width=True,
            column_config={
                "type_local": "Type",
                "prix_m2": st.column_config.NumberColumn("Prix/m² (€)", format="%d €"),
                "surface_reelle_bati": st.column_config.NumberColumn("Surface (m²)", format="%d m²"),
                "nombre_pieces_principales": "Pièces",
                "distance_m": st.column_config.NumberColumn("Distance (m)", format="%d m")
            }
        )

else:
    # Message d'accueil
    st.markdown("""
    <div style="text-align: center; padding: 3rem; background: #f8f9fa; border-radius: 10px; margin: 2rem 0;">
        <h3>Bienvenue sur votre assistant immobilier !</h3>
        <p>Utilisez le panneau de gauche pour rechercher des biens immobiliers autour d'une adresse.</p>
        <p>Vous obtiendrez une carte interactive, des statistiques et une analyse IA personnalisée.</p>
    </div>
    """, unsafe_allow_html=True)