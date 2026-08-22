# Fiche protocole — Pré-enregistrement léger (v2)

**Mémoire M2 MIAGE — Benchmark de LLM génériques pour la détection de racisme, xénophobie et antisémitisme (dataset RXA)**

Document figé avant le lancement de l'exécution complète (phase P5), conformément à la section 6.1 du protocole d'expérimentation contrôlée.

*Mise à jour du 22/08/2026 : ajout d'une section infrastructure/suivi (§6bis), journal des incidents opérationnels (§6ter), et documentation de l'exploration infructueuse d'un 5e modèle (§3). Le panel et le prompt restent inchangés — aucune de ces modifications ne touche aux garanties méthodologiques figées le 20/08/2026.*

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

**Le panel reste fixé à 4 modèles.** Une exploration d'un éventuel 5e fournisseur a été menée le 22/08/2026 (cf. tableau ci-dessous) mais n'a pas abouti à un ajout — décision documentée pour la transparence du processus, sans impact sur le run déjà en cours sur les 4 modèles gelés.

### Fournisseurs/modèles testés et écartés (à documenter dans la discussion du mémoire)

| Fournisseur/modèle | Date | Raison de l'abandon |
|---|---|---|
| GitHub Models | — | Accès jamais obtenu malgré tentatives |
| OpenRouter (nemotron-3-nano-omni-reasoning, nemotron-3-super-120b, poolside/laguna-s-2.1, liquid/lfm-2.5-2.6b) | — | Pool gratuit partagé congestionné, 429 en cascade, refus/réponses vides sur contenu antisémite pour certains modèles Nvidia |
| Cerebras (llama-3.3-70b puis gemma-4-31b) | — | Palier gratuit permanent supprimé ; carte bancaire vérifiée requise (erreur 402 Payment Required), incompatible avec le critère de gratuité stricte |
| NVIDIA NIM (build.nvidia.com) | 20/08/2026 | Site d'inscription indisponible au moment du test initial |
| Cohere (Trial API key) | — | Quota de 1 000 appels/mois insuffisant pour couvrir 1 500 textes en une passe |
| `qwen/qwen3.6-27b` (Groq) | — | Modèle à raisonnement interne : consomme tout son budget de tokens en réflexion cachée, réponses vides même à 1200 tokens et en mode `reasoning_format="hidden"` |
| `deepseek-ai/deepseek-v4-flash-0731` (NVIDIA Build) | 22/08/2026 | Accès obtenu (free tier sans carte bancaire, 1 000 crédits, ~40 rpm), mais latence de réponse jugée incompatible avec un traitement de 1 500 textes dans un délai raisonnable. Free tier basé sur des crédits (pas seulement un débit), risque supplémentaire d'épuisement en cours de run non quantifiable à l'avance. |
| `allam-2-7b` (Groq) | 22/08/2026 | Accès obtenu, robuste techniquement (aucune réponse vide/JSON malformé sur le pilote à 100 textes). Écarté pour raison de qualité de classification : exactitude ≈ 61 % sur le pilote (bien inférieure aux 4 modèles retenus), biais massif vers la catégorie "xénophobie" (72 % des cas de racisme mal classés, 42 % des cas d'antisémitisme mal classés — alors que l'antisémitisme est détecté de façon fiable par les 4 modèles du panel). Modèle 7B, probablement sous-dimensionné et à dominante d'entraînement arabe/anglais pour une tâche fine en français. |

## 4. Versions et dates d'accès

| Modèle | Date/heure du premier test réussi | Date/heure de fin du run complet |
|---|---|---|
| openai/gpt-oss-120b (Groq) | 19/08/2026 | *[à compléter — run multi-jours, cf. §6bis]* |
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

| Fournisseur | rpm | max_essais | Backoff | Limite journalière connue |
|---|---|---|---|---|
| Groq (gpt-oss-120b) | 30 | 5 | Exponentiel, plafonné à 60s | **1 000 requêtes/jour (RPD)** — découvert en cours de run complet le 22/08/2026 ; nécessite une exécution répartie sur plusieurs jours pour ce modèle uniquement (cf. §6ter) |
| Gemini | **15** *(corrigé, initialement configuré à 30 par erreur — quota réel free tier confirmé par 429 le 22/08/2026)* | 5 | Exponentiel, plafonné à 60s | Non identifiée |
| Mistral | 15 | 8 | Exponentiel, plafonné à 60s (ajusté après le pilote suite à des 429 fréquents) | Non identifiée |
| Cloudflare | 20 | 5 | Exponentiel, plafonné à 60s | Non identifiée |

## 6bis. Infrastructure d'exécution et suivi (ajout du 22/08/2026)

Pour sécuriser le run complet (1 500 textes × 4 modèles, plusieurs heures d'exécution ininterrompue), l'infrastructure d'exécution a été renforcée sans modifier la logique de classification ni le prompt :

| Composant | Rôle |
|---|---|
| `etat_run.json` | État global, mis à jour à chaque texte traité (thread-safe, écriture atomique via fichier temporaire + `os.replace`). Contient pour chaque modèle : nombre traité/total, statut (`en_cours`/`termine`/`arrete_credentials`/`arrete_erreur`), nombre d'erreurs, horodatage de dernière mise à jour. |
| `logs/run_*.log` | Journalisation fichier (module `logging`, en plus de la console) de tous les événements (retries, arrêts, erreurs), pour conserver la trace même en cas de fermeture du terminal. |
| `scripts/02_suivi_run.py` | Visualiseur de progression en temps réel (lecture de `etat_run.json` toutes les 5s), lancé dans un terminal séparé pendant le run, sans interférer avec l'écriture des résultats. |
| Distinction erreur fatale / récupérable | Les erreurs de type 401/403/quota (credentials invalides) interrompent immédiatement le fournisseur concerné plutôt que d'épuiser les `max_essais` sur chaque texte restant, limitant la perte de temps en cas d'expiration de clé en cours de run. |

Ces ajouts sont purement opérationnels (traçabilité et robustesse de l'exécution) et n'affectent ni le prompt, ni les paramètres d'appel, ni la logique de classification déjà gelés depuis le 20/08/2026.

## 6ter. Journal des incidents opérationnels (22/08/2026)

Documenté pour la transparence et la reproductibilité, conformément à l'esprit du pré-enregistrement. Aucun de ces incidents n'a nécessité de modification du prompt ou du panel de modèles.

| Incident | Cause | Résolution | Impact sur les données |
|---|---|---|---|
| Gemini : 429 en cascade | rpm configuré à 30, quota réel free tier = 15 rpm (`generate_content_free_tier_requests`) | rpm corrigé à 15 dans la config (§6) | Aucun texte perdu, textes en erreur relancés via le mécanisme de reprise |
| Groq gpt-oss-120b : 429 persistant même après ajustement rpm | Plafond journalier (RPD) de 1 000 requêtes/jour découvert en cours de run, non documenté à l'avance | Run réparti sur plusieurs jours calendaires pour ce modèle uniquement, via le mécanisme de reprise natif du script | Aucun texte perdu, allongement du délai de complétion pour ce modèle |
| Cloudflare : 404 en boucle | Bug de code — variable `CLOUDFLARE_ACCOUNT_ID` non interpolée dans l'URL de base (f-string manquant) suite à une modification du script | Correction du code, ligne `base_url` vérifiée | Lignes d'erreur générées pendant l'incident retirées manuellement du fichier `raw_outputs` correspondant avant reprise, pour permettre leur retraitement |
| `etat_run.json` : accès refusé (WinError 5) | Probable process Python résiduel non arrêté après une tentative d'interruption (Ctrl+C insuffisant face à `ThreadPoolExecutor.shutdown(wait=True)`) | Arrêt forcé de tous les process Python résiduels avant relance ; ajout d'une logique de nouvelle tentative sur l'écriture atomique de l'état | Aucun impact sur `raw_outputs` (écriture flush ligne par ligne, indépendante de `etat_run.json`) |

## 7. Run pilote (phase P4) — résultats et validation

| Modèle | Nombre de `probleme` sur 100 textes | Décision |
|---|---|---|
| openai/gpt-oss-120b (Groq) | 1 (`reponse_vide`) | Sous le seuil de 2 % — validé |
| gemini-3.5-flash-lite | 0 | Validé |
| mistral-large-latest | 0 (après ajustement rpm 30→15 et max_essais 5→8) | Validé |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | 0 | Validé |

**Critère de passage retenu** : taux d'erreur de parsing/refus < 2 % par modèle — atteint pour les 4 modèles. Le panel et le prompt sont gelés à partir du 20/08/2026.

**Observation qualitative du pilote (à documenter, non corrective sur le prompt)** : confusion racisme↔xénophobie observée de façon convergente chez les 4 modèles sur les mêmes textes ambigus (ex. stéréotypes essentialisants sur l'origine). L'antisémitisme est détecté de façon fiable par tous les modèles. `openai/gpt-oss-120b` présente une bonne calibration : ses erreurs s'accompagnent de scores de confiance nettement plus bas que ses réponses correctes.

**Pour mémoire (candidat hors panel testé le 22/08/2026)** : `allam-2-7b` (Groq) a été testé sur le même sous-échantillon pilote à titre exploratoire. Résultat : exactitude ≈ 61 %, biais marqué vers "xénophobie" y compris sur des textes antisémites (42 % mal classés). Ce résultat n'entre pas dans le comparatif retenu (modèle non intégré au panel, cf. §3) mais pourra être mentionné en discussion comme point de comparaison sur l'effet de la taille du modèle.

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
- [ ] Dates et heures exactes de fin de run par modèle (Groq gpt-oss-120b : run multi-jours du fait du plafond RPD, cf. §6/§6ter)
- [ ] Identifiants de version renvoyés par chaque fournisseur si disponibles
- [ ] Vérification finale du taux de `probleme` sur les 1 500 textes (pas seulement le pilote)
- [ ] Nettoyage confirmé des lignes d'erreur liées aux incidents opérationnels du 22/08/2026 (Cloudflare 404, éventuels doublons d'`id` dans `raw_outputs`)
