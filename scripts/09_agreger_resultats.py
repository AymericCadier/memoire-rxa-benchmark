"""
05_agreger_resultats.py
=========================
Étape intermédiaire entre P7/P8 et la rédaction (P9) — Benchmark RXA

Objectif : réduire le nombre de fichiers de résultats à parcourir pour
l'interprétation, en fusionnant les fichiers de même granularité produits
par 03_calculer_metriques.py, SANS jamais toucher aux fichiers de
results/stats/ (P8) qui restent tels quels (déjà à la bonne granularité).

Fusions réalisées dans results/ :
  1. Les 8 matrices de confusion (4 stricte + 4 conditionnelle) par modèle
     -> matrices_confusion_stricte.csv + matrices_confusion_conditionnelle.csv
  2. metriques_globales + taux_refus (détail) + latence_mediane + calibration_confiance
     -> synthese_par_modele.csv (une ligne par modèle, jointure sur 'modele')
  3. stratification_sous_type + stratification_source_generation
     -> stratifications.csv (colonne 'dimension' + 'categorie')

Fichiers volontairement laissés tels quels (structure non fusionnable proprement) :
  - precision_rappel_par_classe.csv
  - confiance_par_sous_type.csv
  - risque_couverture.csv

En plus des CSV agrégés, génère un digest unique 'synthese_resultats.md'
qui compile tous les tableaux (P7 agrégés + P7 non fusionnés + P8) en
Markdown, prêt à être transmis à un LLM ou utilisé comme brouillon pour
la rédaction du chapitre de résultats.

Usage :
    python 05_agreger_resultats.py --results_dir results --stats_dir results/stats --outdir results/agrege
"""

import argparse
import re
from pathlib import Path

import pandas as pd


def lire_csv_si_existe(chemin: Path) -> pd.DataFrame | None:
    if chemin.exists():
        return pd.read_csv(chemin)
    print(f"  [absent, ignoré] {chemin.name}")
    return None


# ---------------------------------------------------------------------------
# 1. Fusion des matrices de confusion
# ---------------------------------------------------------------------------

def fusionner_matrices_confusion(results_dir: Path, outdir: Path) -> dict:
    sorties = {}
    for variante in ["stricte", "conditionnelle"]:
        fichiers = sorted(results_dir.glob(f"matrice_confusion_{variante}_*.csv"))
        if not fichiers:
            print(f"  [aucun fichier trouvé pour matrice_confusion_{variante}_*]")
            continue

        morceaux = []
        for fichier in fichiers:
            # Le nom de modèle a été assaini par 03_calculer_metriques.py
            # (caractères spéciaux remplacés par '_') ; on le récupère tel quel
            # comme identifiant, la correspondance exacte avec 'modele' se fait
            # ensuite via synthese_par_modele.csv si besoin de recoupement.
            nom_modele = fichier.stem.replace(f"matrice_confusion_{variante}_", "")
            df = pd.read_csv(fichier, index_col=0)
            df.insert(0, "modele", nom_modele)
            df.insert(1, "verite", df.index)
            morceaux.append(df.reset_index(drop=True))

        fusion = pd.concat(morceaux, ignore_index=True)
        nom_sortie = f"matrices_confusion_{variante}.csv"
        fusion.to_csv(outdir / nom_sortie, index=False)
        print(f"  -> {nom_sortie} ({len(fichiers)} fichiers fusionnés, {len(fusion)} lignes)")
        sorties[variante] = fusion
    return sorties


# ---------------------------------------------------------------------------
# 2. Synthèse par modèle (une ligne par modèle)
# ---------------------------------------------------------------------------

def construire_synthese_par_modele(results_dir: Path, outdir: Path) -> pd.DataFrame | None:
    df_metriques = lire_csv_si_existe(results_dir / "metriques_globales.csv")
    if df_metriques is None:
        print("  [synthese_par_modele.csv non généré : metriques_globales.csv manquant]")
        return None

    synthese = df_metriques.copy()

    df_refus = lire_csv_si_existe(results_dir / "taux_refus.csv")
    if df_refus is not None:
        colonnes_utiles = [c for c in df_refus.columns if c not in synthese.columns or c == "modele"]
        synthese = synthese.merge(df_refus[colonnes_utiles], on="modele", how="left")

    df_latence = lire_csv_si_existe(results_dir / "latence_mediane.csv")
    if df_latence is not None:
        synthese = synthese.merge(df_latence, on="modele", how="left")

    df_calibration = lire_csv_si_existe(results_dir / "calibration_confiance.csv")
    if df_calibration is not None:
        synthese = synthese.merge(df_calibration, on="modele", how="left")

    synthese = synthese.sort_values("macro_f1_stricte", ascending=False).reset_index(drop=True)
    synthese.to_csv(outdir / "synthese_par_modele.csv", index=False)
    print(f"  -> synthese_par_modele.csv ({len(synthese)} lignes, {len(synthese.columns)} colonnes)")
    return synthese


# ---------------------------------------------------------------------------
# 3. Fusion des stratifications
# ---------------------------------------------------------------------------

def fusionner_stratifications(results_dir: Path, outdir: Path) -> pd.DataFrame | None:
    morceaux = []

    df_sous_type = lire_csv_si_existe(results_dir / "stratification_sous_type.csv")
    if df_sous_type is not None:
        df_sous_type = df_sous_type.rename(columns={"sous_type": "categorie"})
        df_sous_type.insert(1, "dimension", "sous_type")
        morceaux.append(df_sous_type)

    df_source = lire_csv_si_existe(results_dir / "stratification_source_generation.csv")
    if df_source is not None:
        df_source = df_source.rename(columns={"source_generation": "categorie"})
        df_source.insert(1, "dimension", "source_generation")
        morceaux.append(df_source)

    if not morceaux:
        print("  [stratifications.csv non généré : aucun fichier source trouvé]")
        return None

    fusion = pd.concat(morceaux, ignore_index=True)
    fusion.to_csv(outdir / "stratifications.csv", index=False)
    print(f"  -> stratifications.csv ({len(fusion)} lignes)")
    return fusion


# ---------------------------------------------------------------------------
# Génération du digest Markdown unique (P7 agrégé + non fusionné + P8)
# ---------------------------------------------------------------------------

def df_vers_markdown(df: pd.DataFrame, max_lignes: int = 200) -> str:
    if len(df) > max_lignes:
        return df.head(max_lignes).to_markdown(index=False) + f"\n\n*(tronqué à {max_lignes} lignes sur {len(df)})*"
    return df.to_markdown(index=False)


def generer_digest_markdown(outdir: Path, results_dir: Path, stats_dir: Path,
                             synthese: pd.DataFrame | None,
                             stratifs: pd.DataFrame | None,
                             matrices: dict) -> None:
    sections = ["# Synthèse des résultats — Benchmark RXA (phases P7 et P8)\n"]

    if synthese is not None:
        sections.append("## Synthèse par modèle (P7)\n")
        sections.append(df_vers_markdown(synthese))
        sections.append("\n")

    df_precision = lire_csv_si_existe(results_dir / "precision_rappel_par_classe.csv")
    if df_precision is not None:
        sections.append("## Précision / rappel / F1 par classe (P7)\n")
        sections.append(df_vers_markdown(df_precision))
        sections.append("\n")

    if stratifs is not None:
        sections.append("## Analyses stratifiées : sous_type et source_generation (P7)\n")
        sections.append(df_vers_markdown(stratifs))
        sections.append("\n")

    if "stricte" in matrices:
        sections.append("## Matrices de confusion — mesure stricte (P7)\n")
        sections.append(df_vers_markdown(matrices["stricte"]))
        sections.append("\n")

    if "conditionnelle" in matrices:
        sections.append("## Matrices de confusion — mesure conditionnelle (P7)\n")
        sections.append(df_vers_markdown(matrices["conditionnelle"]))
        sections.append("\n")

    df_confiance_sous_type = lire_csv_si_existe(results_dir / "confiance_par_sous_type.csv")
    if df_confiance_sous_type is not None:
        sections.append("## Confiance médiane par sous-type (P7)\n")
        sections.append(df_vers_markdown(df_confiance_sous_type))
        sections.append("\n")

    df_risque_couverture = lire_csv_si_existe(results_dir / "risque_couverture.csv")
    if df_risque_couverture is not None:
        sections.append("## Courbes risque-couverture (P7)\n")
        sections.append(df_vers_markdown(df_risque_couverture))
        sections.append("\n")

    # --- Section P8 : lue depuis stats_dir, jamais fusionnée ---
    sections.append("## Test Q de Cochran (P8)\n")
    df_cochran = lire_csv_si_existe(stats_dir / "cochran_q.csv")
    if df_cochran is not None:
        sections.append(df_vers_markdown(df_cochran))
        sections.append("\n")

    sections.append("## McNemar par paires, correction de Bonferroni (P8)\n")
    df_mcnemar = lire_csv_si_existe(stats_dir / "mcnemar_paires.csv")
    if df_mcnemar is not None:
        sections.append(df_vers_markdown(df_mcnemar))
        sections.append("\n")

    sections.append("## Intervalles de confiance bootstrap par modèle (P8)\n")
    df_bootstrap_modeles = lire_csv_si_existe(stats_dir / "bootstrap_ic_modeles.csv")
    if df_bootstrap_modeles is not None:
        sections.append(df_vers_markdown(df_bootstrap_modeles))
        sections.append("\n")

    sections.append("## Intervalles de confiance bootstrap sur les écarts par paire (P8)\n")
    df_bootstrap_diff = lire_csv_si_existe(stats_dir / "bootstrap_ic_differences_paires.csv")
    if df_bootstrap_diff is not None:
        sections.append(df_vers_markdown(df_bootstrap_diff))
        sections.append("\n")

    chemin_digest = outdir / "synthese_resultats.md"
    chemin_digest.write_text("\n".join(sections), encoding="utf-8")
    print(f"\nDigest Markdown généré : {chemin_digest.resolve()}")


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Agrégation des résultats P7/P8 et génération d'un digest Markdown")
    parser.add_argument("--results_dir", default="results", help="Dossier contenant les sorties de 03_calculer_metriques.py")
    parser.add_argument("--stats_dir", default="results/stats", help="Dossier contenant les sorties de 04_tests_statistiques.py")
    parser.add_argument("--outdir", default="results/agrege", help="Dossier de sortie des fichiers agrégés")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    stats_dir = Path(args.stats_dir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("1. Fusion des matrices de confusion ...")
    matrices = fusionner_matrices_confusion(results_dir, outdir)

    print("\n2. Construction de la synthèse par modèle ...")
    synthese = construire_synthese_par_modele(results_dir, outdir)

    print("\n3. Fusion des stratifications ...")
    stratifs = fusionner_stratifications(results_dir, outdir)

    print("\n4. Génération du digest Markdown unique ...")
    generer_digest_markdown(outdir, results_dir, stats_dir, synthese, stratifs, matrices)

    print(f"\nFichiers agrégés écrits dans : {outdir.resolve()}")
    print("Fichiers laissés inchangés (structure non fusionnable) : "
          "precision_rappel_par_classe.csv, confiance_par_sous_type.csv, risque_couverture.csv "
          f"(à consulter directement dans {results_dir.resolve()})")
    print(f"Dossier stats/ (P8) non modifié : {stats_dir.resolve()}")


if __name__ == "__main__":
    main()
