"""
08_tests_statistiques.py
==========================
Phase P8 du protocole — Benchmark de LLM génériques (dataset RXA)

À partir de `predictions_normalise.csv` (mesure stricte : un refus/reponse_vide
compte comme une prédiction incorrecte, conformément à la politique actée en
phase P5/P7), calcule les trois familles de tests prévues en section 8 de la
fiche protocole :

  1. McNemar par paires (6 paires pour 4 modèles), avec version binomiale
     exacte si b + c < 25, sinon approximation du khi-deux avec correction
     de continuité. Correction de Bonferroni : alpha ajusté = 0,05 / 6.
  2. Test Q de Cochran (test global d'égalité des taux de succès sur les
     4 modèles simultanément — préalable recommandé avant les comparaisons
     par paires, pour limiter l'inflation du risque de première espèce).
  3. Intervalles de confiance bootstrap non paramétrique (1000 ré-échantillonnages,
     seed = 42) sur l'accuracy stricte et le macro-F1 stricte de chaque modèle,
     et sur l'écart de macro-F1 entre chaque paire de modèles.

Usage :
    python 08_tests_statistiques.py --input predictions_normalise.csv --outdir stats

Sorties (dans --outdir) :
    mcnemar_paires.csv
    cochran_q.csv
    bootstrap_ic_modeles.csv
    bootstrap_ic_differences_paires.csv
"""

import argparse
import itertools
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, chi2
from sklearn.metrics import f1_score, accuracy_score
from statsmodels.stats.contingency_tables import cochrans_q

CLASSES = ["racisme", "xenophobie", "antisemitisme"]
LABEL_REFUS = "aucune_reponse"
SEED = 42
N_RESAMPLES = 1000
ALPHA = 0.05


# ---------------------------------------------------------------------------
# Chargement et mise en forme
# ---------------------------------------------------------------------------

def charger_donnees(chemin_csv: str) -> pd.DataFrame:
    df = pd.read_csv(chemin_csv)

    if df["correct"].dtype != bool:
        df["correct"] = df["correct"].astype(str).str.strip().str.lower() == "true"

    # Mesure stricte : un refus (label_norm vide) est une prédiction incorrecte.
    # 'correct' est déjà False sur ces lignes dans le fichier normalisé, on le
    # revérifie explicitement pour ne dépendre d'aucune hypothèse implicite.
    df["label_norm_strict"] = df["label_norm"].fillna(LABEL_REFUS)
    df.loc[df["label_norm"].isna(), "correct"] = False

    return df


def pivot_correct(df: pd.DataFrame) -> pd.DataFrame:
    """Tableau large id x modele -> correct (bool), un texte par ligne.
    Nécessaire pour McNemar (comparaisons appariées) et pour Cochran's Q."""
    large = df.pivot(index="id", columns="modele", values="correct")
    if large.isna().any().any():
        manquants = large.isna().sum()
        raise ValueError(
            f"Des couples (id, modele) sont manquants après pivot : {manquants[manquants > 0].to_dict()}. "
            "Vérifier la consolidation (chaque texte doit avoir une prédiction par modèle)."
        )
    return large.astype(bool)


def pivot_labels(df: pd.DataFrame):
    """Renvoie verite_norm par id (série) et label_norm_strict par modèle (dict id->label),
    nécessaires pour recalculer le macro-F1 sur un sous-échantillon bootstrap."""
    verite = df.drop_duplicates("id").set_index("id")["verite_norm"]
    labels_par_modele = {
        modele: g.set_index("id")["label_norm_strict"]
        for modele, g in df.groupby("modele")
    }
    return verite, labels_par_modele


# ---------------------------------------------------------------------------
# 1. McNemar par paires + correction de Bonferroni
# ---------------------------------------------------------------------------

def test_mcnemar_paires(large: pd.DataFrame) -> pd.DataFrame:
    modeles = list(large.columns)
    paires = list(itertools.combinations(modeles, 2))
    n_paires = len(paires)
    alpha_ajuste = ALPHA / n_paires

    lignes = []
    for modele_a, modele_b in paires:
        correct_a = large[modele_a]
        correct_b = large[modele_b]

        # b = A correct et B incorrect ; c = A incorrect et B correct
        b = int(((correct_a) & (~correct_b)).sum())
        c = int(((~correct_a) & (correct_b)).sum())

        if b + c == 0:
            # Aucune paire discordante : les deux modèles se trompent/réussissent
            # exactement sur les mêmes textes, test non informatif.
            methode = "non_applicable_b_plus_c_nul"
            statistique = np.nan
            p_value = 1.0
        elif b + c < 25:
            # Version binomiale exacte (recommandée pour petits effectifs discordants)
            methode = "binomiale_exacte"
            resultat = binomtest(k=min(b, c), n=b + c, p=0.5, alternative="two-sided")
            statistique = min(b, c)
            p_value = resultat.pvalue
        else:
            # Approximation du khi-deux avec correction de continuité de Yates
            methode = "khi2_continuite"
            statistique = (abs(b - c) - 1) ** 2 / (b + c)
            p_value = 1 - chi2.cdf(statistique, df=1)

        significatif_brut = p_value < ALPHA
        significatif_ajuste = p_value < alpha_ajuste

        lignes.append({
            "modele_a": modele_a,
            "modele_b": modele_b,
            "n_discordant_b_A_correct_B_incorrect": b,
            "n_discordant_c_A_incorrect_B_correct": c,
            "b_plus_c": b + c,
            "methode": methode,
            "statistique": round(statistique, 4) if not np.isnan(statistique) else np.nan,
            "p_value": round(p_value, 6),
            "alpha_brut": ALPHA,
            "significatif_alpha_brut": significatif_brut,
            "alpha_ajuste_bonferroni": round(alpha_ajuste, 6),
            "significatif_alpha_ajuste": significatif_ajuste,
        })

    return pd.DataFrame(lignes).sort_values("p_value").reset_index(drop=True)


# ---------------------------------------------------------------------------
# 2. Test Q de Cochran (test global sur les 4 modèles)
# ---------------------------------------------------------------------------

def test_q_cochran(large: pd.DataFrame) -> pd.DataFrame:
    matrice = large.astype(int).to_numpy()  # n_textes x n_modeles, valeurs 0/1
    resultat = cochrans_q(matrice)

    return pd.DataFrame([{
        "n_textes": matrice.shape[0],
        "n_modeles": matrice.shape[1],
        "statistique_Q": round(resultat.statistic, 4),
        "ddl": matrice.shape[1] - 1,
        "p_value": resultat.pvalue,
        "significatif_alpha_0_05": resultat.pvalue < ALPHA,
        "interpretation": (
            "Au moins un modèle diffère significativement des autres en taux de succès ; "
            "des comparaisons par paires (McNemar) sont justifiées."
            if resultat.pvalue < ALPHA else
            "Aucune différence globale significative détectée entre les 4 modèles ; "
            "les comparaisons par paires doivent être interprétées avec prudence."
        ),
    }])


# ---------------------------------------------------------------------------
# 3. Intervalles de confiance bootstrap non paramétrique
# ---------------------------------------------------------------------------

def _macro_f1_echantillon(verite: pd.Series, labels_par_modele: dict, ids_echantillon: np.ndarray, modele: str) -> float:
    y_true = verite.loc[ids_echantillon].to_numpy()
    y_pred = labels_par_modele[modele].loc[ids_echantillon].to_numpy()
    return f1_score(y_true, y_pred, labels=CLASSES, average="macro", zero_division=0)


def bootstrap_ic_modeles(verite: pd.Series, labels_par_modele: dict, large: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)  # seed consignée dans la fiche protocole
    ids = verite.index.to_numpy()
    n = len(ids)
    modeles = list(large.columns)

    resultats_f1 = {m: [] for m in modeles}
    resultats_acc = {m: [] for m in modeles}

    for _ in range(N_RESAMPLES):
        echantillon = rng.choice(ids, size=n, replace=True)
        for modele in modeles:
            resultats_f1[modele].append(_macro_f1_echantillon(verite, labels_par_modele, echantillon, modele))
            resultats_acc[modele].append(large.loc[echantillon, modele].mean())

    lignes = []
    for modele in modeles:
        f1_arr = np.array(resultats_f1[modele])
        acc_arr = np.array(resultats_acc[modele])
        lignes.append({
            "modele": modele,
            "macro_f1_moyen_bootstrap": round(f1_arr.mean(), 4),
            "macro_f1_ic95_bas": round(np.percentile(f1_arr, 2.5), 4),
            "macro_f1_ic95_haut": round(np.percentile(f1_arr, 97.5), 4),
            "accuracy_moyenne_bootstrap": round(acc_arr.mean(), 4),
            "accuracy_ic95_bas": round(np.percentile(acc_arr, 2.5), 4),
            "accuracy_ic95_haut": round(np.percentile(acc_arr, 97.5), 4),
        })

    return pd.DataFrame(lignes).sort_values("macro_f1_moyen_bootstrap", ascending=False).reset_index(drop=True)


def bootstrap_ic_differences_paires(verite: pd.Series, labels_par_modele: dict, large: pd.DataFrame) -> pd.DataFrame:
    """IC bootstrap sur l'écart de macro-F1 entre chaque paire de modèles.
    Si l'IC à 95% de la différence exclut 0, l'écart est jugé stable au
    ré-échantillonnage (corrobore un résultat McNemar significatif)."""
    rng = np.random.default_rng(SEED)
    ids = verite.index.to_numpy()
    n = len(ids)
    modeles = list(large.columns)
    paires = list(itertools.combinations(modeles, 2))

    differences = {paire: [] for paire in paires}

    for _ in range(N_RESAMPLES):
        echantillon = rng.choice(ids, size=n, replace=True)
        f1_par_modele = {
            modele: _macro_f1_echantillon(verite, labels_par_modele, echantillon, modele)
            for modele in modeles
        }
        for modele_a, modele_b in paires:
            differences[(modele_a, modele_b)].append(f1_par_modele[modele_a] - f1_par_modele[modele_b])

    lignes = []
    for (modele_a, modele_b), valeurs in differences.items():
        arr = np.array(valeurs)
        ic_bas, ic_haut = np.percentile(arr, [2.5, 97.5])
        lignes.append({
            "modele_a": modele_a,
            "modele_b": modele_b,
            "difference_macro_f1_moyenne": round(arr.mean(), 4),
            "ic95_bas": round(ic_bas, 4),
            "ic95_haut": round(ic_haut, 4),
            "ic_exclut_zero": bool(ic_bas > 0 or ic_haut < 0),
        })

    return pd.DataFrame(lignes).sort_values("difference_macro_f1_moyenne", ascending=False, key=abs).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Phase P8 — tests statistiques du benchmark RXA")
    parser.add_argument("--input", default="predictions_normalise.csv", help="Chemin du CSV consolidé et normalisé")
    parser.add_argument("--outdir", default="outputs_P8", help="Dossier de sortie des CSV de résultats")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Chargement de {args.input} ...")
    df = charger_donnees(args.input)
    large = pivot_correct(df)
    verite, labels_par_modele = pivot_labels(df)
    print(f"{large.shape[0]} textes x {large.shape[1]} modèles : {list(large.columns)}")

    print("\n1. Test de McNemar par paires (mesure stricte) ...")
    df_mcnemar = test_mcnemar_paires(large)
    df_mcnemar.to_csv(outdir / "mcnemar_paires.csv", index=False)
    print(df_mcnemar.to_string(index=False))

    print("\n2. Test Q de Cochran (test global sur les 4 modèles) ...")
    df_cochran = test_q_cochran(large)
    df_cochran.to_csv(outdir / "cochran_q.csv", index=False)
    print(df_cochran.to_string(index=False))

    print(f"\n3. Intervalles de confiance bootstrap ({N_RESAMPLES} ré-échantillonnages, seed={SEED}) ...")
    print("   Calcul en cours par modèle (macro-F1 et accuracy) ...")
    df_bootstrap_modeles = bootstrap_ic_modeles(verite, labels_par_modele, large)
    df_bootstrap_modeles.to_csv(outdir / "bootstrap_ic_modeles.csv", index=False)
    print(df_bootstrap_modeles.to_string(index=False))

    print("   Calcul en cours par paire (écart de macro-F1) ...")
    df_bootstrap_diff = bootstrap_ic_differences_paires(verite, labels_par_modele, large)
    df_bootstrap_diff.to_csv(outdir / "bootstrap_ic_differences_paires.csv", index=False)
    print(df_bootstrap_diff.to_string(index=False))

    print(f"\nTous les fichiers de résultats ont été écrits dans : {outdir.resolve()}")


if __name__ == "__main__":
    main()
