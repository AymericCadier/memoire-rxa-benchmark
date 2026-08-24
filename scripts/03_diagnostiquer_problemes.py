"""
Diagnostic complémentaire à la phase P6 — répartition des types de
'probleme' par modèle, pour décider si le taux d'erreur observé sur le
run complet (au-dessus du seuil pilote de 2%) nécessite une action.

Usage :
python scripts/03_diagnostiquer_problemes.py
"""

import pandas as pd

df = pd.read_csv("predictions.csv")

for modele in df["modele"].unique():
    sous = df[df["modele"] == modele]
    n_pb = sous["probleme"].notna().sum()
    if n_pb == 0:
        continue
    print(f"\n=== {modele} : {n_pb} problèmes sur {len(sous)} ({n_pb/len(sous)*100:.1f}%) ===")
    print(sous["probleme"].value_counts())

    # Répartition des problèmes par sous_type et source_generation, pour
    # voir si les erreurs sont concentrées sur des cas précis ou diffuses
    print("\nPar sous_type :")
    print(sous[sous["probleme"].notna()]["sous_type"].value_counts())
    print("\nPar source_generation :")
    print(sous[sous["probleme"].notna()]["source_generation"].value_counts())
