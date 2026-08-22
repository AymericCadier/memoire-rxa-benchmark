"""
Test de classification reelle (vrai prompt) sur le panel a 5 fournisseurs :
groq_gptoss, gemini, mistral, cloudflare, nvidia_deepseek.
Envoie 3 textes d'exemple (HORS dataset RXA, ecrits a la main) et verifie
que chaque fournisseur renvoie un JSON valide et parsable.

Modeles a raisonnement (gpt-oss-120b) : parametres specifiques transmis
via extra_body pour masquer/reduire le raisonnement interne dans la
reponse finale.

nvidia_deepseek : ajout exploratoire (22/08/2026), free tier NVIDIA Build
base sur des credits (pas seulement un RPM) -> ce test isole permet de
verifier avant d'integrer ce fournisseur au run parallele complet.

Prérequis .env :
GROQ_API_KEY, GEMINI_API_KEY, MISTRAL_API_KEY, CLOUDFLARE_API_KEY,
NVIDIA_API_KEY

Usage :
python scripts/00b_test_classification_avec_nvidia.py
"""

import json, os, pathlib
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

CLOUDFLARE_ACCOUNT_ID = "13c530a2588696e224178f7d60634329"

PROVIDERS = {
    # "groq_gptoss": {
    #     "base_url": "https://api.groq.com/openai/v1",
    #     "key": os.environ.get("GROQ_API_KEY"),
    #     "modele": "openai/gpt-oss-120b",
    #     "max_tokens": 600,
    #     "extra": {"reasoning_effort": "low"},
    # },
    # "gemini": {
    #     "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    #     "key": os.environ.get("GEMINI_API_KEY"),
    #     "modele": "gemini-3.5-flash-lite",
    #     "max_tokens": 200,
    #     "extra": {},
    # },
    # "mistral": {
    #     "base_url": "https://api.mistral.ai/v1",
    #     "key": os.environ.get("MISTRAL_API_KEY"),
    #     "modele": "mistral-large-latest",
    #     "max_tokens": 200,
    #     "extra": {},
    # },
    # "cloudflare": {
    #     "base_url": f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/v1",
    #     "key": os.environ.get("CLOUDFLARE_API_KEY"),
    #     "modele": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    #     "max_tokens": 300,
    #     "extra": {},
    # },
    "groq_allam": {
            "base_url": "https://api.groq.com/openai/v1",
            "key": os.environ.get("GROQ_API_KEY"),
            "modele": "allam-2-7b",
            "max_tokens": 300,
            "extra": {},
        },
}

SYSTEM_PROMPT = pathlib.Path("prompts/prompt_v1.txt").read_text(encoding="utf-8")
USER_TPL = 'Texte a classer :\n"""\n{texte}\n"""\n\nReponds uniquement par le JSON demande.'
VALID = {"racisme", "xenophobie", "antisemitisme"}

# Textes d'exemple ECRITS A LA MAIN, absents du dataset RXA
TEXTES_TEST = [
    ("Ces gens la ont toujours eu la delinquance dans le sang.", "racisme"),
    ("Qu'ils rentrent chez eux, la France n'est pas un hotel.", "xenophobie"),
    ("Cherchez a qui appartiennent les banques et les medias, vous comprendrez qui dirige vraiment.", "antisemitisme"),
]


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


def tester_fournisseur(nom, cfg):
    if not cfg["key"]:
        print(f"\n=== {nom} === clé manquante dans .env -> ignoré")
        return
    client = OpenAI(base_url=cfg["base_url"], api_key=cfg["key"])
    print(f"\n=== {nom} / {cfg['modele']} ===")
    for texte, attendu in TEXTES_TEST:
        try:
            rep = client.chat.completions.create(
                model=cfg["modele"],
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_TPL.format(texte=texte)},
                ],
                temperature=0, top_p=1, max_tokens=cfg["max_tokens"],
                extra_body=cfg["extra"] if cfg["extra"] else None,
            )
            brut = rep.choices[0].message.content
            label, conf, pb = parser(brut)
            statut = "OK" if pb is None and label == attendu else (
                "LABEL_INATTENDU" if pb is None else f"PROBLEME({pb})"
            )
            print(f"  [{statut}] attendu={attendu} obtenu={label} confiance={conf} brut={brut!r}")
        except Exception as e:
            print(f"  [ERREUR_API] {e}")


if __name__ == "__main__":
    for nom, cfg in PROVIDERS.items():
        tester_fournisseur(nom, cfg)
