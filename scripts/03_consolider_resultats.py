"""
Phase P6 du protocole RXA — Consolidation des résultats.
Fusionne les fichiers raw_outputs/*.jsonl (un par modèle) en une table
unique predictions.csv, avec vérifications d'intégrité avant export.

Usage :
python scripts/02_consolider_resultats.py
"""

import json, pathlib
import pandas as pd

RAW_DIR = pathlib.Path("raw_outputs")
DATASET_PATH = pathlib.Path("data/dataset_eval.jsonl")
SORTIE = pathlib.Path("predictions.csv")


def charger_jsonl(chemin):
    with open(chemin, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    dataset = charger_jsonl(DATASET_PATH)
    ids_attendus = {item["id"] for item in dataset}
    print(f"Corpus de référence : {len(ids_attendus)} textes attendus par modèle.\n")

    fichiers = sorted(RAW_DIR.glob("*_p1.jsonl"))
    if not fichiers:
        print("Aucun fichier trouvé dans raw_outputs/. Vérifiez le chemin.")
        return

    toutes_lignes = []
    for chemin in fichiers:
        lignes = charger_jsonl(chemin)
        modele = lignes[0]["modele"] if lignes else chemin.stem

        ids_presents = [l["id"] for l in lignes]
        doublons = len(ids_presents) - len(set(ids_presents))
        manquants = ids_attendus - set(ids_presents)
        problemes = sum(1 for l in lignes if l.get("probleme") is not None)

        print(f"[{modele}] {chemin.name}")
        print(f"  {len(lignes)} lignes | {doublons} doublons | {len(manquants)} manquants | {problemes} problèmes ({problemes/len(lignes)*100:.1f}%)")
        if doublons:
            print(f"  ATTENTION : doublons détectés, à nettoyer avant de continuer.")
        if manquants:
            print(f"  ATTENTION : {len(manquants)} id manquants -> {list(manquants)[:5]}...")

        toutes_lignes.extend(lignes)
        print()

    df = pd.DataFrame(toutes_lignes)

    colonnes = [
        "id", "fournisseur", "modele", "verite", "sous_type", "source_generation",
        "label", "confiance", "probleme", "latence_ms", "essais", "erreur", "horodatage",
    ]
    df = df[[c for c in colonnes if c in df.columns]]

    df.to_csv(SORTIE, index=False, encoding="utf-8")
    print(f"\n{len(df)} lignes écrites dans {SORTIE} ({df['modele'].nunique()} modèles).")

    print("\nRécapitulatif par modèle :")
    recap = df.groupby("modele").agg(
        n=("id", "count"),
        problemes=("probleme", lambda x: x.notna().sum()),
        latence_mediane_ms=("latence_ms", "median"),
    )
    recap["taux_probleme_%"] = (recap["problemes"] / recap["n"] * 100).round(2)
    print(recap)


if __name__ == "__main__":
    main()
