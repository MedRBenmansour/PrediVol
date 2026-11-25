# Journal de projet – PrédiVol (déploiement, UA3)

## Versions du modèle

| Version | Date | Modèle | MAE validation | MAE test | Où |
|---|---|---|---|---|---|
| 1 | 23 nov. 2026 | Gradient boosting, perte absolue + régression quantile 10 %/90 % | 20,97 min | 21,48 min | `models:/predivol-retard-arrivee/1` (DagsHub) et `models/predivol_modele/` |

Réglages (recherche aléatoire du Jalon 2, section 25) : loss = absolute_error, learning_rate = 0,0445, max_leaf_nodes = 221, min_samples_leaf = 237, l2_regularization = 0,0502, max_features = 0,5924, max_iter = 800.

## Journal des décisions

| Date | Décision | Pourquoi |
|---|---|---|
| 23 nov. | Structure du dépôt selon le module 1 de l'UA3 (app/, models/, test/, Dockerfile…) | Projet clair, relançable par une autre personne |
| 23 nov. | Ré-entraîner le modèle final avec les meilleurs réglages, sans refaire la recherche | La session Colab du Jalon 2 était fermée ; 15 min au lieu de 3 h. Même résultat (MAE test 21,48) |
| 23 nov. | Sérialiser au format `mlflow.pyfunc` (classe ModelePrediVol) | Le modèle contient aussi l'ajout des 5 variables et la fourchette : l'API envoie seulement les données brutes d'un vol |
| 23 nov. | Enregistrer le modèle dans le registre MLflow de DagsHub | Version numérotée, récupérable de n'importe où |
| 24 nov. | Python 3.13 partout (Colab, .venv-api, Docker) | Le modèle est sérialisé avec cloudpickle : il faut la même version de Python pour le recharger |
| 24 nov. | Versions épinglées dans requirements.txt (scikit-learn 1.6.1, mlflow 3.18.0…) | Reproductibilité : mêmes versions qu'à l'entraînement |
| 24 nov. | FastAPI avec 3 endpoints : /health, /ready, /predict | Endpoints demandés par le cours ; /docs pour tester |
| 24 nov. | Météo facultative dans /predict | Les prévisions ne sont pas toujours disponibles ; le modèle gère les valeurs manquantes |
| 24 nov. | Docker : python:3.13-slim, utilisateur non root, HEALTHCHECK, port 8080 | Bonnes pratiques du module (image légère, sécurité, surveillance) |
| 24 nov. | Lancement avec `-p 8081:8080` sur notre poste | Le port 8080 était déjà pris par un autre projet |
| 25 nov. | Relecture du README par le 2e membre de l'équipe, sur un autre poste | Vérifier que le projet se relance sans aide (checklist 5.3) ; README complété |
| 25 nov. | Ajout d'un 6e test : temps de réponse < 1 s | Vérifier automatiquement le critère de latence |
| 25 nov. | Ajout de `test_predictions.py` (19 tests) | Vérifier que les prédictions sont correctes, stables et réagissent dans le bon sens (météo), et que les cas limites sont gérés |

## Seuils et critères Go / No-Go

| Critère | Seuil | Résultat | Décision |
|---|---|---|---|
| MAE sur le test | ≤ 23,1 min (contrat) | 21,48 min | Go |
| Gain vs modèle naïf | ≥ 10 % | 17,5 % | Go |
| Tests de l'API | 25 / 25 | 25 / 25 | Go |
| Temps de prédiction | < 1 s par requête | 0,08 à 0,2 s (1re requête dans Docker : 2,4 s) | Go |
| Capture des retards ≥ 60 min | ≥ 36 % | 31,5 % | À améliorer (pas bloquant pour un prototype) |

## ✅ Checklist de validation

| | Critère | Preuve |
|---|---|---|
| ✅ | L'API répond à /health, /ready, /predict | Testé en local (uvicorn) et dans Docker (`predivol-api:v1`) ; /health et /ready : 200 ; /predict : 200, ATL→LGA Delta soir → 4,7 min (−16,8 à 47,7), risque modéré |
| ✅ | Tous les tests passent | `pytest` : 25 / 25 — 6 tests des endpoints (`test_api.py`) et 19 tests des prédictions (`test_predictions.py`) |
| ✅ | Temps de réponse acceptable | `duree_ms` : 77,8 ms dans Docker et environ 200 ms en local après la 1re requête (1re requête : 0,8 à 2,4 s, chargement) ; test `test_latence` : < 1 s |
| ✅ | Erreurs gérées proprement | 422 si données invalides (Pydantic, test `test_predict_invalide`) ; 503 si modèle non chargé (/ready, /predict) ; 500 avec message si la prédiction échoue ; erreurs écrites dans les logs |
| ✅ | README testé par quelqu'un d'autre | 25 nov. : Mohamed a suivi le README sur son propre poste Windows (venv, tests, API, Docker), sans aide de l'auteure. Ajouts faits au README après ce test : installer Python 3.13 s'il manque, démarrer Docker Desktop avant `docker build`, `/` renvoie 404 (utiliser /docs), `--env-file .env` facultatif |

## Risques du déploiement et mesures

| Risque | Mesure |
|---|---|
| Versions différentes entre entraînement et API | Python 3.13 et versions épinglées partout |
| Données invalides envoyées à l'API | Validation Pydantic : erreur 422 claire |
| Modèle absent ou non chargé | /ready renvoie 503 ; l'API démarre quand même et l'écrit dans les logs |
| Fuite du jeton DagsHub | Jeton dans `.env`, jamais sur GitHub ni dans l'image Docker |
| Dérive des données (nouvelles compagnies, saisons) | Surveiller la MAE chaque mois ; ré-entraîner si elle dépasse 23,1 min |
| Modèle lourd (fichier de 62 Mo) | Accepté pour le prototype ; à alléger (Git LFS ou registre MLflow seulement) |

## À faire ensuite

- Montrer en classe : sérialisation, structure, API dans Docker
- Pousser l'image dans un registre (Docker Hub) puis déployer (Google Cloud Run)
- Alléger le fichier du modèle et suivre les prédictions (logs, latence)