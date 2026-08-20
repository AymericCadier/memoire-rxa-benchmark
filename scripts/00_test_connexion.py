"""
Phase P2 du protocole RXA — Test de connexion "hello world" uniquement.
Ne dépend pas du prompt.

Mise à jour du panel (19/08/2026) :
- Groq : llama-3.3-70b-versatile déprécié -> remplacé par openai/gpt-oss-120b
  (modèle ouvert de grande taille, rôle équivalent dans le tableau 7 du protocole)
- OpenRouter : deepseek/deepseek-r1:free retiré du gratuit -> la liste des
  modèles ":free" est interrogée en direct via l'API pour éviter de figer
  un identifiant qui pourrait disparaître à nouveau.

Prérequis : variables d'environnement dans .env
    GEMINI_API_KEY, GROQ_API_KEY, MISTRAL_API_KEY, OPENROUTER_API_KEY

Usage :
    python scripts/00_test_connexion.py
"""

import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key": os.environ.get("GROQ_API_KEY"),
        "modeles": ["openai/gpt-oss-120b"],
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key": os.environ.get("GEMINI_API_KEY"),
        "modeles": ["gemini-3.5-flash-lite"],
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "key": os.environ.get("MISTRAL_API_KEY"),
        "modeles": ["mistral-large-latest"],
    },
}


def lister_modeles_gratuits_openrouter(cle):
    """Interroge le catalogue OpenRouter et ne garde que les modeles gratuits
    (id se terminant par ':free' ET prix input/output a 0)."""
    if not cle:
        return []
    r = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {cle}"},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json().get("data", [])
    gratuits = []
    for m in data:
        pricing = m.get("pricing", {})
        prix_in = float(pricing.get("prompt", "1") or "1")
        prix_out = float(pricing.get("completion", "1") or "1")
        if prix_in == 0 and prix_out == 0:
            gratuits.append(m["id"])
    return gratuits


def hello_world():
    for nom, cfg in PROVIDERS.items():
        if not cfg["key"]:
            print(f"[{nom}] clé manquante dans .env -> ignoré")
            continue
        client = OpenAI(base_url=cfg["base_url"], api_key=cfg["key"])
        for modele in cfg["modeles"]:
            try:
                rep = client.chat.completions.create(
                    model=modele,
                    messages=[{"role": "user", "content": "Réponds juste: ok"}],
                    max_tokens=10,
                )
                print(f"[{nom}/{modele}] OK -> {rep.choices[0].message.content!r}")
            except Exception as e:
                print(f"[{nom}/{modele}] ECHEC -> {e}")

    cle_or = os.environ.get("OPENROUTER_API_KEY")
    if not cle_or:
        print("[openrouter] clé manquante dans .env -> ignoré")
        return
    try:
        gratuits = lister_modeles_gratuits_openrouter(cle_or)
        print(f"\n[openrouter] {len(gratuits)} modèles gratuits trouvés actuellement, ex: {gratuits[:10]}")
        if gratuits:
            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=cle_or)
            test_modele = gratuits[0]
            rep = client.chat.completions.create(
                model=test_modele,
                messages=[{"role": "user", "content": "Réponds juste: ok"}],
                max_tokens=10,
            )
            print(f"[openrouter/{test_modele}] OK -> {rep.choices[0].message.content!r}")
    except Exception as e:
        print(f"[openrouter] ECHEC -> {e}")


if __name__ == "__main__":
    hello_world()
