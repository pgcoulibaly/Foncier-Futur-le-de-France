import streamlit as st
import requests
from streamlit_folium import st_folium
import folium
import plotly.express as px
import pandas as pd
import json
import time

API_URL = st.secrets.get("API_URL", "http://localhost:8000")
# Config de la page
st.set_page_config(
    page_title="ProxImmo",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🏠",
)

# CSS 
st.markdown(
    """
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
    
    .analysis-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-top: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #28a745;
    }
    
    .streaming-analysis {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        min-height: 100px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        line-height: 1.5;
    }
    
    .streaming-cursor {
        display: inline-block;
        width: 2px;
        height: 1.2em;
        background-color: #667eea;
        animation: blink 1s infinite;
        margin-left: 2px;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    
    .analysis-complete {
        border-left: 4px solid #28a745;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .analysis-error {
        border-left: 4px solid #dc3545;
        background: #f8d7da;
        color: #721c24;
    }
</style>
""",
    unsafe_allow_html=True,
)

# En-tête principal
st.markdown(
    """
<div class="main-header">
    <h1>ProxImmo</h1>
    <p>Découvrez les biens immobiliers autour de vous avec notre analyse IA</p>
</div>
""",
    unsafe_allow_html=True,
)


# Fonction de streaming  pour sauvegarder le résultat
def stream_analysis_sync(adresse, rayon, placeholder):
    """
    Version synchrone du streaming et sauvegarde le résultat
    """
    try:
        # Affichage initial
        placeholder.markdown(
            """
        <div class="streaming-analysis">
            <h4>Connexion au service d'analyse...</h4>
            <p>Initialisation en cours<span class="streaming-cursor"></span></p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Requête streaming
        response = requests.get(
            f"{API_URL}/analyse_stream",
            params={"adresse": adresse, "rayon_m": rayon},
            stream=True,
            timeout=600,
        )

        if response.status_code != 200:
            error_content = """
            <div class="streaming-analysis analysis-error">
                <h4>Erreur de connexion</h4>
                <p>Impossible de se connecter au service d'analyse</p>
            </div>
            """
            placeholder.markdown(error_content, unsafe_allow_html=True)
            # Sauvegarder l'erreur et marquer comme terminé
            st.session_state.analysis_result = error_content
            st.session_state.analysis_completed = True
            return

        full_content = ""

        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    data = json.loads(line[6:])  # Enlever "data: "

                    if data["type"] == "start":
                        placeholder.markdown(
                            f"""
                        <div class="streaming-analysis">
                            <h4>Analyse IA en cours...</h4>
                            <p>{data['content']}<span class="streaming-cursor"></span></p>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                    elif data["type"] == "content":
                        full_content += data["content"]
                        # Mise à jour en temps réel
                        placeholder.markdown(
                            f"""
                        <div class="streaming-analysis">
                            <h4>Analyse IA</h4>
                            <div style="white-space: pre-wrap;">{full_content}<span class="streaming-cursor"></span></div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        # Petit délai pour voir l'effet streaming
                        time.sleep(0.1)

                    elif data["type"] == "end":
                        # Analyse terminée
                        final_content = f"""
                        <div class="streaming-analysis analysis-complete">
                            <h4>Analyse IA terminée</h4>
                            <div style="white-space: pre-wrap;">{full_content}</div>
                        </div>
                        """
                        placeholder.markdown(final_content, unsafe_allow_html=True)
                        # Sauvegarder le résultat et marquer comme terminé
                        st.session_state.analysis_result = final_content
                        st.session_state.analysis_completed = True
                        break

                    elif data["type"] == "error":
                        error_content = f"""
                        <div class="streaming-analysis analysis-error">
                            <h4>Erreur</h4>
                            <p>{data['content']}</p>
                        </div>
                        """
                        placeholder.markdown(error_content, unsafe_allow_html=True)
                        # Sauvegarder l'erreur et marquer comme terminé
                        st.session_state.analysis_result = error_content
                        st.session_state.analysis_completed = True
                        break

                except json.JSONDecodeError:
                    continue

    except requests.exceptions.RequestException as e:
        error_content = f"""
        <div class="streaming-analysis analysis-error">
            <h4>Erreur de connexion</h4>
            <p>Impossible de se connecter au service d'analyse: {str(e)}</p>
        </div>
        """
        placeholder.markdown(error_content, unsafe_allow_html=True)
        # Sauvegarder l'erreur et marquer comme terminé
        st.session_state.analysis_result = error_content
        st.session_state.analysis_completed = True
    except Exception as e:
        error_content = f"""
        <div class="streaming-analysis analysis-error">
            <h4>Erreur inattendue</h4>
            <p>{str(e)}</p>
        </div>
        """
        placeholder.markdown(error_content, unsafe_allow_html=True)
        # Sauvegarder l'erreur et marquer comme terminé
        st.session_state.analysis_result = error_content
        st.session_state.analysis_completed = True


# Sidebar 
with st.sidebar:
    st.header("Paramètres de recherche")

    adresse = st.text_input(
        "Adresse",
        placeholder="Adresse uniquement en Île-de-France",
        help="Saisissez une adresse en Île-de-France",
    )

    rayon = st.slider(
        "Rayon de recherche (mètres)",
        min_value=100,
        max_value=1000,
        value=500,
        step=100,
        help="Définissez le périmètre de recherche",
    )

    st.markdown("---")
    rechercher = st.button("Lancer la recherche", use_container_width=True)

# Initialisation des états de session
if "biens" not in st.session_state:
    st.session_state.biens = []
if "analysis_completed" not in st.session_state:
    st.session_state.analysis_completed = False
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = ""
if "current_search" not in st.session_state:
    st.session_state.current_search = {}
if "stats_per_type" not in st.session_state:
    st.session_state.stats_per_type = {}
if "coord" not in st.session_state:
    st.session_state.coord = ()

# Logique de recherche
if rechercher:
    if not adresse:
        st.warning("Veuillez saisir une adresse pour commencer la recherche.")
    else:
        # Réinitialiser l'état de l'analyse pour une nouvelle recherche
        st.session_state.analysis_completed = False
        st.session_state.analysis_result = ""
        st.session_state.current_search = {"adresse": adresse, "rayon": rayon}

        with st.spinner("Recherche des biens..."):
            try:
                # Appel à l'endpoint des données de base
                res = requests.get(
                    f"{API_URL}/biens_proches",
                    params={"adresse": adresse, "rayon_m": rayon},
                )
                res.raise_for_status()
                data = res.json()

                biens = data.get("biens_proches", [])
                st.session_state.biens = biens
                stats_per_type = data.get("stats_per_type", {})
                st.session_state.stats_per_type = stats_per_type
                coord = data.get("coord", ())
                st.session_state.coord = coord

                if not biens:
                    st.info(
                        "Aucun bien trouvé dans ce rayon. Essayez d'augmenter le périmètre de recherche."
                    )

            except Exception as e:
                st.error(f"Erreur lors de la requête : {e}")

# Affichage des résultats
if st.session_state.biens:

    # Récupération du rayon utilisé pour la recherche actuelle
    rayon_recherche = st.session_state.current_search.get("rayon", rayon)
    adresse_recherche = st.session_state.current_search.get("adresse", adresse)

    # Métriques principales
    st.subheader("Aperçu du marché")

    df_biens = pd.DataFrame(st.session_state.biens)
    prix_moyen = df_biens["prix_m2"].mean()
    surface_moyenne = df_biens["surface_reelle_bati"].mean()
    nb_pieces_moyen = df_biens["nombre_pieces_principales"].mean()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Prix moyen/m²",
            value=f"{prix_moyen:,.0f} €",
            delta=f"{len(st.session_state.biens)} biens",
        )

    with col2:
        st.metric(label="Surface moyenne", value=f"{surface_moyenne:.0f} m²")

    with col3:
        st.metric(label="Pièces moyennes", value=f"{nb_pieces_moyen:.1f}")

    with col4:
        st.metric(label="Rayon", value=f"{rayon_recherche} m")

    # Carte et graphiques
    col_map, col_chart = st.columns([2, 1])

    with col_map:
        st.subheader("Localisation des biens")

        # Calcul du centre basé sur l'adresse recherchée (moyenne des coordonnées)
        center_lat = sum(bien["latitude"] for bien in st.session_state.biens) / len(
            st.session_state.biens
        )
        center_lon = sum(bien["longitude"] for bien in st.session_state.biens) / len(
            st.session_state.biens
        )

        # Calcul du zoom optimal basé sur le rayon
        if rayon <= 500:
            zoom_level = 16
        else:
            zoom_level = 15

        # Carte Folium
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_level,
            tiles="CartoDB positron",
            max_zoom=18,
            zoom_control=True,
            scrollWheelZoom=True,
            doubleClickZoom=False,
            dragging=True,
        )

        # Point central de l'adresse recherchée
        folium.Marker(
            [center_lat, center_lon],
            popup=folium.Popup(
                f"""
            <div style="font-family: Arial; width: 180px; text-align: center;">
                <h4 style="color: #ff6b35; margin-bottom: 10px;">Adresse recherchée</h4>
                <p><strong>Rayon:</strong> {rayon_recherche} m</p>
                <p style="color: #666; font-size: 12px;">{adresse_recherche}</p>
            </div>
            """,
                max_width=200,
            ),
            icon=folium.Icon(color="orange", icon="star", prefix="fa"),
            tooltip="Point de recherche",
        ).add_to(m)

        # Cercle de rayon parfaitement centré avec marge de sécurité
        rayon_reel = rayon_recherche + 100  # Ajout de 100m de marge
        folium.Circle(
            location=[center_lat, center_lon],
            radius=rayon_reel,
            color="#ff6b35",
            weight=2,
            fill=True,
            fillColor="#ff6b35",
            fillOpacity=0.1,
            popup=f"Zone de recherche: {rayon_recherche}m",
            tooltip=f"Rayon affiché: {rayon_recherche}m",
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
                i, bien = biens_list[0]

                # Couleur selon le prix
                if bien["prix_m2"] > prix_moyen * 1.2:
                    color = "red"
                    icon = "arrow-up"
                    price_status = "Prix élevé"
                elif bien["prix_m2"] < prix_moyen * 0.8:
                    color = "green"
                    icon = "arrow-down"
                    price_status = "Prix attractif"
                else:
                    color = "blue"
                    icon = "home"
                    price_status = "Prix moyen"

                folium.Marker(
                    [bien["latitude"], bien["longitude"]],
                    popup=folium.Popup(
                        f"""
                    <div style="font-family: Arial; width: 220px;">
                        <h4 style="color: #667eea; margin-bottom: 8px;">{bien["type_local"]} #{i+1}</h4>
                        <div style="background: #f8f9fa; padding: 8px; border-radius: 5px; margin: 5px 0;">
                            <p style="margin: 2px 0;"><strong>Prix:</strong> {round(bien["prix_m2"],2):,} €/m² <em>({price_status})</em></p>
                            <p style="margin: 2px 0;"><strong>Surface:</strong> {bien["surface_reelle_bati"]} m²</p>
                            <p style="margin: 2px 0;"><strong>Pièces:</strong> {bien["nombre_pieces_principales"]}</p>
                            <p style="margin: 2px 0;"><strong>Adresse:</strong> {bien["adresse"]} </p>
                            <p style="margin: 2px 0;"><strong>Distance:</strong> {round(bien["distance_m"])} m</p>
                        </div>
                    </div>
                    """,
                        max_width=250,
                    ),
                    icon=folium.Icon(color=color, icon=icon, prefix="fa"),
                    tooltip=f"{bien['type_local']} - {round(bien['prix_m2'],2):,}€/m²",
                ).add_to(m)

            else:
                #  plusieurs biens à la même adresse
                lat, lon = float(coord_key.split(",")[0]), float(
                    coord_key.split(",")[1]
                )

                # Calcul du prix moyen pour cette adresse
                prix_moyens_adresse = sum(
                    bien["prix_m2"] for _, bien in biens_list
                ) / len(biens_list)

                # Couleur du marqueur principal basée sur le prix moyen
                if prix_moyens_adresse > prix_moyen * 1.2:
                    main_color = "red"
                elif prix_moyens_adresse < prix_moyen * 0.8:
                    main_color = "green"
                else:
                    main_color = "blue"

                # popup détaillé pour tous les biens
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
                        price_indicator = "•"
                        border_color = "#ff4444"
                    elif bien["prix_m2"] < prix_moyens_adresse * 0.9:
                        price_indicator = "•"
                        border_color = "#44ff44"
                    else:
                        price_indicator = "•"
                        border_color = "#4444ff"

                    popup_content += f"""
                    <div style="background: #f8f9fa; padding: 6px; border-radius: 3px; margin: 3px 0; border-left: 3px solid {border_color};">
                        <p style="margin: 1px 0; font-weight: bold;">{price_indicator} {bien["type_local"]} #{i+1}</p>
                        <p style="margin: 1px 0; font-size: 12px;"><strong>Prix:</strong> {round(bien["prix_m2"],2):,} €/m²</p>
                        <p style="margin: 1px 0; font-size: 12px;"><strong>Surface:</strong> {bien["surface_reelle_bati"]} m² | <strong>Pièces:</strong> {bien["nombre_pieces_principales"]}</p>
                        <p style="margin: 2px 0;"><strong>Adresse:</strong> {bien["adresse"]} </p>
                    </div>
                    """

                popup_content += "</div>"

                #  Icône spéciale pour les groupes
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    icon=folium.Icon(color=main_color, icon="building", prefix="fa"),
                    tooltip=f"{len(biens_list)} biens - {prix_moyens_adresse:,.0f}€/m² moy.",
                ).add_to(m)

                
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
                        color = "red"
                    elif bien["prix_m2"] < prix_moyen * 0.8:
                        color = "green"
                    else:
                        color = "blue"

                    folium.CircleMarker(
                        [offset_lat, offset_lon],
                        radius=6,
                        popup=folium.Popup(
                            f"""
                        <div style="font-family: Arial; width: 180px;">
                            <h5 style="color: #667eea; margin-bottom: 5px;">{bien["type_local"]} #{i+1}</h5>
                            <p style="margin: 1px 0; font-size: 11px;"><strong>Prix:</strong> {round(bien["prix_m2"],2):,} €/m²</p>
                            <p style="margin: 1px 0; font-size: 11px;"><strong>Surface:</strong> {bien["surface_reelle_bati"]} m²</p>
                            <p style="margin: 1px 0; font-size: 11px;"><strong>Pièces:</strong> {bien["nombre_pieces_principales"]}</p>
                            <p style="margin: 2px 0;"><strong>Adresse:</strong> {bien["adresse"]} </p>
                        </div>
                        """,
                            max_width=200,
                        ),
                        color=color,
                        fillColor=color,
                        fillOpacity=0.7,
                        weight=2,
                        tooltip=f"{bien['type_local']} - {bien['prix_m2']:,}€/m²",
                    ).add_to(m)

        # Affichage de la carte
        map_data = st_folium(m, width=700, height=500)

        st.info(
            f"Zone fixée sur {rayon_recherche}m autour de: {adresse_recherche[:50]}{'...' if len(adresse_recherche) > 50 else ''}"
        )

    with col_chart:
        # Légende de la carte
        st.markdown(
            """
        <div style="
            background: rgba(255, 255, 255, 0.85);
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 12px;
            line-height: 1.4;
            display: grid;
            grid-template-columns: auto 1fr;
            grid-row-gap: 6px;
            grid-column-gap: 8px;
            max-width: 280px;
            margin-bottom: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <span style="width:12px; height:12px; background:red;   border-radius:50%;"></span><span><strong>Prix élevé</strong> : > 120 % du prix moyen</span>
            <span style="width:12px; height:12px; background:blue;  border-radius:50%;"></span><span><strong>Prix moyen</strong> : 80 – 120 % du prix moyen</span>
            <span style="width:12px; height:12px; background:green; border-radius:50%;"></span><span><strong>Prix attractif</strong> : < 80 % du prix moyen</span>
            <span style="width:12px; height:12px; background:orange;border-radius:50%;"></span><span><strong>Adresse recherchée</strong> : point central</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

        if st.session_state.stats_per_type:
            st.markdown("###### Statistiques par type de bien")

            # Extraire les données du dictionnaire
            stats_dict = st.session_state.stats_per_type

            # Récupérer les types de biens uniques
            types_biens = list(stats_dict["nombre_biens_par_type"].keys())

            # Créer une liste de dictionnaires pour le DataFrame
            data_for_df = []
            for type_bien in types_biens:
                data_for_df.append(
                    {
                        "Type de bien": type_bien,
                        "Nombre": stats_dict["nombre_biens_par_type"].get(type_bien, 0),
                        "Prix moyen/m²": round(
                            float(
                                stats_dict["prix_m2_moyen_par_type"].get(type_bien, 0)
                            ),
                            2,
                        ),
                        "Prix min/m²": round(
                            float(stats_dict["prix_m2_min_par_type"].get(type_bien, 0)),
                            2,
                        ),
                        "Prix max/m²": round(
                            float(stats_dict["prix_m2_max_par_type"].get(type_bien, 0)),
                            2,
                        ),
                        "Surface moyenne": round(
                            float(
                                stats_dict["surface_moyenne_par_type"].get(type_bien, 0)
                            ),
                            2,
                        ),
                        "Nb pièces moyen": float(
                            stats_dict["nombre_pieces_moyen_par_type"].get(type_bien, 0)
                        ),
                    }
                )

            # Créer le DataFrame
            df_stats = pd.DataFrame(data_for_df)

            df_stats = (
                df_stats.set_index(
                    "Type de bien"
                )  
                .T.reset_index()  
                .rename(
                    columns={"index": "Type de bien"}
                )  
            )

            # Afficher le tableau stylisé
            st.dataframe(
                df_stats,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Type de bien": st.column_config.TextColumn(
                        width="medium",
                    ),
                    "Nombre": st.column_config.NumberColumn(
                        format="%d",
                        width="small",
                    ),
                    "Prix moyen/m²": st.column_config.NumberColumn(
                        format="%d €",
                        width="small",
                    ),
                    "Prix min/m²": st.column_config.NumberColumn(
                        format="%d €",
                        width="small",
                    ),
                    "Prix max/m²": st.column_config.NumberColumn(
                        format="%d €",
                        width="small",
                    ),
                    "Surface moyenne": st.column_config.NumberColumn(
                        format="%d m²",
                        width="small",
                    ),
                    "Nb pièces moyen": st.column_config.NumberColumn(
                        format="%.1f",
                        width="small",
                    ),
                },
            )
    # Section pour l'analyse streaming
    st.subheader("Analyse du marché local")

    # Placeholder pour l'analyse
    analysis_placeholder = st.empty()

    # Afficher le résultat sauvegardé s'il existe
    if st.session_state.analysis_result:
        analysis_placeholder.markdown(
            st.session_state.analysis_result, unsafe_allow_html=True
        )

    # Gestion du bouton d'analyse
    if st.session_state.analysis_completed:
        st.button(
            "Analyse terminée",
            disabled=True,
            help="L'analyse a été effectuée. Lancez une nouvelle recherche pour relancer l'analyse.",
            use_container_width=False,
        )

    else:
        # Bouton de lancement de l'analyse
        if st.button("Lancer l'analyse IA", type="primary", use_container_width=False):
            with st.spinner("Analyse en cours..."):
                stream_analysis_sync(
                    adresse_recherche, rayon_recherche, analysis_placeholder
                )

    # Tableau des données
    with st.expander("Voir le détail des biens"):
        df_display = df_biens.copy()
        df_display["distance_m"] = df_display["distance_m"].round(0)
        df_display["prix_m2"] = df_display["prix_m2"].round(0)

        st.dataframe(
            df_display[
                [
                    "type_local",
                    "prix_m2",
                    "surface_reelle_bati",
                    "nombre_pieces_principales",
                    "adresse",
                    "distance_m",
                ]
            ],
            use_container_width=True,
        )

else:
    # Message d'accueil
    st.markdown(
        """
    <div style="text-align: center; padding: 3rem; background: #f8f9fa; border-radius: 10px; margin: 2rem 0;">
        <h3>Bienvenue sur votre assistant immobilier !</h3>
        <p>Utilisez le panneau de gauche pour rechercher des biens immobiliers autour d'une adresse.</p>
        <p>Vous obtiendrez une carte interactive, des statistiques et une analyse IA personnalisée.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
