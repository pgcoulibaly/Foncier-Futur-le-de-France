from together import Together
from typing import AsyncGenerator
import asyncio
from core.stat_compute import (
    prix_m2_moyen_par_type,
    prix_m2_max_par_type,
    prix_m2_min_par_type,
    surface_moyenne_par_type,
    nombre_pieces_moyen_par_type,
    nombre_biens_par_type
)

def analyse_biens_par_llm(biens: list[dict], rayon_m: int, param: dict) -> str:
    """
    Version originale non-streaming (conservée pour compatibilité)
    """
    try:
        client = Together()
        # Calcul des statistiques (logique conservée)
        stats = {
            "nombre_biens": nombre_biens_par_type(biens),
            "prix_m2_moyen": prix_m2_moyen_par_type(biens),
            "prix_m2_max": prix_m2_max_par_type(biens),
            "prix_m2_min": prix_m2_min_par_type(biens),
            "surface_moyenne": surface_moyenne_par_type(biens),
            "nombre_pieces_moyen": nombre_pieces_moyen_par_type(biens)
        }
        
        # Générer le prompt (fonction conservée)
        prompt = formater_prompt(stats, rayon_m)

        # Appel API via Together SDK
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            messages=[
                {"role": "system", "content": "Tu es un expert en analyse immobilière."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            top_p=0.95,
            max_tokens=300,
            repetition_penalty=1
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        param["logger"].error(f"Erreur analyse LLM: {e}")
        return "Analyse indisponible temporairement."

async def analyse_biens_par_llm_stream(biens: list[dict], rayon_m: int, param: dict) -> AsyncGenerator[str, None]:
    """
    Version streaming de l'analyse LLM avec Together.ai
    Conserve exactement la même logique de calcul des statistiques
    
    :param biens: Liste de biens 
    :param rayon_m: Rayon choisi en mètres
    :param param: engine et logger 
    :yield: Chunks de texte au fur et à mesure de la génération
    """
    try:
        # Calcul des statistiques sur TOUS les biens (logique identique)
        stats = {
            "nombre_biens": nombre_biens_par_type(biens),
            "prix_m2_moyen": prix_m2_moyen_par_type(biens),
            "prix_m2_max": prix_m2_max_par_type(biens),
            "prix_m2_min": prix_m2_min_par_type(biens),
            "surface_moyenne": surface_moyenne_par_type(biens),
            "nombre_pieces_moyen": nombre_pieces_moyen_par_type(biens)
        }
        
        # Générer le prompt (fonction conservée exactement)
        prompt = formater_prompt(stats, rayon_m)
        
        param["logger"].info(f"Analyse streaming démarrée pour {len(biens)} biens")
        
        # Utilisation de Together.ai en mode streaming
        try:
            # Tentative d'utilisation du streaming natif de Together
            # Note: Vérifiez si Together supporte le streaming dans votre version
            client = Together()
            
            response = client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                messages=[
                    {"role": "system", "content": "Tu es un expert en analyse immobilière."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                top_p=0.95,
                max_tokens=1024,
                repetition_penalty=1,
                stream=True  # Activation du streaming si supporté
            )
            
            # Streaming des chunks
            for chunk in response:
                if hasattr(chunk, 'choices') and chunk.choices:
                    if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta:
                        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                            await asyncio.sleep(0.01)  # Délai pour un streaming naturel
                            
        except Exception as streaming_error:
            # Fallback : simulation de streaming avec la réponse complète
            param["logger"].warning(f"Streaming natif indisponible, simulation: {streaming_error}")
            
            client = Together()
            response = client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                messages=[
                    {"role": "system", "content": "Tu es un expert en analyse immobilière."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                top_p=0.95,
                max_tokens=1024,
                repetition_penalty=1.3
            )
            
            # Simulation de streaming en découpant la réponse
            full_content = response.choices[0].message.content.strip()
            
            # Découpage par mots pour simuler un streaming naturel
            words = full_content.split(' ')
            current_chunk = ""
            
            for word in words:
                current_chunk += word + " "
                
                # Envoyer un chunk tous les 3-5 mots
                if len(current_chunk.split()) >= 4:
                    yield current_chunk
                    current_chunk = ""
                    await asyncio.sleep(0.05)  # Délai pour simuler la génération
            
            # Envoyer le reste s'il y en a
            if current_chunk.strip():
                yield current_chunk

    except Exception as e:
        param["logger"].error(f"Erreur analyse LLM streaming: {e}")
        yield f"\n\n Erreur lors de l'analyse : Analyse indisponible temporairement."

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
        f"\n".join(parts) +
        "\n\nÀ partir de ces statistiques, rédige un commentaire détaillé pour chaque type de bien de manière indépendante. "
        "Pour chaque type de bien, analyse uniquement ses propres caractéristiques sans le comparer aux autres types. "
        "Tu dois présenter les prix en insistant sur l'écart entre le minimum, la moyenne et le maximum de ce type spécifique. "
        "Commente également les surfaces et le nombre moyen de pièces pour ce type, en montrant ce que ces chiffres indiquent sur les biens de cette catégorie. "
        "Ne fais aucune supposition extérieure : ne parle pas d'équipements, d'environnement, de qualité ou de demande. "
        "Ne fais strictement aucune comparaison avec d'autres secteurs, périodes, ou autres types de biens. "
        "Traite chaque type de bien comme une analyse isolée et autonome. "
        "Limite-toi à analyser les chiffres de chaque type individuellement et à les expliquer de façon précise et complète. "
        "Si le nombre de biens est de 0 pour un type, indique qu'il n'y a pas eu de vente de ce type en 2024 dans le rayon choisi et limite-toi à ça.\n\n"
        "les titres de section ═══ APPARTEMENTS ═══ ou ═══ MAISONS ═══ repectivement pour chaque type de bien  "
        "Rajoute une synthése la fin de l'analyse avec le titre ═══ CONCLUSION ═══ "
       
    )
