# Fiche protocole — Pré-enregistrement léger

**Mémoire M2 MIAGE — Benchmark de LLM génériques pour la détection de racisme, xénophobie et antisémitisme (dataset RXA)**

Document figé avant le lancement de l'exécution complète (phase P5), conformément à la section 6.1 du protocole d'expérimentation contrôlée.

---

## 1. Corpus

| Élément | Valeur |
|---|---|
| Fichier source | `dataset_RXA_final.xlsx`, feuille `dataset_final` |
| Fichier figé | `data/dataset_eval.jsonl` |
| Nombre de textes | 1 500 (500 racisme / 500 xénophobie / 500 antisémitisme) |
| Seed de mélange | `42` (bibliothèque : `numpy.random.default_rng`) |
| Empreinte SHA-256 du corpus | *27A4E6231D7F31786F53D7DDB1DFE334D89A8591A4D604B5C54B5E8F121B8E5F* |
| Sous-échantillon pilote | `data/pilote_100.jsonl` (100 textes, tirage stratifié par `type_haine_final`) |
| Sous-échantillon de répétition | `data/repetition_300.jsonl` (300 textes, tirage stratifié) |

## 2. Prompt

| Élément | Valeur |
|---|---|
| Fichier | `prompts/prompt_v1.txt` |
| Stratégie | Zero-shot |
| Empreinte SHA-256 du prompt | *481E19D8097BF3FA3F7BE93AF3286DAD899A2F78D5314EB1939BFF7F6970BAE7* |
| Date de gel | 20/08/2026 |
| Format de sortie exigé | `{"categorie": "racisme"\|"xenophobie"\|"antisemitisme", "confiance": 0.0-1.0}` |
| Modification post-pilote | Aucune. La confusion racisme/xénophobie observée au pilote n'a pas donné lieu à un ajustement du prompt (décision méthodologique : éviter le surajustement de l'instrument sur les données d'évaluation). |

## 3. Panel de modèles retenu

| # | Fournisseur | Identifiant exact transmis à l'API | Éditeur | Rôle dans le comparatif |
|---|---|---|---|---|
| 1 | Groq | `openai/gpt-oss-120b` | OpenAI | Ouvert, grand, référence de raisonnement masqué |
| 2 | Google AI Studio | `gemini-3.5-flash-lite` | Google | Propriétaire, léger/rapide |
| 3 | Mistral La Plateforme (plan Experiment) | `mistral-large-latest` | Mistral AI | Ouvert, européen |
| 4 | Cloudflare Workers AI | `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | Meta | Ouvert, grand |

### Fournisseurs testés et écartés (à documenter dans la discussion du mémoire)

| Fournisseur/modèle | Raison de l'abandon |
|---|---|
| GitHub Models | Accès jamais obtenu malgré tentatives |
| OpenRouter (nemotron-3-nano-omni-reasoning, nemotron-3-super-120b, poolside/laguna-s-2.1, liquid/lfm-2.5-2.6b) | Pool gratuit partagé congestionné, 429 en cascade, refus/réponses vides sur contenu antisémite pour certains modèles Nvidia |
| Cerebras (llama-3.3-70b puis gemma-4-31b) | Palier gratuit permanent supprimé ; carte bancaire vérifiée requise (erreur 402 Payment Required), incompatible avec le critère de gratuité stricte |
| NVIDIA NIM (build.nvidia.com) | Site d'inscription indisponible au moment du test (20/08/2026) |
| Cohere (Trial API key) | Quota de 1 000 appels/mois insuffisant pour couvrir 1 500 textes en une passe |
| `qwen/qwen3.6-27b` (Groq) | Modèle à raisonnement interne : consomme tout son budget de tokens en réflexion cachée, réponses vides même à 1200 tokens et en mode `reasoning_format="hidden"` |

## 4. Versions et dates d'accès

| Modèle | Date/heure du premier test réussi | Date/heure de fin du run complet |
|---|---|---|
| openai/gpt-oss-120b (Groq) | 19/08/2026 | *[à compléter]* |
| gemini-3.5-flash-lite | 19/08/2026 | *[à compléter]* |
| mistral-large-latest | 19/08/2026 | *[à compléter]* |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | 20/08/2026 | *[à compléter]* |

*Note : les identifiants de version affichés par chaque fournisseur (le cas échéant) sont à consigner dans les journaux `logs/` au moment du run complet.*

## 5. Paramètres d'appel

| Paramètre | Valeur commune | Exceptions |
|---|---|---|
| `temperature` | 0 | — |
| `top_p` | 1 | — |
| `max_tokens` | 200 (Gemini, Mistral) | 400 (Groq gpt-oss-120b, raisonnement masqué), 300 (Cloudflare) |
| `reasoning_effort` | — | `"low"` pour openai/gpt-oss-120b uniquement |
| Pénalités (`presence_penalty`, `frequency_penalty`) | Absentes | — |

## 6. Gestion des limites de débit (par fournisseur)

| Fournisseur | rpm | max_essais | Backoff |
|---|---|---|---|
| Groq (gpt-oss-120b) | 30 | 5 | Exponentiel, plafonné à 60s |
| Gemini | 30 | 5 | Exponentiel, plafonné à 60s |
| Mistral | 15 | 8 | Exponentiel, plafonné à 60s (ajusté après le pilote suite à des 429 fréquents) |
| Cloudflare | 20 | 5 | Exponentiel, plafonné à 60s |

## 7. Run pilote (phase P4) — résultats et validation

| Modèle | Nombre de `probleme` sur 100 textes | Décision |
|---|---|---|
| openai/gpt-oss-120b (Groq) | 1 (`reponse_vide`) | Sous le seuil de 2 % — validé |
| gemini-3.5-flash-lite | 0 | Validé |
| mistral-large-latest | 0 (après ajustement rpm 30→15 et max_essais 5→8) | Validé |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | 0 | Validé |

**Critère de passage retenu** : taux d'erreur de parsing/refus < 2 % par modèle — atteint pour les 4 modèles. Le panel et le prompt sont gelés à partir du 20/08/2026.

**Observation qualitative du pilote (à documenter, non corrective sur le prompt)** : confusion racisme↔xénophobie observée de façon convergente chez les 4 modèles sur les mêmes textes ambigus (ex. stéréotypes essentialisants sur l'origine). L'antisémitisme est détecté de façon fiable par tous les modèles. `openai/gpt-oss-120b` présente une bonne calibration : ses erreurs s'accompagnent de scores de confiance nettement plus bas que ses réponses correctes.

## 8. Métriques et tests statistiques prévus

| Élément | Choix |
|---|---|
| Métrique principale | macro-F1 |
| Métriques secondaires | Accuracy, précision/rappel par classe, kappa de Cohen, taux de refus (stricte et conditionnelle), taux d'erreur de parsing, latence médiane |
| Politique de traitement des refus | Un refus/`reponse_vide` compte comme une prédiction incorrecte en mesure stricte ; métriques recalculées en mesure conditionnelle sur les seules réponses exploitables |
| Analyses stratifiées | Par `sous_type` (9 catégories) et par `source_generation` (6 catégories) |
| Test de comparaison par paires | McNemar (version binomiale exacte si b+c < 25) |
| Correction multi-tests | Bonferroni, α ajusté = 0,05 / 6 (6 paires pour 4 modèles) |
| Test global | Q de Cochran |
| Intervalles de confiance | Bootstrap non paramétrique, 1 000 ré-échantillonnages, seed = 42 |

## 9. Éléments restant à compléter après le run complet

- [ ] Empreinte SHA-256 du corpus et du prompt (à insérer ci-dessus)
- [ ] Dates et heures exactes de fin de run par modèle
- [ ] Identifiants de version renvoyés par chaque fournisseur si disponibles
- [ ] Vérification finale du taux de `probleme` sur les 1 500 textes (pas seulement le pilote)
