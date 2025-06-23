def prix_m2_moyen_par_type(biens):
    """
    Calcule le prix moyen au m² pour chaque type de bien.

    :param biens: Liste de dictionnaires contenant les données des biens.
    :return: Dictionnaire {type_local: prix_m2_moyen arrondi à 3 décimales} ou message d'erreur.
    """
    try:
        stats = {}
        for b in biens:
            type_local = b.get("type_local")
            prix = b.get("prix_m2")
            if type_local and prix is not None:
                stats.setdefault(type_local, []).append(prix)
        return {t: (round(sum(p) / len(p), 3) if p else None) for t, p in stats.items()}
    except Exception as e:
        return {"error": f"Erreur dans prix_m2_moyen_par_type: {str(e)}"}


def nombre_pieces_moyen_par_type(biens):
    """
    Calcule le nombre moyen de pièces principales par type de bien.

    :param biens: Liste de dictionnaires contenant les données des biens.
    :return: Dictionnaire {type_local: nombre_pieces_moyen} ou message d'erreur.
    """
    try:
        stats = {}
        for b in biens:
            type_local = b.get("type_local")
            pieces = b.get("nombre_pieces_principales")
            if type_local and pieces is not None:
                stats.setdefault(type_local, []).append(pieces)
        return {t: (sum(p) / len(p) if p else None) for t, p in stats.items()}
    except Exception as e:
        return {"error": f"Erreur dans nombre_pieces_moyen_par_type: {str(e)}"}


def prix_m2_min_par_type(biens):
    """
    Calcule le prix minimum au m² pour chaque type de bien.

    :param biens: Liste de dictionnaires contenant les données des biens.
    :return: Dictionnaire {type_local: prix_m2_min} ou message d'erreur.
    """
    try:
        stats = {}
        for b in biens:
            type_local = b.get("type_local")
            prix = b.get("prix_m2")
            if type_local and prix is not None:
                if type_local not in stats:
                    stats[type_local] = prix
                else:
                    stats[type_local] = min(prix, stats[type_local])
        return stats
    except Exception as e:
        return {"error": f"Erreur dans prix_m2_min_par_type: {str(e)}"}


def prix_m2_max_par_type(biens):
    """
    Calcule le prix maximum au m² pour chaque type de bien.

    :param biens: Liste de dictionnaires contenant les données des biens.
    :return: Dictionnaire {type_local: prix_m2_max} ou message d'erreur.
    """
    try:
        stats = {}
        for b in biens:
            type_local = b.get("type_local")
            prix = b.get("prix_m2")
            if type_local and prix is not None:
                stats[type_local] = max(prix, stats.get(type_local, prix))
        return stats
    except Exception as e:
        return {"error": f"Erreur dans prix_m2_max_par_type: {str(e)}"}


def surface_moyenne_par_type(biens):
    """
    Calcule la surface bâtie moyenne pour chaque type de bien.

    :param biens: Liste de dictionnaires contenant les données des biens.
    :return: Dictionnaire {type_local: surface_moyenne} ou message d'erreur.
    """
    try:
        stats = {}
        for b in biens:
            type_local = b.get("type_local")
            surf = b.get("surface_reelle_bati")
            if type_local and surf is not None:
                stats.setdefault(type_local, []).append(surf)
        return {t: (sum(s) / len(s) if s else None) for t, s in stats.items()}
    except Exception as e:
        return {"error": f"Erreur dans surface_moyenne_par_type: {str(e)}"}


def nombre_biens_par_type(biens):
    """
    Compte le nombre de biens pour chaque type de bien.

    :param biens: Liste de dictionnaires contenant les données des biens.
    :return: Dictionnaire {type_local: nombre de biens} ou message d'erreur.
    """
    try:
        stats = {}
        for b in biens:
            type_local = b.get("type_local")
            if type_local:
                stats[type_local] = stats.get(type_local, 0) + 1
        return stats
    except Exception as e:
        return {"error": f"Erreur dans nombre_biens_par_type: {str(e)}"}
