# PrédiVol – Prédire le retard d'un vol avant le départ

Projet IA du groupe 7 (Mohamed Ridha Benmansour et Mariem Gnichi) – Collège La Cité, automne 2026.

PrédiVol prédit, **avant le départ**, le retard d'un vol à l'arrivée (en minutes), avec une fourchette 10 %–90 %.
Client fictif : Air Numidia (planificateurs du centre de contrôle des opérations).

- Données : vols intérieurs américains 2023 (Kaggle, *US 2023 Civil Flights, Delays, Meteo and Aircrafts*)
- Modèle final : gradient boosting (perte absolue), MAE de **21,5 min** sur le test (naïf : 26,0 min, soit 17,5 % de mieux)
- Suivi des expériences : https://dagshub.com/gnichimariem1-cell/predivol.mlflow
- Modèle enregistré : `models:/predivol-retard-arrivee/1` (registre MLflow) et `models/predivol_modele/` (local)

## Structure du projet

```
app/main.py            API FastAPI : endpoints /health, /ready, /predict
app/model_loader.py    chargement du modèle MLflow (mlflow.pyfunc.load_model)
app/utils.py           schéma d'un vol et préparation des données
models/predivol_modele modèle sérialisé avec MLflow (pyfunc)
test/test_api.py       tests de l'API (pytest)
notebooks/             dépendances du notebook
PrediVol.ipynb         données, modèles, optimisation (Jalons 1 et 2), sérialisation (sections 30 à 32)
requirements.txt       dépendances de l'API, versions épinglées
Dockerfile             image Docker de l'API
journal_de_projet.md   choix, versions et décisions
.env                   secrets (non versionné)
```

## Lancer l'API en local

Python **3.13** est obligatoire (même version que l'entraînement du modèle).

```powershell
py -V:3.13 -m venv .venv-api
.venv-api\Scripts\activate
pip install -r requirements.txt pytest httpx
uvicorn app.main:app --port 8080
```

Ouvrir http://localhost:8080/docs.

## Tester

```powershell
python -m pytest -q test
```

5 tests : `/health`, `/ready`, prédiction valide, prédiction sans météo, données invalides (erreur 422).

## Lancer avec Docker

```powershell
docker build -t predivol-api:v1 .
docker run --rm -p 8080:8080 --env-file .env predivol-api:v1
```

Si le port 8080 est déjà utilisé : `-p 8081:8080`, puis ouvrir http://localhost:8081/docs.

## Faire une prédiction

`POST /predict` :

```json
{"vols": [{
  "date_vol": "2023-07-14", "compagnie": "Delta Air Lines Inc",
  "aeroport_depart": "ATL", "aeroport_arrivee": "LGA",
  "moment_depart": "Evening", "categorie_distance": "Short Haul >1500Mi",
  "vols_jour_avion": 4, "trafic_depart_jour": 950, "trafic_arrivee_jour": 520
}]}
```

Réponse :

```json
{"predictions": [{"retard_prevu_min": 4.7, "borne_basse_min": -16.8, "borne_haute_min": 47.7, "risque": "modéré"}]}
```

## Fichier .env

```
MODEL_URI=models/predivol_modele
# MODEL_URI=models:/predivol-retard-arrivee/1
DAGSHUB_USER=gnichimariem1-cell
DAGSHUB_TOKEN=votre_jeton
```