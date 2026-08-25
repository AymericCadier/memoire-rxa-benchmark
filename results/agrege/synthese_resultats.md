# Synthèse des résultats — Benchmark RXA (phases P7 et P8)

## Synthèse par modèle (P7)

| modele                                   |   n_total |   n_refus |   taux_refus_pct |   accuracy_stricte |   accuracy_conditionnelle |   macro_f1_stricte |   macro_f1_conditionnelle |   kappa_stricte |   kappa_conditionnelle |   n_reponse_vide |   n_parsing_echoue |   n_refus_total |   latence_mediane_ms |   latence_p25_ms |   latence_p75_ms |   latence_max_ms |   confiance_mediane_correct |   confiance_mediane_incorrect |   ecart_confiance_correct_vs_incorrect |   n_correct |   n_incorrect |
|:-----------------------------------------|----------:|----------:|-----------------:|-------------------:|--------------------------:|-------------------:|--------------------------:|----------------:|-----------------------:|-----------------:|-------------------:|----------------:|---------------------:|-----------------:|-----------------:|-----------------:|----------------------------:|------------------------------:|---------------------------------------:|------------:|--------------:|
| gemini-3.5-flash-lite                    |      1500 |         0 |             0    |              0.836 |                    0.836  |             0.8324 |                    0.8324 |          0.754  |                 0.754  |                0 |                  0 |               0 |                558   |              525 |            604   |            45998 |                        0.95 |                          0.85 |                                   0.1  |        1254 |           246 |
| mistral-large-latest                     |      1500 |         0 |             0    |              0.826 |                    0.826  |             0.8221 |                    0.8221 |          0.739  |                 0.739  |                0 |                  0 |               0 |                685   |              610 |            983.8 |            82828 |                        0.95 |                          0.85 |                                   0.1  |        1239 |           261 |
| openai/gpt-oss-120b                      |      1500 |        13 |             0.87 |              0.736 |                    0.7424 |             0.738  |                    0.7416 |          0.6057 |                 0.6134 |               10 |                  3 |              13 |                723   |              522 |           1049.2 |            98406 |                        0.96 |                          0.6  |                                   0.36 |        1104 |           383 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast |      1500 |         0 |             0    |              0.724 |                    0.724  |             0.7207 |                    0.7207 |          0.586  |                 0.586  |                0 |                  0 |               0 |                742.5 |              624 |            992.5 |            33708 |                        0.9  |                          0.8  |                                   0.1  |        1086 |           414 |


## Précision / rappel / F1 par classe (P7)

| modele                                   | classe        |   precision |   rappel |     f1 |   support |
|:-----------------------------------------|:--------------|------------:|---------:|-------:|----------:|
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | racisme       |      0.8679 |    0.46  | 0.6013 |       500 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | xenophobie    |      0.5643 |    0.974 | 0.7146 |       500 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | antisemitisme |      0.9919 |    0.738 | 0.8463 |       500 |
| gemini-3.5-flash-lite                    | racisme       |      0.9072 |    0.606 | 0.7266 |       500 |
| gemini-3.5-flash-lite                    | xenophobie    |      0.6972 |    0.944 | 0.802  |       500 |
| gemini-3.5-flash-lite                    | antisemitisme |      0.9796 |    0.958 | 0.9687 |       500 |
| mistral-large-latest                     | racisme       |      0.871  |    0.594 | 0.7063 |       500 |
| mistral-large-latest                     | xenophobie    |      0.692  |    0.93  | 0.7935 |       500 |
| mistral-large-latest                     | antisemitisme |      0.9795 |    0.954 | 0.9666 |       500 |
| openai/gpt-oss-120b                      | racisme       |      0.688  |    0.56  | 0.6174 |       500 |
| openai/gpt-oss-120b                      | xenophobie    |      0.648  |    0.928 | 0.7632 |       500 |
| openai/gpt-oss-120b                      | antisemitisme |      0.989  |    0.72  | 0.8333 |       500 |


## Analyses stratifiées : sous_type et source_generation (P7)

| modele                                   | dimension         | categorie                       |   n |   accuracy_stricte |   macro_f1_stricte |   taux_refus_pct |
|:-----------------------------------------|:------------------|:--------------------------------|----:|-------------------:|-------------------:|-----------------:|
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | sous_type         | ambigu                          |  93 |             0.5806 |             0.4488 |             0    |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | sous_type         | complotisme                     |  29 |             1      |             0.6667 |             0    |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | sous_type         | dog_whistle                     | 138 |             0.7101 |             0.4816 |             0    |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | sous_type         | exclusion                       | 107 |             0.8037 |             0.6419 |             0    |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | sous_type         | haine_explicite                 | 428 |             0.8668 |             0.8645 |             0    |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | sous_type         | haine_implicite                 | 298 |             0.6443 |             0.597  |             0    |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | sous_type         | hostilite_religieuse            |  46 |             0.6087 |             0.4    |             0    |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | sous_type         | sarcasme                        | 123 |             0.6423 |             0.5145 |             0    |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | sous_type         | stereotype                      | 238 |             0.6261 |             0.6034 |             0    |
| gemini-3.5-flash-lite                    | sous_type         | ambigu                          |  93 |             0.7419 |             0.6706 |             0    |
| gemini-3.5-flash-lite                    | sous_type         | complotisme                     |  29 |             1      |             0.6667 |             0    |
| gemini-3.5-flash-lite                    | sous_type         | dog_whistle                     | 138 |             0.7971 |             0.6424 |             0    |
| gemini-3.5-flash-lite                    | sous_type         | exclusion                       | 107 |             0.7944 |             0.6857 |             0    |
| gemini-3.5-flash-lite                    | sous_type         | haine_explicite                 | 428 |             0.9299 |             0.9243 |             0    |
| gemini-3.5-flash-lite                    | sous_type         | haine_implicite                 | 298 |             0.7987 |             0.7545 |             0    |
| gemini-3.5-flash-lite                    | sous_type         | hostilite_religieuse            |  46 |             0.6957 |             0.5139 |             0    |
| gemini-3.5-flash-lite                    | sous_type         | sarcasme                        | 123 |             0.8049 |             0.7452 |             0    |
| gemini-3.5-flash-lite                    | sous_type         | stereotype                      | 238 |             0.8151 |             0.7738 |             0    |
| mistral-large-latest                     | sous_type         | ambigu                          |  93 |             0.7634 |             0.6725 |             0    |
| mistral-large-latest                     | sous_type         | complotisme                     |  29 |             1      |             0.6667 |             0    |
| mistral-large-latest                     | sous_type         | dog_whistle                     | 138 |             0.7681 |             0.6005 |             0    |
| mistral-large-latest                     | sous_type         | exclusion                       | 107 |             0.785  |             0.6397 |             0    |
| mistral-large-latest                     | sous_type         | haine_explicite                 | 428 |             0.9042 |             0.899  |             0    |
| mistral-large-latest                     | sous_type         | haine_implicite                 | 298 |             0.802  |             0.763  |             0    |
| mistral-large-latest                     | sous_type         | hostilite_religieuse            |  46 |             0.6522 |             0.4613 |             0    |
| mistral-large-latest                     | sous_type         | sarcasme                        | 123 |             0.7561 |             0.7009 |             0    |
| mistral-large-latest                     | sous_type         | stereotype                      | 238 |             0.8403 |             0.7989 |             0    |
| openai/gpt-oss-120b                      | sous_type         | ambigu                          |  93 |             0.5591 |             0.4787 |             1.08 |
| openai/gpt-oss-120b                      | sous_type         | complotisme                     |  29 |             0.931  |             0.6533 |             3.45 |
| openai/gpt-oss-120b                      | sous_type         | dog_whistle                     | 138 |             0.6957 |             0.5362 |             1.45 |
| openai/gpt-oss-120b                      | sous_type         | exclusion                       | 107 |             0.7944 |             0.6663 |             0    |
| openai/gpt-oss-120b                      | sous_type         | haine_explicite                 | 428 |             0.9112 |             0.9054 |             0    |
| openai/gpt-oss-120b                      | sous_type         | haine_implicite                 | 298 |             0.6242 |             0.5746 |             1.34 |
| openai/gpt-oss-120b                      | sous_type         | hostilite_religieuse            |  46 |             0.6087 |             0.4018 |             2.17 |
| openai/gpt-oss-120b                      | sous_type         | sarcasme                        | 123 |             0.626  |             0.5407 |             2.44 |
| openai/gpt-oss-120b                      | sous_type         | stereotype                      | 238 |             0.6849 |             0.6621 |             0.42 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | source_generation | generation_complement           |  83 |             0.506  |             0.3356 |             0    |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | source_generation | generation_originale            | 420 |             0.6643 |             0.6244 |             0    |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | source_generation | hardcase                        | 254 |             0.6535 |             0.4264 |             0    |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | source_generation | transfert_racisme_antisemitisme | 194 |             0.9948 |             0.3325 |             0    |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | source_generation | transfert_racisme_xenophobie    | 137 |             0.9927 |             0.3321 |             0    |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | source_generation | tri_manuel                      | 412 |             0.6553 |             0.7031 |             0    |
| gemini-3.5-flash-lite                    | source_generation | generation_complement           |  83 |             0.6627 |             0.4293 |             0    |
| gemini-3.5-flash-lite                    | source_generation | generation_originale            | 420 |             0.8214 |             0.7946 |             0    |
| gemini-3.5-flash-lite                    | source_generation | hardcase                        | 254 |             0.8819 |             0.6073 |             0    |
| gemini-3.5-flash-lite                    | source_generation | transfert_racisme_antisemitisme | 194 |             1      |             0.3333 |             0    |
| gemini-3.5-flash-lite                    | source_generation | transfert_racisme_xenophobie    | 137 |             0.9489 |             0.3246 |             0    |
| gemini-3.5-flash-lite                    | source_generation | tri_manuel                      | 412 |             0.7427 |             0.7547 |             0    |
| mistral-large-latest                     | source_generation | generation_complement           |  83 |             0.5542 |             0.3651 |             0    |
| mistral-large-latest                     | source_generation | generation_originale            | 420 |             0.8119 |             0.784  |             0    |
| mistral-large-latest                     | source_generation | hardcase                        | 254 |             0.8583 |             0.6034 |             0    |
| mistral-large-latest                     | source_generation | transfert_racisme_antisemitisme | 194 |             1      |             0.3333 |             0    |
| mistral-large-latest                     | source_generation | transfert_racisme_xenophobie    | 137 |             0.9489 |             0.3246 |             0    |
| mistral-large-latest                     | source_generation | tri_manuel                      | 412 |             0.7524 |             0.7705 |             0    |
| openai/gpt-oss-120b                      | source_generation | generation_complement           |  83 |             0.5904 |             0.3867 |             0    |
| openai/gpt-oss-120b                      | source_generation | generation_originale            | 420 |             0.7024 |             0.6807 |             0.48 |
| openai/gpt-oss-120b                      | source_generation | hardcase                        | 254 |             0.5787 |             0.4385 |             1.97 |
| openai/gpt-oss-120b                      | source_generation | transfert_racisme_antisemitisme | 194 |             0.9948 |             0.3325 |             0    |
| openai/gpt-oss-120b                      | source_generation | transfert_racisme_xenophobie    | 137 |             0.9416 |             0.3233 |             0.73 |
| openai/gpt-oss-120b                      | source_generation | tri_manuel                      | 412 |             0.7063 |             0.731  |             1.21 |


## Matrices de confusion — mesure stricte (P7)

| modele                                   | verite              |   predit_racisme |   predit_xenophobie |   predit_antisemitisme |   predit_aucune_reponse |
|:-----------------------------------------|:--------------------|-----------------:|--------------------:|-----------------------:|------------------------:|
| _cf_meta_llama-3_3-70b-instruct-fp8-fast | vrai_racisme        |              230 |                 267 |                      3 |                       0 |
| _cf_meta_llama-3_3-70b-instruct-fp8-fast | vrai_xenophobie     |               13 |                 487 |                      0 |                       0 |
| _cf_meta_llama-3_3-70b-instruct-fp8-fast | vrai_antisemitisme  |               22 |                 109 |                    369 |                       0 |
| _cf_meta_llama-3_3-70b-instruct-fp8-fast | vrai_aucune_reponse |                0 |                   0 |                      0 |                       0 |
| gemini-3_5-flash-lite                    | vrai_racisme        |              303 |                 192 |                      5 |                       0 |
| gemini-3_5-flash-lite                    | vrai_xenophobie     |               23 |                 472 |                      5 |                       0 |
| gemini-3_5-flash-lite                    | vrai_antisemitisme  |                8 |                  13 |                    479 |                       0 |
| gemini-3_5-flash-lite                    | vrai_aucune_reponse |                0 |                   0 |                      0 |                       0 |
| mistral-large-latest                     | vrai_racisme        |              297 |                 199 |                      4 |                       0 |
| mistral-large-latest                     | vrai_xenophobie     |               29 |                 465 |                      6 |                       0 |
| mistral-large-latest                     | vrai_antisemitisme  |               15 |                   8 |                    477 |                       0 |
| mistral-large-latest                     | vrai_aucune_reponse |                0 |                   0 |                      0 |                       0 |
| openai_gpt-oss-120b                      | vrai_racisme        |              280 |                 212 |                      4 |                       4 |
| openai_gpt-oss-120b                      | vrai_xenophobie     |               34 |                 464 |                      0 |                       2 |
| openai_gpt-oss-120b                      | vrai_antisemitisme  |               93 |                  40 |                    360 |                       7 |
| openai_gpt-oss-120b                      | vrai_aucune_reponse |                0 |                   0 |                      0 |                       0 |


## Matrices de confusion — mesure conditionnelle (P7)

| modele                                   | verite             |   predit_racisme |   predit_xenophobie |   predit_antisemitisme |
|:-----------------------------------------|:-------------------|-----------------:|--------------------:|-----------------------:|
| _cf_meta_llama-3_3-70b-instruct-fp8-fast | vrai_racisme       |              230 |                 267 |                      3 |
| _cf_meta_llama-3_3-70b-instruct-fp8-fast | vrai_xenophobie    |               13 |                 487 |                      0 |
| _cf_meta_llama-3_3-70b-instruct-fp8-fast | vrai_antisemitisme |               22 |                 109 |                    369 |
| gemini-3_5-flash-lite                    | vrai_racisme       |              303 |                 192 |                      5 |
| gemini-3_5-flash-lite                    | vrai_xenophobie    |               23 |                 472 |                      5 |
| gemini-3_5-flash-lite                    | vrai_antisemitisme |                8 |                  13 |                    479 |
| mistral-large-latest                     | vrai_racisme       |              297 |                 199 |                      4 |
| mistral-large-latest                     | vrai_xenophobie    |               29 |                 465 |                      6 |
| mistral-large-latest                     | vrai_antisemitisme |               15 |                   8 |                    477 |
| openai_gpt-oss-120b                      | vrai_racisme       |              280 |                 212 |                      4 |
| openai_gpt-oss-120b                      | vrai_xenophobie    |               34 |                 464 |                      0 |
| openai_gpt-oss-120b                      | vrai_antisemitisme |               93 |                  40 |                    360 |


## Confiance médiane par sous-type (P7)

| modele                                   | sous_type            |   confiance_mediane |   n |
|:-----------------------------------------|:---------------------|--------------------:|----:|
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | ambigu               |                0.8  |  93 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | dog_whistle          |                0.8  | 138 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | exclusion            |                0.8  | 107 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | haine_implicite      |                0.8  | 298 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | hostilite_religieuse |                0.8  |  46 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | sarcasme             |                0.8  | 123 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | stereotype           |                0.8  | 238 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | complotisme          |                0.9  |  29 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | haine_explicite      |                0.9  | 428 |
| gemini-3.5-flash-lite                    | ambigu               |                0.85 |  93 |
| gemini-3.5-flash-lite                    | dog_whistle          |                0.85 | 138 |
| gemini-3.5-flash-lite                    | haine_implicite      |                0.85 | 298 |
| gemini-3.5-flash-lite                    | hostilite_religieuse |                0.85 |  46 |
| gemini-3.5-flash-lite                    | sarcasme             |                0.85 | 123 |
| gemini-3.5-flash-lite                    | stereotype           |                0.85 | 238 |
| gemini-3.5-flash-lite                    | complotisme          |                0.95 |  29 |
| gemini-3.5-flash-lite                    | exclusion            |                0.95 | 107 |
| gemini-3.5-flash-lite                    | haine_explicite      |                0.98 | 428 |
| mistral-large-latest                     | ambigu               |                0.8  |  93 |
| mistral-large-latest                     | haine_implicite      |                0.85 | 298 |
| mistral-large-latest                     | dog_whistle          |                0.9  | 138 |
| mistral-large-latest                     | sarcasme             |                0.9  | 123 |
| mistral-large-latest                     | complotisme          |                0.95 |  29 |
| mistral-large-latest                     | exclusion            |                0.95 | 107 |
| mistral-large-latest                     | haine_explicite      |                0.95 | 428 |
| mistral-large-latest                     | hostilite_religieuse |                0.95 |  46 |
| mistral-large-latest                     | stereotype           |                0.95 | 238 |
| openai/gpt-oss-120b                      | ambigu               |                0.6  |  92 |
| openai/gpt-oss-120b                      | haine_implicite      |                0.62 | 294 |
| openai/gpt-oss-120b                      | sarcasme             |                0.7  | 120 |
| openai/gpt-oss-120b                      | dog_whistle          |                0.8  | 136 |
| openai/gpt-oss-120b                      | stereotype           |                0.82 | 237 |
| openai/gpt-oss-120b                      | exclusion            |                0.95 | 107 |
| openai/gpt-oss-120b                      | hostilite_religieuse |                0.95 |  45 |
| openai/gpt-oss-120b                      | complotisme          |                0.98 |  28 |
| openai/gpt-oss-120b                      | haine_explicite      |                0.98 | 428 |


## Courbes risque-couverture (P7)

| modele                                   |   seuil_confiance |   couverture_pct |   accuracy_sur_predictions_retenues |   n_retenu |
|:-----------------------------------------|------------------:|-----------------:|------------------------------------:|-----------:|
| @cf/meta/llama-3.3-70b-instruct-fp8-fast |               0   |           100    |                              0.724  |       1500 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast |               0.2 |            98.73 |                              0.7313 |       1481 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast |               0.4 |            95.73 |                              0.7493 |       1436 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast |               0.5 |            95.73 |                              0.7493 |       1436 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast |               0.6 |            95.73 |                              0.7493 |       1436 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast |               0.7 |            91.73 |                              0.7674 |       1376 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast |               0.8 |            91.73 |                              0.7674 |       1376 |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast |               0.9 |            41    |                              0.9398 |        615 |
| gemini-3.5-flash-lite                    |               0   |           100    |                              0.836  |       1500 |
| gemini-3.5-flash-lite                    |               0.2 |           100    |                              0.836  |       1500 |
| gemini-3.5-flash-lite                    |               0.4 |            99.93 |                              0.8359 |       1499 |
| gemini-3.5-flash-lite                    |               0.5 |            99.67 |                              0.8368 |       1495 |
| gemini-3.5-flash-lite                    |               0.6 |            98.07 |                              0.847  |       1471 |
| gemini-3.5-flash-lite                    |               0.7 |            91.8  |                              0.8802 |       1377 |
| gemini-3.5-flash-lite                    |               0.8 |            91    |                              0.8821 |       1365 |
| gemini-3.5-flash-lite                    |               0.9 |            49.53 |                              0.9758 |        743 |
| mistral-large-latest                     |               0   |           100    |                              0.826  |       1500 |
| mistral-large-latest                     |               0.2 |           100    |                              0.826  |       1500 |
| mistral-large-latest                     |               0.4 |            99.73 |                              0.8262 |       1496 |
| mistral-large-latest                     |               0.5 |            99.67 |                              0.8268 |       1495 |
| mistral-large-latest                     |               0.6 |            99.67 |                              0.8268 |       1495 |
| mistral-large-latest                     |               0.7 |            99.07 |                              0.8277 |       1486 |
| mistral-large-latest                     |               0.8 |            91.8  |                              0.8388 |       1377 |
| mistral-large-latest                     |               0.9 |            69.87 |                              0.876  |       1048 |
| openai/gpt-oss-120b                      |               0   |           100    |                              0.7424 |       1487 |
| openai/gpt-oss-120b                      |               0.2 |            94.35 |                              0.7755 |       1403 |
| openai/gpt-oss-120b                      |               0.4 |            86.35 |                              0.8053 |       1284 |
| openai/gpt-oss-120b                      |               0.5 |            83.52 |                              0.8156 |       1242 |
| openai/gpt-oss-120b                      |               0.6 |            82.52 |                              0.8191 |       1227 |
| openai/gpt-oss-120b                      |               0.7 |            69.6  |                              0.8821 |       1035 |
| openai/gpt-oss-120b                      |               0.8 |            60.32 |                              0.9264 |        897 |
| openai/gpt-oss-120b                      |               0.9 |            51.58 |                              0.9609 |        767 |


## Test Q de Cochran (P8)

|   n_textes |   n_modeles |   statistique_Q |   ddl |     p_value | significatif_alpha_0_05   | interpretation                                                                                                                     |
|-----------:|------------:|----------------:|------:|------------:|:--------------------------|:-----------------------------------------------------------------------------------------------------------------------------------|
|       1500 |           4 |         237.209 |     3 | 3.81915e-51 | True                      | Au moins un modèle diffère significativement des autres en taux de succès ; des comparaisons par paires (McNemar) sont justifiées. |


## McNemar par paires, correction de Bonferroni (P8)

| modele_a                                 | modele_b              |   n_discordant_b_A_correct_B_incorrect |   n_discordant_c_A_incorrect_B_correct |   b_plus_c | methode         |   statistique |   p_value |   alpha_brut | significatif_alpha_brut   |   alpha_ajuste_bonferroni | significatif_alpha_ajuste   |
|:-----------------------------------------|:----------------------|---------------------------------------:|---------------------------------------:|-----------:|:----------------|--------------:|----------:|-------------:|:--------------------------|--------------------------:|:----------------------------|
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | gemini-3.5-flash-lite |                                     26 |                                    194 |        220 | khi2_continuite |      126.768  |  0        |         0.05 | True                      |                  0.008333 | True                        |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | mistral-large-latest  |                                     33 |                                    186 |        219 | khi2_continuite |      105.498  |  0        |         0.05 | True                      |                  0.008333 | True                        |
| mistral-large-latest                     | openai/gpt-oss-120b   |                                    178 |                                     43 |        221 | khi2_continuite |       81.2489 |  0        |         0.05 | True                      |                  0.008333 | True                        |
| gemini-3.5-flash-lite                    | openai/gpt-oss-120b   |                                    190 |                                     40 |        230 | khi2_continuite |       96.5261 |  0        |         0.05 | True                      |                  0.008333 | True                        |
| gemini-3.5-flash-lite                    | mistral-large-latest  |                                     62 |                                     47 |        109 | khi2_continuite |        1.7982 |  0.179934 |         0.05 | False                     |                  0.008333 | False                       |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | openai/gpt-oss-120b   |                                     79 |                                     97 |        176 | khi2_continuite |        1.642  |  0.200045 |         0.05 | False                     |                  0.008333 | False                       |


## Intervalles de confiance bootstrap par modèle (P8)

| modele                                   |   macro_f1_moyen_bootstrap |   macro_f1_ic95_bas |   macro_f1_ic95_haut |   accuracy_moyenne_bootstrap |   accuracy_ic95_bas |   accuracy_ic95_haut |
|:-----------------------------------------|---------------------------:|--------------------:|---------------------:|-----------------------------:|--------------------:|---------------------:|
| gemini-3.5-flash-lite                    |                     0.8323 |              0.8151 |               0.8504 |                       0.8358 |              0.818  |               0.854  |
| mistral-large-latest                     |                     0.822  |              0.8039 |               0.8409 |                       0.8259 |              0.8067 |               0.8453 |
| openai/gpt-oss-120b                      |                     0.7379 |              0.7174 |               0.7599 |                       0.736  |              0.714  |               0.758  |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast |                     0.7205 |              0.6985 |               0.7421 |                       0.7239 |              0.7    |               0.746  |


## Intervalles de confiance bootstrap sur les écarts par paire (P8)

| modele_a                                 | modele_b              |   difference_macro_f1_moyenne |   ic95_bas |   ic95_haut | ic_exclut_zero   |
|:-----------------------------------------|:----------------------|------------------------------:|-----------:|------------:|:-----------------|
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | gemini-3.5-flash-lite |                       -0.1118 |    -0.1302 |     -0.0937 | True             |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | mistral-large-latest  |                       -0.1015 |    -0.1202 |     -0.0827 | True             |
| gemini-3.5-flash-lite                    | openai/gpt-oss-120b   |                        0.0944 |     0.0753 |      0.1154 | True             |
| mistral-large-latest                     | openai/gpt-oss-120b   |                        0.0841 |     0.0643 |      0.103  | True             |
| @cf/meta/llama-3.3-70b-instruct-fp8-fast | openai/gpt-oss-120b   |                       -0.0174 |    -0.0367 |      0.0003 | False            |
| gemini-3.5-flash-lite                    | mistral-large-latest  |                        0.0103 |    -0.003  |      0.024  | False            |

