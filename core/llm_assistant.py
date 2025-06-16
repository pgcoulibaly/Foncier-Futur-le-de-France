from together import Together



from core.stat_compute import (
    prix_m2_moyen_par_type,
    prix_m2_max_par_type,
    prix_m2_min_par_type,
    surface_moyenne_par_type,
    nombre_pieces_moyen_par_type,
    nombre_biens_par_type
)

# Instancier le client Together (il prend la clé API via TOGETHER_API_KEY automatiquement ou tu peux la passer en argument)


def analyse_biens_par_llm(biens: list[dict], rayon_m: int,api_key: str ) -> str:
    """
    Calcule les statistiques des biens et génère une analyse via Llama 3.3 70B sur Together.ai.

    :param biens: Liste de biens (dictionnaires)
    :param rayon_m: Rayon choisi en mètres
    :param api_key: api_key 
    :return: Analyse textuelle générée
    """
    try:
        client = Together(api_key)
        # Calcul des statistiques
        stats = {
            "nombre_biens": nombre_biens_par_type(biens),
            "prix_m2_moyen": prix_m2_moyen_par_type(biens),
            "prix_m2_max": prix_m2_max_par_type(biens),
            "prix_m2_min": prix_m2_min_par_type(biens),
            "surface_moyenne": surface_moyenne_par_type(biens),
            "nombre_pieces_moyen": nombre_pieces_moyen_par_type(biens)
        }
        

        # Générer le prompt
        prompt = formater_prompt(stats, rayon_m)

        # Appel API via Together SDK
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            messages=[
                {"role": "system", "content": "Tu es un expert en analyse immobilière."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            top_p=0.95,
            max_tokens=1024,
            repetition_penalty=1.1
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Erreur lors de l'analyse : {str(e)}"

def formater_prompt(stats: dict, rayon_m: int) -> str:
    """
    Formate les stats pour le prompt LLM avec un commentaire factuel détaillé incluant le nombre total de biens et la répartition.
    Si aucun bien n'est trouvé, génère un message simple sans analyse.

    :param stats: Stats calculées
    :param rayon_m: Rayon en mètres
    :return: Texte du prompt
    """
    parts = []
    nombre_biens_par_type = stats.get("nombre_biens", {}) or {}
    total_biens = sum(nombre_biens_par_type.values())

    # Répartition par type
    repartition = "\n".join([f"- {t} : {n} bien(s)" for t, n in nombre_biens_par_type.items()])

    # Stats détaillées
    for t in stats.get("prix_m2_moyen", {}).keys():
        parts.append(
            f"{t} :\n"
            f"- Nombre de biens : {nombre_biens_par_type.get(t, 0)}\n"
            f"- Prix moyen au m² : {stats['prix_m2_moyen'].get(t)} €\n"
            f"- Prix max au m² : {stats['prix_m2_max'].get(t)} €\n"
            f"- Prix min au m² : {stats['prix_m2_min'].get(t)} €\n"
            f"- Surface moyenne : {stats['surface_moyenne'].get(t)} m²\n"
            f"- Nombre de pièces moyen : {stats['nombre_pieces_moyen'].get(t)}\n"
        )

    return (
        f"Voici un résumé détaillé des biens vendus dans un rayon de {rayon_m} mètres :\n\n"
        f"Nombre total de biens : {total_biens}\n"
        f"Répartition par type :\n{repartition}\n\n"
        + "\n".join(parts) +
        "\n\nÀ partir de ces statistiques, rédige un commentaire détaillé pour chaque type de bien. "
        "Tu dois présenter les prix en insistant sur l'écart entre le minimum, la moyenne et le maximum. "
        "Commente également les surfaces et le nombre moyen de pièces, en montrant ce que ces chiffres indiquent sur les biens observés. "
        "Ne fais aucune supposition extérieure : ne parle pas d'équipements, d'environnement, de qualité ou de demande. "
        "Ne fais strictement aucune comparaison avec d'autres secteurs ou périodes. "
        "Limite-toi à analyser les chiffres et à les expliquer de façon précise et complète."
        "Si le nombre de bien est de 0 reponds qu il y'a pas de vendu en 2024 dans le rayon choisi et limite toi à ça"
    )
