"""
Retire des fichiers raw_outputs/*.jsonl les lignes en erreur liées à un
quota JOURNALIER (tokens/day, requests/day, neurons Cloudflare), pour
que le mécanisme de reprise natif de 01_run_modele.py les retraite lors
d'un prochain lancement (une fois le quota réinitialisé).

Ne touche PAS aux autres types de 'probleme' (reponse_vide sans erreur
réseau, parsing_echoue, label_invalide) : ceux-là restent tels quels,
ce sont des résultats de fond du modèle, pas des incidents d'infra.

Usage :
python scripts/05_nettoyer_pour_repasse.py
python scripts/05_nettoyer_pour_repasse.py --confirmer   (pour écrire réellement)
"""

import json, pathlib, re, argparse, shutil

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


def main(confirmer):
    fichiers = sorted(RAW_DIR.glob("*_p1.jsonl"))
    if not fichiers:
        print("Aucun fichier trouvé dans raw_outputs/.")
        return

    for chemin in fichiers:
        lignes = charger_jsonl(chemin)
        modele = lignes[0]["modele"] if lignes else chemin.stem

        propres = [l for l in lignes if not est_quota_journalier(l.get("erreur"))]
        retirees = [l for l in lignes if est_quota_journalier(l.get("erreur"))]

        if not retirees:
            continue

        print(f"[{modele}] {chemin.name} : {len(retirees)} lignes à retirer sur {len(lignes)}")

        if confirmer:
            sauvegarde = chemin.with_suffix(chemin.suffix + ".backup")
            shutil.copy(chemin, sauvegarde)
            with chemin.open("w", encoding="utf-8") as f:
                for l in propres:
                    f.write(json.dumps(l, ensure_ascii=False) + "\n")
            print(f"  -> fichier nettoyé, sauvegarde faite dans {sauvegarde.name}")
        else:
            print("  -> mode simulation, rien écrit (relancez avec --confirmer pour appliquer)")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirmer", action="store_true")
    args = parser.parse_args()
    main(args.confirmer)
