"""
Suivi de traitement en direct pour 01_run_modele_avec_suivi.py.

Lit etat_run.json toutes les quelques secondes et affiche une table
de progression par modèle, sans toucher aux fichiers raw_outputs.
A lancer dans un second terminal pendant le run --complet.

Usage : python scripts/02_suivi_run.py
"""

import json, time, pathlib, sys

ETAT_FICHIER = pathlib.Path("etat_run.json")
INTERVALLE_S = 5
SEUIL_ALERTE_S = 180  # pas de mise à jour depuis > 3 min -> suspect (crash / blocage)


def charger():
    if not ETAT_FICHIER.exists():
        return {}
    try:
        return json.loads(ETAT_FICHIER.read_text(encoding="utf-8"))
    except Exception:
        return {}


def afficher(etat):
    now = time.time()
    print("\033[H\033[J", end="")  # clear écran
    print(f"Suivi run — {time.strftime('%H:%M:%S')}\n")
    print(f"{'modele':<35} {'statut':<20} {'progression':<15} {'erreurs':<8} {'derniere_maj'}")
    print("-" * 100)
    for modele, info in etat.items():
        traites = info.get("traites", 0)
        total = info.get("total", "?")
        statut = info.get("statut", "?")
        erreurs = info.get("erreurs", 0)
        derniere_maj = info.get("derniere_maj", "-")
        alerte = ""
        if derniere_maj != "-":
            try:
                t = time.mktime(time.strptime(derniere_maj, "%Y-%m-%dT%H:%M:%S"))
                if statut == "en_cours" and (now - t) > SEUIL_ALERTE_S:
                    alerte = "  <-- AUCUNE MAJ DEPUIS PLUS DE 3 MIN, VERIFIER"
            except Exception:
                pass
        progression = f"{traites}/{total}"
        print(f"{modele:<35} {statut:<20} {progression:<15} {erreurs:<8} {derniere_maj}{alerte}")
    print()
    for modele, info in etat.items():
        if info.get("statut") == "arrete_credentials":
            print(f"ATTENTION : {modele} arrêté sur erreur de credentials/quota -> {info.get('cause')}")
        if info.get("statut") == "arrete_erreur":
            print(f"ATTENTION : {modele} arrêté sur erreur inattendue -> {info.get('cause')}")


if __name__ == "__main__":
    try:
        while True:
            afficher(charger())
            time.sleep(INTERVALLE_S)
    except KeyboardInterrupt:
        sys.exit(0)
