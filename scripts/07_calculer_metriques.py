"""
07_calculer_metriques.py
=========================
Phase P7 du protocole — Benchmark de LLM génériques (dataset RXA)

Calcule, à partir de `predictions_normalise.csv` (6000 lignes = 1500 textes x 4 modèles),
l'ensemble des métriques prévues en section 8 de la fiche protocole :

  - Accuracy, macro-F1, kappa de Cohen (mesure stricte ET conditionnelle)
  - Précision / rappel / F1 par classe (racisme, xenophobie, antisemitisme)
  - Matrices de confusion par modèle (stricte et conditionnelle)
  - Taux de refus (reponse_vide / parsing_echoue), stricte vs conditionnelle
  - Analyses stratifiées par sous_type (9 catégories) et source_generation (6 catégories)
  - Latence médiane par modèle
  - Analyses de confiance : calibration (confiance correct vs incorrect),
    courbes risque-couverture, confiance moyenne par sous_type

Politique de traitement des refus (cf. fiche protocole §7-8) :
  Un refus/reponse_vide compte comme une prédiction INCORRECTE en mesure stricte.
  En mesure conditionnelle, il est exclu (calcul uniquement sur les réponses exploitables).

Usage :
    python 07_calculer_metriques.py --input predictions_normalise.csv --outdir results

Sorties (dans --outdir) :
    metriques_globales.csv
    precision_rappel_par_classe.csv
    matrice_confusion_stricte_<modele>.csv
    matrice_confusion_conditionnelle_<modele>.csv
    taux_refus.csv
    stratification_sous_type.csv
    stratification_source_generation.csv
    latence_mediane.csv
    calibration_confiance.csv
    risque_couverture.csv
    confiance_par_sous_type.csv
"""

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    cohen_kappa_score,
    accuracy_score,
)

CLASSES = ["racisme", "xenophobie", "antisemitisme"]
LABEL_REFUS = "aucune_reponse"


# ---------------------------------------------------------------------------
# Chargement et préparation
# ---------------------------------------------------------------------------

def charger_donnees(chemin_csv: str) -> pd.DataFrame:
    df = pd.read_csv(chemin_csv)

    colonnes_attendues = {
        "id", "fournisseur", "modele", "verite", "sous_type", "source_generation",
        "label", "confiance", "probleme", "latence_ms", "essais", "erreur",
        "horodatage", "verite_norm", "label_norm", "correct",
    }
    manquantes = colonnes_attendues - set(df.columns)
    if manquantes:
        raise ValueError(f"Colonnes manquantes dans le CSV : {manquantes}")

    # 'correct' peut être lu comme bool ou comme string 'True'/'False'
    if df["correct"].dtype != bool:
        df["correct"] = df["correct"].astype(str).str.strip().str.lower() == "true"

    # y_pred stricte : les refus/parsing_echoue (label_norm vide) deviennent une
    # catégorie explicite distincte des 3 classes réelles, pour qu'ils comptent
    # comme faux négatifs dans le calcul du rappel sans jamais être compatibles
    # avec une classe réelle (donc sans jamais compter comme un vrai positif).
    df["label_norm_strict"] = df["label_norm"].fillna(LABEL_REFUS)
    df["est_refus"] = df["label_norm"].isna() | (df["probleme"].notna())

    return df


# ---------------------------------------------------------------------------
# Métriques globales (accuracy, macro-F1, kappa) — stricte et conditionnelle
# ---------------------------------------------------------------------------

def metriques_globales(df: pd.DataFrame) -> pd.DataFrame:
    lignes = []
    for modele, g in df.groupby("modele"):
        y_true = g["verite_norm"]
        y_pred_strict = g["label_norm_strict"]

        # --- Mesure stricte (refus = incorrect) ---
        acc_stricte = accuracy_score(y_true, y_pred_strict)
        f1_stricte = f1_score(y_true, y_pred_strict, labels=CLASSES, average="macro", zero_division=0)
        # kappa nécessite des labels comparables ; on inclut la catégorie refus
        # comme valeur possible de y_pred pour ne pas fausser l'accord observé/attendu.
        kappa_stricte = cohen_kappa_score(y_true, y_pred_strict, labels=CLASSES + [LABEL_REFUS])

        # --- Mesure conditionnelle (uniquement réponses exploitables) ---
        g_cond = g[~g["est_refus"]]
        if len(g_cond) > 0:
            y_true_c = g_cond["verite_norm"]
            y_pred_c = g_cond["label_norm"]
            acc_cond = accuracy_score(y_true_c, y_pred_c)
            f1_cond = f1_score(y_true_c, y_pred_c, labels=CLASSES, average="macro", zero_division=0)
            kappa_cond = cohen_kappa_score(y_true_c, y_pred_c, labels=CLASSES)
        else:
            acc_cond = f1_cond = kappa_cond = np.nan

        taux_refus = g["est_refus"].mean()

        lignes.append({
            "modele": modele,
            "n_total": len(g),
            "n_refus": int(g["est_refus"].sum()),
            "taux_refus_pct": round(taux_refus * 100, 2),
            "accuracy_stricte": round(acc_stricte, 4),
            "accuracy_conditionnelle": round(acc_cond, 4) if not np.isnan(acc_cond) else np.nan,
            "macro_f1_stricte": round(f1_stricte, 4),
            "macro_f1_conditionnelle": round(f1_cond, 4) if not np.isnan(f1_cond) else np.nan,
            "kappa_stricte": round(kappa_stricte, 4),
            "kappa_conditionnelle": round(kappa_cond, 4) if not np.isnan(kappa_cond) else np.nan,
        })

    return pd.DataFrame(lignes).sort_values("macro_f1_stricte", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Précision / rappel / F1 par classe (mesure stricte, refus = incorrect)
# ---------------------------------------------------------------------------

def precision_rappel_par_classe(df: pd.DataFrame) -> pd.DataFrame:
    lignes = []
    for modele, g in df.groupby("modele"):
        y_true = g["verite_norm"]
        y_pred = g["label_norm_strict"]
        precisions, rappels, f1s, supports = precision_recall_fscore_support(
            y_true, y_pred, labels=CLASSES, zero_division=0
        )
        for classe, p, r, f1, s in zip(CLASSES, precisions, rappels, f1s, supports):
            lignes.append({
                "modele": modele,
                "classe": classe,
                "precision": round(p, 4),
                "rappel": round(r, 4),
                "f1": round(f1, 4),
                "support": int(s),
            })
    return pd.DataFrame(lignes)


# ---------------------------------------------------------------------------
# Matrices de confusion (stricte : colonne "aucune_reponse" incluse)
# ---------------------------------------------------------------------------

def matrices_confusion(df: pd.DataFrame, outdir: Path) -> None:
    for modele, g in df.groupby("modele"):
        nom_fichier = re.sub(r"[^a-zA-Z0-9_-]", "_", modele)

        # Stricte : labels réels + catégorie refus, pour visualiser où partent les refus
        labels_strict = CLASSES + [LABEL_REFUS]
        cm_stricte = confusion_matrix(g["verite_norm"], g["label_norm_strict"], labels=labels_strict)
        df_cm_stricte = pd.DataFrame(cm_stricte, index=[f"vrai_{c}" for c in labels_strict],
                                      columns=[f"predit_{c}" for c in labels_strict])
        df_cm_stricte.to_csv(outdir / f"matrice_confusion_stricte_{nom_fichier}.csv")

        # Conditionnelle : uniquement réponses exploitables
        g_cond = g[~g["est_refus"]]
        if len(g_cond) > 0:
            cm_cond = confusion_matrix(g_cond["verite_norm"], g_cond["label_norm"], labels=CLASSES)
            df_cm_cond = pd.DataFrame(cm_cond, index=[f"vrai_{c}" for c in CLASSES],
                                       columns=[f"predit_{c}" for c in CLASSES])
            df_cm_cond.to_csv(outdir / f"matrice_confusion_conditionnelle_{nom_fichier}.csv")


# ---------------------------------------------------------------------------
# Taux de refus détaillé (par nature de problème)
# ---------------------------------------------------------------------------

def taux_refus_detail(df: pd.DataFrame) -> pd.DataFrame:
    lignes = []
    for modele, g in df.groupby("modele"):
        n = len(g)
        n_vide = (g["probleme"] == "reponse_vide").sum()
        n_parsing = (g["probleme"] == "parsing_echoue").sum()
        n_refus_total = g["est_refus"].sum()
        lignes.append({
            "modele": modele,
            "n_total": n,
            "n_reponse_vide": int(n_vide),
            "n_parsing_echoue": int(n_parsing),
            "n_refus_total": int(n_refus_total),
            "taux_refus_pct": round(n_refus_total / n * 100, 2),
        })
    return pd.DataFrame(lignes).sort_values("taux_refus_pct", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Analyses stratifiées (sous_type, source_generation)
# ---------------------------------------------------------------------------

def stratification(df: pd.DataFrame, colonne: str) -> pd.DataFrame:
    lignes = []
    for (modele, valeur), g in df.groupby(["modele", colonne]):
        y_true = g["verite_norm"]
        y_pred = g["label_norm_strict"]
        acc = accuracy_score(y_true, y_pred)
        f1m = f1_score(y_true, y_pred, labels=CLASSES, average="macro", zero_division=0)
        lignes.append({
            "modele": modele,
            colonne: valeur,
            "n": len(g),
            "accuracy_stricte": round(acc, 4),
            "macro_f1_stricte": round(f1m, 4),
            "taux_refus_pct": round(g["est_refus"].mean() * 100, 2),
        })
    return pd.DataFrame(lignes).sort_values(["modele", colonne]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Latence médiane
# ---------------------------------------------------------------------------

def latence_mediane(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("modele")["latence_ms"].agg(
        latence_mediane_ms="median",
        latence_p25_ms=lambda s: s.quantile(0.25),
        latence_p75_ms=lambda s: s.quantile(0.75),
        latence_max_ms="max",
    ).round(1)
    return g.reset_index().sort_values("latence_mediane_ms")


# ---------------------------------------------------------------------------
# Analyses de confiance (calibration, risque-couverture, par sous-type)
# Ces analyses sont purement descriptives : elles n'interviennent jamais
# dans le calcul de l'accuracy / macro-F1 / kappa ci-dessus.
# ---------------------------------------------------------------------------

def calibration_confiance(df: pd.DataFrame) -> pd.DataFrame:
    g_cond = df[~df["est_refus"]].copy()
    lignes = []
    for modele, g in g_cond.groupby("modele"):
        conf_correct = g.loc[g["correct"], "confiance"]
        conf_incorrect = g.loc[~g["correct"], "confiance"]
        lignes.append({
            "modele": modele,
            "confiance_mediane_correct": round(conf_correct.median(), 3) if len(conf_correct) else np.nan,
            "confiance_mediane_incorrect": round(conf_incorrect.median(), 3) if len(conf_incorrect) else np.nan,
            "ecart_confiance_correct_vs_incorrect": round(
                conf_correct.median() - conf_incorrect.median(), 3
            ) if len(conf_correct) and len(conf_incorrect) else np.nan,
            "n_correct": len(conf_correct),
            "n_incorrect": len(conf_incorrect),
        })
    return pd.DataFrame(lignes)


def risque_couverture(df: pd.DataFrame, seuils=None) -> pd.DataFrame:
    """Pour chaque modèle et chaque seuil de confiance, calcule la couverture
    (proportion de prédictions conservées) et l'accuracy sur ces prédictions
    conservées uniquement. Répond à : si on écarte les prédictions les moins
    sûres, quel modèle offre le meilleur compromis couverture/exactitude ?"""
    if seuils is None:
        seuils = [0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

    g_cond = df[~df["est_refus"]].copy()
    lignes = []
    for modele, g in g_cond.groupby("modele"):
        n_total_modele = len(g)
        for seuil in seuils:
            g_seuil = g[g["confiance"] >= seuil]
            couverture = len(g_seuil) / n_total_modele if n_total_modele else np.nan
            acc_seuil = g_seuil["correct"].mean() if len(g_seuil) else np.nan
            lignes.append({
                "modele": modele,
                "seuil_confiance": seuil,
                "couverture_pct": round(couverture * 100, 2) if not np.isnan(couverture) else np.nan,
                "accuracy_sur_predictions_retenues": round(acc_seuil, 4) if not np.isnan(acc_seuil) else np.nan,
                "n_retenu": len(g_seuil),
            })
    return pd.DataFrame(lignes)


def confiance_par_sous_type(df: pd.DataFrame) -> pd.DataFrame:
    g_cond = df[~df["est_refus"]].copy()
    resultat = g_cond.groupby(["modele", "sous_type"])["confiance"].agg(
        confiance_mediane="median", n="count"
    ).round(3).reset_index()
    return resultat.sort_values(["modele", "confiance_mediane"])


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Phase P7 — calcul des métriques du benchmark RXA")
    parser.add_argument("--input", default="predictions_normalise.csv", help="Chemin du CSV consolidé et normalisé")
    parser.add_argument("--outdir", default="outputs_P7", help="Dossier de sortie des CSV de résultats")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Chargement de {args.input} ...")
    df = charger_donnees(args.input)
    print(f"{len(df)} lignes chargées, {df['modele'].nunique()} modèles détectés : "
          f"{sorted(df['modele'].unique())}")

    print("Calcul des métriques globales (accuracy, macro-F1, kappa, taux de refus) ...")
    df_globales = metriques_globales(df)
    df_globales.to_csv(outdir / "metriques_globales.csv", index=False)
    print(df_globales.to_string(index=False))

    print("\nCalcul précision/rappel/F1 par classe ...")
    precision_rappel_par_classe(df).to_csv(outdir / "precision_rappel_par_classe.csv", index=False)

    print("Génération des matrices de confusion (stricte + conditionnelle) par modèle ...")
    matrices_confusion(df, outdir)

    print("Calcul du détail des refus (reponse_vide / parsing_echoue) ...")
    taux_refus_detail(df).to_csv(outdir / "taux_refus.csv", index=False)

    print("Analyses stratifiées par sous_type ...")
    stratification(df, "sous_type").to_csv(outdir / "stratification_sous_type.csv", index=False)

    print("Analyses stratifiées par source_generation ...")
    stratification(df, "source_generation").to_csv(outdir / "stratification_source_generation.csv", index=False)

    print("Calcul de la latence médiane par modèle ...")
    latence_mediane(df).to_csv(outdir / "latence_mediane.csv", index=False)

    print("Analyses de confiance : calibration, risque-couverture, confiance par sous-type ...")
    calibration_confiance(df).to_csv(outdir / "calibration_confiance.csv", index=False)
    risque_couverture(df).to_csv(outdir / "risque_couverture.csv", index=False)
    confiance_par_sous_type(df).to_csv(outdir / "confiance_par_sous_type.csv", index=False)

    print(f"\nTous les fichiers de résultats ont été écrits dans : {outdir.resolve()}")


if __name__ == "__main__":
    main()
