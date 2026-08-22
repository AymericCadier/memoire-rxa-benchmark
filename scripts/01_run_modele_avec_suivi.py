"""
Phase P4/P5 du protocole RXA — Run pilote et exécution complète.
Version avec suivi de traitement (état persistant + logs fichier)
pour se remettre d'un crash ou d'une expiration de clé API sans
perdre le fil de ce qui a déjà été traité.

Nouveautés par rapport à 01_run_modele.py :
  - etat_run.json : état global (thread-safe, écriture atomique),
    mis à jour à chaque texte traité. Permet de savoir en un coup
    d'oeil où en est chaque modèle sans ouvrir les raw_outputs.
  - logs/run_*.log : trace complète sur disque (en plus de la console),
    survit à un crash de terminal / coupure de session.
  - Distinction erreur récupérable (429/500/502/503/timeout) vs
    erreur fatale (401/403/invalid_api_key/insufficient_quota) :
    sur erreur fatale on arrête immédiatement ce fournisseur au lieu
    d'épuiser tous les essais sur chaque texte restant.

Usage : identique au script original.
  python scripts/01_run_modele_avec_suivi.py --pilote
  python scripts/01_run_modele_avec_suivi.py --complet

Suivi en parallèle (autre terminal) :
  python scripts/02_suivi_run.py
"""

import json, os, time, random, pathlib, argparse, logging, threading, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

TIMEOUT_REQUETE = 45
CLOUDFLARE_ACCOUNT_ID = "13c530a2588696e224178f7d60634329"

ETAT_FICHIER = pathlib.Path("etat_run.json")
ETAT_LOCK = threading.Lock()

LOG_DIR = pathlib.Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_PATH = LOG_DIR / f"run_{time.strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),  # garde l'affichage console habituel
    ],
)
log = logging.getLogger("run_modele")

# Marqueurs de rate-limit / indisponibilité temporaire -> on retente.
ERREURS_RECUPERABLES = ("429", "500", "502", "503", "timeout", "Timeout")
# Marqueurs de credentials/quota invalides -> inutile de retenter, on arrête ce fournisseur.
ERREURS_FATALES = (
    "401", "403", "invalid_api_key", "Unauthorized", "authentication",
    "insufficient_quota", "PERMISSION_DENIED", "API_KEY_INVALID",
)

PROVIDERS = {
    "groq_gptoss": {
        "base_url": "https://api.groq.com/openai/v1",
        "key": os.environ.get("GROQ_API_KEY"),
        "rpm": 10, "max_tokens": 400, "max_essais": 5, "extra": {},
        "modeles": ["openai/gpt-oss-120b"],
    },
    # "groq_allam": {
    #     "base_url": "https://api.groq.com/openai/v1",
    #     "key": os.environ.get("GROQ_API_KEY"),
    #     "rpm": 10, "max_tokens": 300, "max_essais": 5, "extra": {},
    #     "modeles": ["allam-2-7b"],
    # },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key": os.environ.get("GEMINI_API_KEY"),
        "rpm": 15, "max_tokens": 200, "max_essais": 5, "extra": {},
        "modeles": ["gemini-3.5-flash-lite"],
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "key": os.environ.get("MISTRAL_API_KEY"),
        "rpm": 15, "max_tokens": 200, "max_essais": 8, "extra": {},
        "modeles": ["mistral-large-latest"],
    },
    "cloudflare": {
        "base_url": f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/v1",
        "key": os.environ.get("CLOUDFLARE_API_KEY"),
        "rpm": 20, "max_tokens": 300, "max_essais": 5, "extra": {},
        "modeles": ["@cf/meta/llama-3.3-70b-instruct-fp8-fast"],
    },
}

SYSTEM_PROMPT = pathlib.Path("prompts/prompt_v1.txt").read_text(encoding="utf-8")
USER_TPL = 'Texte a classer :\n"""\n{texte}\n"""\n\nReponds uniquement par le JSON demande.'
VALID = {"racisme", "xenophobie", "antisemitisme"}


# ---------------------------------------------------------------------------
# Suivi de traitement : état global thread-safe, écriture atomique
# ---------------------------------------------------------------------------
def _lire_etat():
    if ETAT_FICHIER.exists():
        try:
            return json.loads(ETAT_FICHIER.read_text(encoding="utf-8"))
        except Exception:
            log.warning("etat_run.json illisible, recréation.")
    return {}


def maj_etat(modele, **champs):
    with ETAT_LOCK:
        etat = _lire_etat()
        entree = etat.get(modele, {})
        entree.update(champs)
        entree["derniere_maj"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        etat[modele] = entree
        with tempfile.NamedTemporaryFile(
            "w", dir=ETAT_FICHIER.parent or ".", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(etat, tmp, ensure_ascii=False, indent=2)
            tmp_path = tmp.name
        for tentative in range(5):
            try:
                os.replace(tmp_path, ETAT_FICHIER)
                return
            except PermissionError:
                time.sleep(0.3 * (tentative + 1))
        os.replace(tmp_path, ETAT_FICHIER)  # dernière tentative, laisse planter si ça persiste


def classifier_erreur(msg: str) -> str:
    if any(x in msg for x in ERREURS_FATALES):
        return "fatale"
    if any(x in msg for x in ERREURS_RECUPERABLES) or "rate limit" in msg.lower():
        return "recuperable"
    return "inconnue"


class ErreurFataleFournisseur(Exception):
    """Levée quand un fournisseur renvoie une erreur de credentials/quota définitive."""


def classer(client, modele, texte, max_tokens, extra, max_essais):
    for essai in range(max_essais):
        t0 = time.perf_counter()
        try:
            rep = client.chat.completions.create(
                model=modele,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_TPL.format(texte=texte)},
                ],
                temperature=0, top_p=1, max_tokens=max_tokens,
                timeout=TIMEOUT_REQUETE,
                extra_body=extra if extra else None,
            )
            brut = rep.choices[0].message.content
            return {"brut": brut, "latence_ms": round((time.perf_counter() - t0) * 1000),
                     "essais": essai + 1, "erreur": None}
        except Exception as e:
            msg = str(e)
            nature = classifier_erreur(msg)
            if nature == "fatale":
                log.error(f"[{modele}] erreur FATALE (credentials/quota) -> arrêt immédiat : {msg}")
                raise ErreurFataleFournisseur(msg)
            if nature == "recuperable" and essai < max_essais - 1:
                attente = min(2 ** (essai + 1) + random.uniform(0, 1), 60)
                log.warning(f"[{modele}] retard/erreur -> attente {attente:.1f}s (essai {essai+1}/{max_essais})")
                time.sleep(attente)
                continue
            return {"brut": None, "latence_ms": None, "essais": essai + 1, "erreur": msg}


def parser(brut):
    if brut is None or brut.strip() == "":
        return None, None, "reponse_vide"
    t = brut.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        d = json.loads(t[t.index("{"):t.rindex("}") + 1])
    except Exception:
        return None, None, "parsing_echoue"
    cat = str(d.get("categorie", "")).strip().lower()
    if cat not in VALID:
        return None, d.get("confiance"), "label_invalide"
    return cat, d.get("confiance"), None


def run(fournisseur, modele, chemin_textes, passe=1):
    cfg = PROVIDERS[fournisseur]
    client = OpenAI(base_url=cfg["base_url"], api_key=cfg["key"], timeout=TIMEOUT_REQUETE)
    textes = [json.loads(l) for l in open(chemin_textes, encoding="utf-8")]

    nom_fichier = modele.replace('/', '_').replace(':', '_').replace('@', '')
    sortie = pathlib.Path(f"raw_outputs/{nom_fichier}_p{passe}.jsonl")
    sortie.parent.mkdir(parents=True, exist_ok=True)

    faits = set()
    if sortie.exists():
        with sortie.open(encoding="utf-8") as f:
            faits = {json.loads(l)["id"] for l in f if l.strip()}
        log.info(f"[{modele}] {len(faits)} textes déjà traités, reprise.")

    total = len(textes)
    maj_etat(modele, fournisseur=fournisseur, total=total, traites=len(faits),
              erreurs=0, statut="en_cours", debut=time.strftime("%Y-%m-%dT%H:%M:%S"))

    pause = 60 / cfg["rpm"] * 1.1
    traites = 0
    erreurs = 0

    try:
        with sortie.open("a", encoding="utf-8") as f:
            for item in textes:
                if item["id"] in faits:
                    continue
                r = classer(client, modele, item["text"], cfg["max_tokens"], cfg.get("extra", {}), cfg["max_essais"])
                label, conf, pb = parser(r["brut"])
                if pb:
                    erreurs += 1
                f.write(json.dumps({
                    "id": item["id"], "passe": passe,
                    "horodatage": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "fournisseur": fournisseur, "modele": modele,
                    "params": {"temperature": 0, "top_p": 1, "max_tokens": cfg["max_tokens"], **cfg.get("extra", {})},
                    "verite": item["type_haine_final"],
                    "sous_type": item.get("sous_type"),
                    "source_generation": item.get("source_generation"),
                    "reponse_brute": r["brut"], "label": label,
                    "confiance": conf, "probleme": pb,
                    "latence_ms": r["latence_ms"], "essais": r["essais"],
                    "erreur": r["erreur"],
                }, ensure_ascii=False) + "\n")
                f.flush()
                traites += 1
                maj_etat(modele, traites=traites + len(faits), erreurs=erreurs, statut="en_cours")
                if traites % 20 == 0:
                    log.info(f"[{modele}] {traites + len(faits)}/{total} textes traités "
                              f"({erreurs} erreurs de parsing/réponse)")
                time.sleep(pause)
    except ErreurFataleFournisseur as e:
        maj_etat(modele, statut="arrete_credentials", cause=str(e))
        log.error(f"[{modele}] run interrompu, clé/quota probablement invalide. Voir etat_run.json.")
        return
    except Exception as e:
        maj_etat(modele, statut="arrete_erreur", cause=str(e))
        log.error(f"[{modele}] run interrompu par une exception inattendue : {e}")
        raise

    maj_etat(modele, statut="termine", fin=time.strftime("%Y-%m-%dT%H:%M:%S"))
    log.info(f"[{modele}] Terminé : {sortie}")


if __name__ == "__main__":
    parser_args = argparse.ArgumentParser()
    parser_args.add_argument("--pilote", action="store_true")
    parser_args.add_argument("--complet", action="store_true")
    args = parser_args.parse_args()

    fichier = "data/pilote_100.jsonl" if args.pilote else "data/dataset_eval.jsonl"

    if not (args.pilote or args.complet):
        print("Utiliser --pilote ou --complet")
        raise SystemExit(0)

    taches = []
    for nom, cfg in PROVIDERS.items():
        if not cfg["key"]:
            continue
        for modele in cfg["modeles"]:
            taches.append((nom, modele))

    log.info(f"Lancement en parallèle de {len(taches)} modèles... (log : {LOG_PATH})")
    with ThreadPoolExecutor(max_workers=len(taches)) as executor:
        futures = {
            executor.submit(run, nom, modele, fichier, 1): (nom, modele)
            for nom, modele in taches
        }
        for future in as_completed(futures):
            nom, modele = futures[future]
            try:
                future.result()
            except Exception as e:
                log.error(f"[{modele}] ECHEC INATTENDU -> {e}")

    log.info("Tous les modèles ont terminé ou se sont arrêtés.")
