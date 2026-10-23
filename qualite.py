"""Contrôle qualité d'une ligne d'usinage : lecture des mesures, verdicts, statistiques, rapport."""
import math

NOMINAL = 25.0     # diamètre nominal des axes, en mm
TOLERANCE = 0.05   # tolérance admise : 25,00 ± 0,05 mm


# --- Étape 1 : lire les données -----------------------------------------------------------------
def lire_mesure(texte):
    t = texte.strip().lower()      # " 25,03 MM " -> "25,03 mm"
    t = t.removesuffix("mm")       # "25,03 "
    t = t.strip()                  # "25,03"
    t = t.replace(",", ".")        # "25.03"
    try:
        x = float(t)
    except ValueError:
        raise ValueError(f"mesure invalide : {texte.strip()!r}")
    if not math.isfinite(x) or x <= 0:   # refuse nan, inf, 0 et négatifs
        raise ValueError(f"mesure invalide : {texte.strip()!r}")
    return x


def valider_code(code):
    return (
        len(code) == 8
        and code[:3].isalpha() and code[:3].isupper() and code[:3].isascii()
        and code[3] == "-"
        and code[4:].isdigit() and code[4:].isascii()
    )


# --- Étape 2 : décider ----------------------------------------------------------------------------
def ecart(mesure, nominal=NOMINAL):
    return round(mesure - nominal, 3)


def verdict(mesure, nominal=NOMINAL, tolerance=TOLERANCE):
    if tolerance <= 0:
        raise ValueError(f"tolérance invalide : {tolerance!r}")
    e = ecart(mesure, nominal)
    if abs(e) <= tolerance:
        return "conforme"
    elif e > 0:
        return "à reprendre"
    else:
        return "rebut"


# --- Étape 3 : analyser une ligne -----------------------------------------------------------------
def analyser_ligne(ligne, *, nominal=NOMINAL, tolerance=TOLERANCE):
    champs = ligne.split(";")

    if len(champs) != 2:
        raise ValueError(f"2 champs attendus, {len(champs)} trouvé(s)")

    code = champs[0].strip().upper()

    if not valider_code(code):
        raise ValueError(f"code invalide : {code!r}")

    mesure = lire_mesure(champs[1])
    v = verdict(mesure, nominal=nominal, tolerance=tolerance)

    return (code, mesure, v)


# --- Étape 4 : analyser un lot --------------------------------------------------------------------
def analyser_lot(lignes, **reglages):
    resultats = []
    erreurs = []

    for numero, ligne in enumerate(lignes, start=1):
        if not ligne.strip() or ligne.strip().startswith("#"):
            continue

        try:
            resultat = analyser_ligne(ligne, **reglages)
            resultats.append(resultat)

        except ValueError as err:
            erreurs.append(f"ligne {numero} : {err}")

    return resultats, erreurs

def compter_verdicts(resultats):
    conformes = 0
    a_reprendre = 0
    rebuts = 0

    for code, mesure, v in resultats:
        if v == "conforme":
            conformes += 1
        elif v == "à reprendre":
            a_reprendre += 1
        elif v == "rebut":
            rebuts += 1

    return conformes, a_reprendre, rebuts

# --- Étape 5 : statistiques et capabilité ---------------------------------------------------------

def moyenne(*valeurs):
    if len(valeurs) == 0:
        raise ValueError("Au moins une valeur est nécessaire")

    return sum(valeurs) / len(valeurs)

def ecart_type(*valeurs):
    if len(valeurs) < 2:
        raise ValueError("Au moins deux valeurs sont nécessaires")

    m = moyenne(*valeurs)
    somme = 0

    for x in valeurs:
        somme += (x - m) ** 2

    return math.sqrt(somme / (len(valeurs) - 1))

def capabilite(mesures, *, nominal=NOMINAL, tolerance=TOLERANCE):
    s = ecart_type(*mesures)

    if s == 0:
        raise ValueError("L'écart-type est nul")

    tmin = nominal - tolerance
    tmax = nominal + tolerance

    cp = (tmax - tmin) / (6 * s)

    cpk = min(tmax - moyenne(*mesures),
              moyenne(*mesures) - tmin) / (3 * s)

    return round(cp, 2), round(cpk, 2)

# --- Étape 6 : le rapport -------------------------------------------------------------------------

def rapport(lignes, *, nominal=NOMINAL, tolerance=TOLERANCE):
    """Génère un rapport complet de contrôle qualité."""
    resultats, erreurs = analyser_lot(
        lignes,
        nominal=nominal,
        tolerance=tolerance
    )

    sortie = []

    # En-tête du rapport
    sortie.append(
        f"Contrôle des axes : {nominal:.2f} ± {tolerance:.2f} mm"
    )

    # IMPORTANT : respecter exactement les espaces attendus
    sortie.append(
        f"{'Code':<10}{'Mesure':>8} {'Écart':>8}   Verdict"
    )

    # Afficher les résultats de chaque pièce
    for code, mesure, v in resultats:
        e = ecart(mesure, nominal)

        sortie.append(
            f"{code:<10}{mesure:>8.3f} {e:>+8.3f}   {v}"
        )

    # Compter les verdicts
    conformes, a_reprendre, rebuts = compter_verdicts(resultats)

    nombre_pieces = len(resultats)

    if nombre_pieces > 0:
        pourcentage = conformes / nombre_pieces
    else:
        pourcentage = 0

    sortie.append(
        f"Pièces : {nombre_pieces} | "
        f"conformes : {conformes} ({pourcentage:.1%}) | "
        f"à reprendre : {a_reprendre} | rebuts : {rebuts}"
    )

    # Calculer les indices de capabilité s'il y a au moins deux pièces
    if len(resultats) >= 2:
        mesures = [mesure for code, mesure, v in resultats]

        cp, cpk = capabilite(
            mesures,
            nominal=nominal,
            tolerance=tolerance
        )

        if cpk >= 1.33:
            conclusion = "procédé capable"
        else:
            conclusion = "procédé NON capable"

        sortie.append(
            f"Cp = {cp:.2f} | Cpk = {cpk:.2f} -> {conclusion}"
        )

    # Afficher les erreurs à la fin du rapport
    if erreurs:
        sortie.append(f"Lignes rejetées : {len(erreurs)}")

        for erreur in erreurs:
            sortie.append(f"  {erreur}")

    return "\n".join(sortie)
# --- Étape 8 (à la maison) : histogramme ----------------------------------------------------------
def histogramme(mesures: list[float], *, debut: float, pas: float, nb_classes: int) -> str:
    """Histogramme texte avec une étoile par mesure dans chaque classe."""
    effectifs = [0] * nb_classes

    for mesure in mesures:
        for indice in range(nb_classes):
            borne_basse = debut + indice * pas
            borne_haute = debut + (indice + 1) * pas
            if borne_basse <= mesure < borne_haute:
                effectifs[indice] += 1
                break

    return "\n".join(
        f"[{debut + indice * pas:.3f} ; {debut + (indice + 1) * pas:.3f}[ "
        + "*" * effectif
        for indice, effectif in enumerate(effectifs)
    )
