"""
Phase P4/P5 du protocole RXA — Run pilote et exécution complète.

Panel final (20/08/2026) :
- groq_gptoss : openai/gpt-oss-120b        (OpenAI, ouvert, grand)
- groq_qwen   : abandonné (raisonnement Qwen ingérable en tokens)
- gemini      : gemini-3.5-flash-lite       (Google, propriétaire, léger)
- mistral     : mistral-large-latest        (Mistral AI, ouvert, européen)
- cloudflare  : llama-3.3-70b-instruct-fp8-fast (Meta, ouvert, grand)

Panel final retenu a 4 modeles (5e modele abandonne apres exploration
infructueuse d'OpenRouter, Cerebras, NVIDIA NIM, Cohere, Qwen/Groq).

Mistral (20/08/2026) : 429 frequents constates au pilote meme a rpm=30.
Ajustement de prudence : rpm abaisse a 15, max_essais porte a 8, backoff
plafonne a 60s par tentative, pour minimiser le risque de reponse_vide
sur le run complet (1500 textes) plutot que d'avoir a repasser un
complement apres coup.

Prérequis : variables d'environnement dans .env
    GROQ_API_KEY, GEMINI_API_KEY, MISTRAL_API_KEY, CLOUDLFARE_API_KEY

Usage :
    python scripts/01_run_modele.py --pilote
    python scripts/01_run_modele.py --complet
"""

import json, os, time, random, pathlib, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

TIMEOUT_REQUETE = 45
CLOUDFLARE_ACCOUNT_ID = "13c530a2588696e224178f7d60634329"

PROVIDERS = {
    "groq_gptoss": {
        "base_url": "https://api.groq.com/openai/v1",
        "key": os.environ.get("GROQ_API_KEY"),
        "rpm": 30,
        "max_tokens": 400,
        "max_essais": 5,
        "extra": {},
        "modeles": ["openai/gpt-oss-120b"],
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key": os.environ.get("GEMINI_API_KEY"),
        "rpm": 30,
        "max_tokens": 200,
        "max_essais": 5,
        "extra": {},
        "modeles": ["gemini-3.5-flash-lite"],
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "key": os.environ.get("MISTRAL_API_KEY"),
        "rpm": 15,
        "max_tokens": 200,
        "max_essais": 8,
        "extra": {},
        "modeles": ["mistral-large-latest"],
    },
    "cloudflare": {
        "base_url": f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/v1",
        "key": os.environ.get("CLOUDFLARE_API_KEY"),
        "rpm": 20,
        "max_tokens": 300,
        "max_essais": 5,
        "extra": {},
        "modeles": ["@cf/meta/llama-3.3-70b-instruct-fp8-fast"],
    },
}

SYSTEM_PROMPT = pathlib.Path("prompts/prompt_v1.txt").read_text(encoding="utf-8")
USER_TPL = 'Texte a classer :\n"""\n{texte}\n"""\n\nReponds uniquement par le JSON demande.'
VALID = {"racisme", "xenophobie", "antisemitisme"}


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
            recuperable = any(x in msg for x in ("429", "500", "502", "503", "timeout", "Timeout")) \
                or "rate limit" in msg.lower()
            if recuperable and essai < max_essais - 1:
                attente = min(2 ** (essai + 1) + random.uniform(0, 1), 60)
                print(f"[{modele}] retard/erreur -> attente {attente:.1f}s (essai {essai+1}/{max_essais})")
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
        print(f"[{modele}] {len(faits)} textes déjà traités, reprise.")

    pause = 60 / cfg["rpm"] * 1.1
    traites = 0

    with sortie.open("a", encoding="utf-8") as f:
        for item in textes:
            if item["id"] in faits:
                continue
            r = classer(client, modele, item["text"], cfg["max_tokens"], cfg.get("extra", {}), cfg["max_essais"])
            label, conf, pb = parser(r["brut"])
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
            if traites % 20 == 0:
                print(f"[{modele}] {traites + len(faits)}/{len(textes)} textes traités")
            time.sleep(pause)
    print(f"[{modele}] Terminé : {sortie}")


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

    print(f"Lancement en parallèle de {len(taches)} modèles...\n")
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
                print(f"[{modele}] ECHEC INATTENDU -> {e}")

    print("\nTous les modèles ont terminé ou se sont arrêtés.")
