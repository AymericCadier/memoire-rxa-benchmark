# Fiche protocole — Pré-enregistrement léger (version finale, post-run, post-P7/P8)

**Mémoire M2 MIAGE — Benchmark de LLM génériques pour la détection de racisme, xénophobie et antisémitisme (dataset RXA)**

Document figé avant le lancement de l'exécution complète (phase P5), conformément à la section 6.1 du protocole d'expérimentation contrôlée.

*Mise à jour du 25/08/2026 : phases P7 (calcul des métriques) et P8 (tests statistiques) terminées et validées. Scripts `scripts/03_calculer_metriques.py` et `scripts/04_tests_statistiques.py` exécutés de bout en bout, sorties vérifiées ligne à ligne (cohérence des effectifs, convergence croisée McNemar/bootstrap). Le protocole passe en phase P9 (rédaction et discussion des résultats).*

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
| Format de sortie exigé | `{"categorie": "racisme"|"xenophobie"|"antisemitisme", "confiance": 0.0-1.0}` |
| Modification post-pilote | Aucune. |

## 3. Panel de modèles retenu (final)

| # | Fournisseur | Identifiant exact transmis à l'API | Éditeur | Rôle dans le comparatif |
|---|---|---|---|---|
| 1 | Groq | `openai/gpt-oss-120b` | OpenAI | Ouvert, grand, référence de raisonnement masqué |
| 2 | Google AI Studio | `gemini-3.5-flash-lite` | Google | Propriétaire, léger/rapide |
| 3 | Mistral La Plateforme (plan Experiment) | `mistral-large-latest` | Mistral AI | Ouvert, européen |
| 4 | Cloudflare Workers AI | `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | Meta | Ouvert, grand |

Le panel est resté fixé à ces 4 modèles jusqu'à la fin du run.

### Fournisseurs/modèles testés et écartés

| Fournisseur/modèle | Date | Raison de l'abandon |
|---|---|---|
| GitHub Models | — | Accès jamais obtenu malgré tentatives |
| OpenRouter (nemotron-3-nano-omni-reasoning, nemotron-3-super-120b, poolside/laguna-s-2.1, liquid/lfm-2.5-2.6b) | — | Pool gratuit partagé congestionné, 429 en cascade, refus/réponses vides sur contenu antisémite |
| Cerebras (llama-3.3-70b puis gemma-4-31b) | — | Carte bancaire vérifiée requise (402), incompatible avec la gratuité stricte |
| NVIDIA NIM (build.nvidia.com), 1re tentative | 20/08/2026 | Site d'inscription indisponible |
| Cohere (Trial API key) | — | Quota mensuel de 1 000 appels insuffisant |
| `qwen/qwen3.6-27b` (Groq) | — | Raisonnement interne consommant tout le budget de tokens |
| `deepseek-ai/deepseek-v4-flash-0731` (NVIDIA Build), 2e tentative | 22/08/2026 | Accès obtenu, mais latence trop élevée pour 1 500 textes |
| `allam-2-7b` (Groq) | 22/08/2026 | Exactitude ≈ 61 % sur pilote, biais massif vers "xénophobie" (42 % d'antisémitisme mal classé) |

## 4. Versions et dates d'accès (définitif)

| Modèle | Premier test réussi | Fin du run complet |
|---|---|---|
| openai/gpt-oss-120b (Groq) | 19/08/2026 | 24/08/2026 18:04 *(run multi-jours, plafonds RPD et TPD rencontrés)* |
| gemini-3.5-flash-lite | 19/08/2026 | 24/08/2026 13:06 |
| mistral-large-latest | 19/08/2026 | 24/08/2026 14:01 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | 20/08/2026 | 24/08/2026 17:56 *(repasse après incident "neurons" journaliers)* |

## 5. Paramètres d'appel

| Paramètre | Valeur commune | Exceptions |
|---|---|---|
| `temperature` | 0 | — |
| `top_p` | 1 | — |
| `max_tokens` | 200 (Gemini, Mistral) | 400 (Groq gpt-oss-120b), 300 (Cloudflare) |
| `reasoning_effort` | — | `"low"` pour openai/gpt-oss-120b uniquement |
| Pénalités | Absentes | — |

## 6. Gestion des limites de débit (par fournisseur, valeurs finales)

| Fournisseur | rpm | max_essais | Backoff | Limites journalières identifiées |
|---|---|---|---|---|
| Groq (gpt-oss-120b) | 30 | 5 | Exponentiel, plafonné à 60s | 1 000 requêtes/jour (RPD) **et** 200 000 tokens/jour (TPD) — run réparti sur plusieurs jours |
| Gemini | 15 (corrigé) | 5 | Exponentiel, plafonné à 60s | Aucune rencontrée |
| Mistral | 15 | 8 | Exponentiel, plafonné à 60s | Aucune rencontrée |
| Cloudflare | 20 | 5 | Exponentiel, plafonné à 60s | 10 000 "neurons"/jour |

## 6bis. Infrastructure d'exécution et suivi

| Composant | Rôle |
|---|---|
| `etat_run.json` | État global par modèle (statut, progression, erreurs), lu par le visualiseur. Limite connue : ne cumule pas les erreurs entre sessions de reprise (le comptage fiable est celui fait après coup sur `raw_outputs`). |
| `logs/run_*.log` | Journalisation fichier complète. |
| `scripts/02_suivi_run.py` | Visualiseur de progression en temps réel. |
| `scripts/02_consolider_resultats.py` | Fusionne les 4 `raw_outputs/*.jsonl` en `predictions.csv`, avec vérification de doublons/manquants. |
| `scripts/03_diagnostiquer_problemes.py` | Répartition des `probleme` par modèle, `sous_type`, `source_generation`. |
| `scripts/04_compter_erreurs_quota.py` / `05_nettoyer_pour_repasse.py` | Détection et retrait ciblé des échecs liés à un quota journalier, pour repasse ultérieure. |
| `scripts/04_normaliser_predictions.py` | Normalise les accents de `verite` pour la rendre comparable à `label`, produit `predictions_normalise.csv` avec une colonne `correct`. |
| `scripts/03_calculer_metriques.py` | **[Nouveau]** Phase P7 : matrices de confusion, accuracy, macro-F1, kappa (stricte/conditionnelle), précision/rappel/F1 par classe, taux de refus, stratifications par `sous_type` et `source_generation`, latence médiane, analyses de confiance (calibration, risque-couverture, confiance par sous-type). Sorties dans `outputs_P7/`. |
| `scripts/04_tests_statistiques.py` | **[Nouveau]** Phase P8 : McNemar par paires (exact/khi2 selon b+c), correction de Bonferroni, test Q de Cochran, IC bootstrap non paramétrique (1000 tirages, seed=42) sur macro-F1/accuracy par modèle et sur les écarts par paire. Sorties dans `outputs_P8/`. |

## 6ter. Journal des incidents opérationnels (clos)

| Date | Incident | Cause | Résolution | Impact final sur les données |
|---|---|---|---|---|
| 22/08 | Gemini : 429 en cascade | rpm mal configuré (30 au lieu de 15) | rpm corrigé à 15 | Aucun |
| 22/08 | Groq gpt-oss-120b : 429 persistant | Plafond RPD (1 000/jour) | Run réparti sur plusieurs jours | Aucun |
| 22/08 | Cloudflare : 404 en boucle | Bug de code (f-string manquant) | Code corrigé | Lignes retirées et retraitées |
| 22/08 | `etat_run.json` : accès refusé | Process Python résiduel | Process tués, retry ajouté | Aucun |
| 24/08 | Groq gpt-oss-120b : 129 textes en échec (TPD, 200 000 tokens/jour) | Plafond journalier distinct du RPD | Nettoyage + repasse après reset | **Résolu, 0 échec technique résiduel** |
| 24/08 | Cloudflare : 61 textes en échec ("neurons"/jour) | Budget journalier free tier épuisé | Nettoyage + repasse | **Résolu, 0 échec technique résiduel** |

## 7. Résultats finaux du run complet (1 500 textes × 4 modèles)

| Modèle | `probleme` sur 1 500 | Taux | Nature |
|---|---|---|---|
| openai/gpt-oss-120b (Groq) | 13 | 0,87 % | 10 `reponse_vide` + 3 `parsing_echoue`, résiduel légitime (raisonnement masqué), sous le seuil de 2 % du pilote |
| gemini-3.5-flash-lite | 0 | 0 % | — |
| mistral-large-latest | 0 | 0 % | — |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | 0 | 0 % | Après repasse post-incident "neurons" |

**Décision retenue conformément au protocole** : les 13 cas résiduels sur gpt-oss-120b ne sont pas retraités (règle anti-ajustement post-hoc) et comptent comme prédiction incorrecte en mesure stricte, avec recalcul en mesure conditionnelle (appliqué en phase P7, cf. §8bis).

**Pour mémoire (hors panel)** : `allam-2-7b` testé le 22/08/2026, exactitude ≈ 61 % sur pilote, non intégré (cf. §3).

## 8. Métriques et tests statistiques prévus (phase P7/P8 — **réalisé**, cf. §8bis)

| Élément | Choix |
|---|---|
| Métrique principale | macro-F1 |
| Métriques secondaires | Accuracy, précision/rappel par classe, kappa de Cohen, taux de refus (stricte et conditionnelle), taux d'erreur de parsing, latence médiane |
| Politique de traitement des refus | Refus/`reponse_vide` = prédiction incorrecte en mesure stricte ; recalcul en mesure conditionnelle sur les réponses exploitables |
| Analyses stratifiées | Par `sous_type` (9 catégories) et `source_generation` (6 catégories) |
| Comparaison par paires | McNemar (binomiale exacte si b+c < 25) |
| Correction multi-tests | Bonferroni, α ajusté = 0,05 / 6 |
| Test global | Q de Cochran |
| Intervalles de confiance | Bootstrap non paramétrique, 1 000 ré-échantillonnages, seed = 42 |
| **Prérequis technique** | Normaliser les accents de `verite` avant tout calcul (`verite_norm` vs `label`) — géré par `04_normaliser_predictions.py` |

## 8bis. Résultats obtenus (phases P7 et P8, clos le 25/08/2026)

### Tableau 10 — Résultats principaux (modèles × métriques), mesure stricte

| Modèle | Accuracy | Macro-F1 | Kappa | Taux de refus |
|---|---|---|---|---|
| gemini-3.5-flash-lite | 0,836 | 0,8324 | 0,754 | 0 % |
| mistral-large-latest | 0,826 | 0,8221 | 0,739 | 0 % |
| openai/gpt-oss-120b | 0,736 | 0,7380 | 0,6057 | 0,87 % |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | 0,724 | 0,7207 | 0,586 | 0 % |

IC bootstrap à 95 % (macro-F1, 1000 tirages, seed=42) : Gemini [0,8151 ; 0,8504], Mistral [0,8039 ; 0,8409], gpt-oss-120b [0,7174 ; 0,7599], Llama [0,6985 ; 0,7421] — les deux groupes {Gemini, Mistral} et {gpt-oss-120b, Llama} ne se chevauchent pas.

### McNemar par paires (6 comparaisons, α ajusté Bonferroni = 0,008333)

| Paire | b+c | Méthode | p-value | Significatif (ajusté) |
|---|---|---|---|---|
| Llama vs Gemini | 220 | khi2_continuité | < 0,0001 | Oui |
| Llama vs Mistral | 219 | khi2_continuité | < 0,0001 | Oui |
| Mistral vs gpt-oss-120b | 221 | khi2_continuité | < 0,0001 | Oui |
| Gemini vs gpt-oss-120b | 230 | khi2_continuité | < 0,0001 | Oui |
| Gemini vs Mistral | 109 | khi2_continuité | 0,180 | **Non** |
| Llama vs gpt-oss-120b | 176 | khi2_continuité | 0,200 | **Non** |

Convergence confirmée avec les IC bootstrap sur l'écart de macro-F1 par paire : les deux mêmes paires (Gemini-Mistral et Llama-gptoss) sont les seules dont l'IC à 95 % inclut 0.

**Interprétation retenue** : le panel se structure statistiquement en **deux groupes homogènes** plutôt qu'en un classement continu à 4 niveaux — {Gemini, Mistral} significativement supérieur à {gpt-oss-120b, Llama 3.3 70B}, sans différence significative intra-groupe.

### Test Q de Cochran (test global)

Q = 237,21, ddl = 3, p ≈ 3,82 × 10⁻⁵¹ (hautement significatif) → au moins un modèle diffère significativement des autres ; les comparaisons par paires (McNemar) sont statistiquement justifiées.

### Points d'analyse complémentaire réalisés en P7

- Confusion racisme→xénophobie confirmée sur gpt-oss-120b (42,4 % des textes racisme classés xénophobie), cohérente avec le biais déjà observé sur `allam-2-7b` au pilote (42 % d'antisémitisme mal classé) — signal d'un artefact structurel de la tâche plutôt que d'un défaut isolé à un modèle.
- Stratification par `sous_type` : chute de performance nette sur `ambigu`, `hostilite_religieuse`, `dog_whistle` et `sarcasme` pour les 4 modèles, conforme à l'hypothèse H3.
- Analyse risque-couverture : gpt-oss-120b montre le gain d'accuracy le plus fort entre seuil de confiance 0 et 0,9 (+21,9 points), suggérant une calibration de confiance relativement fiable malgré un macro-F1 global plus faible.
- Comparaison à `allam-2-7b` (hors panel, 7B) : écart de 11 points d'accuracy avec le modèle du panel le plus faible (Llama 70B, 72,4 %), suggérant un effet de taille plus marqué que prévu par H1 en dessous d'un certain seuil de paramètres.

## 9. Éléments restant à compléter

- [x] Run complet des 1 500 textes sur les 4 modèles (24/08/2026)
- [x] Consolidation en table unique (`predictions.csv`, 6 000 lignes, 0 doublon/manquant)
- [x] Nettoyage des résidus hors panel (`allam-2-7b`)
- [x] Normalisation des accents (`predictions_normalise.csv`)
- [x] Calcul des métriques P7 (matrices de confusion, macro-F1, kappa, analyses stratifiées, confiance) — `outputs_P7/`
- [x] Tests statistiques P8 (McNemar, Cochran, bootstrap) — `outputs_P8/`
- [ ] Identifiants de version exacts renvoyés par chaque fournisseur, si disponibles
- [ ] Interprétation qualitative approfondie des résultats P7/P8 (confusion racisme/xénophobie sur les 4 modèles, calibration complète — en cours)
- [ ] Rédaction du chapitre méthodologique intégrant le journal d'incidents comme illustration des limites de la "gratuité stricte"
- [ ] Rédaction de la discussion des résultats en lien avec l'état de l'art (mémoire de référence M1)
