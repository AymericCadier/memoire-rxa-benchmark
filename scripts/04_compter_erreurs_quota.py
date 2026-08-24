"""
Compte, par fichier raw_outputs/*.jsonl, le nombre de lignes en erreur
liées à un plafond JOURNALIER de quota (pas un simple 429 récupérable
en quelques secondes) :
- Groq  : "tokens per day" / "TPD" / "requests per day" / "RPD"
- Cloudflare : "neurons" / "daily free allocation"

Ces cas ne peuvent pas être corrigés par un simple retry immédiat : il
faut attendre la réinitialisation du quota journalier avant de rejouer
les textes concernés.

Usage :
python scripts/04_compter_erreurs_quota.py
"""

import json, pathlib, re

RAW_DIR = pathlib.Path("raw_outputs")

MOTIFS_QUOTA_JOURNALIER = [
    r"tokens per day",
    r"\bTPD\b",
    r"requests per day",
    r"\bRPD\b",
    r"neurons",
    r"daily free allocation",
    r"daily limit",
]
REGEX_QUOTA = re.compile("|".join(MOTIFS_QUOTA_JOURNALIER), re.IGNORECASE)


def charger_jsonl(chemin):
    with open(chemin, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def est_quota_journalier(erreur):
    if not erreur:
        return False
    return bool(REGEX_QUOTA.search(str(erreur)))


def main():
    fichiers = sorted(RAW_DIR.glob("*_p1.jsonl"))
    if not fichiers:
        print("Aucun fichier trouvé dans raw_outputs/.")
        return

    total_global = 0
    for chemin in fichiers:
        lignes = charger_jsonl(chemin)
        modele = lignes[0]["modele"] if lignes else chemin.stem

        en_erreur = [l for l in lignes if l.get("erreur")]
        quota = [l for l in en_erreur if est_quota_journalier(l["erreur"])]
        autres = [l for l in en_erreur if not est_quota_journalier(l["erreur"])]

        print(f"[{modele}] {chemin.name}")
        print(f"  {len(lignes)} lignes | {len(en_erreur)} en erreur au total")
        print(f"    -> {len(quota)} liées à un quota journalier (à rejouer après reset)")
        print(f"    -> {len(autres)} autres erreurs (à examiner séparément)")
        if quota:
            ids = [l["id"] for l in quota]
            print(f"    ids concernés (aperçu) : {ids[:5]}{'...' if len(ids) > 5 else ''}")
        print()
        total_global += len(quota)

    print(f"Total tous modèles confondus : {total_global} textes bloqués par un quota journalier.")


if __name__ == "__main__":
    main()
