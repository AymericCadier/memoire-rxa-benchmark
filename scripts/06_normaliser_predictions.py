"""
Normalise les accents de la colonne 'verite' dans predictions.csv pour
qu'elle soit directement comparable a la colonne 'label' (qui utilise les
valeurs sans accent definies dans le prompt : racisme/xenophobie/antisemitisme).

Ajoute une colonne 'verite_norm' plutot que d'ecraser 'verite', pour
conserver l'orthographe originale du dataset (utile pour l'affichage dans
le memoire) tout en ayant une colonne exploitable pour les calculs.

Usage :
python scripts/04_normaliser_predictions.py
"""

import unicodedata
import pandas as pd

ENTREE = "predictions.csv"
SORTIE = "predictions_normalise.csv"


def normaliser(s):
    if pd.isna(s):
        return s
    return "".join(
        c for c in unicodedata.normalize("NFD", str(s))
        if unicodedata.category(c) != "Mn"
    ).lower()


def main():
    df = pd.read_csv(ENTREE)

    df["verite_norm"] = df["verite"].apply(normaliser)
    df["label_norm"] = df["label"].apply(normaliser)  # sécurité, au cas où

    valides = {"racisme", "xenophobie", "antisemitisme"}
    inattendu_verite = set(df["verite_norm"].dropna().unique()) - valides
    inattendu_label = set(df["label_norm"].dropna().unique()) - valides
    if inattendu_verite:
        print(f"ATTENTION : valeurs inattendues dans verite_norm -> {inattendu_verite}")
    if inattendu_label:
        print(f"ATTENTION : valeurs inattendues dans label_norm -> {inattendu_label}")

    df["correct"] = df["verite_norm"] == df["label_norm"]

    df.to_csv(SORTIE, index=False, encoding="utf-8")
    print(f"{len(df)} lignes écrites dans {SORTIE}")

    print("\nExactitude globale par modèle (mesure stricte, refus = incorrect) :")
    recap = df.groupby("modele").agg(
        n=("id", "count"),
        n_correct=("correct", "sum"),
        n_refus=("probleme", lambda x: x.notna().sum()),
    )
    recap["accuracy_stricte_%"] = (recap["n_correct"] / recap["n"] * 100).round(2)
    print(recap)


if __name__ == "__main__":
    main()
