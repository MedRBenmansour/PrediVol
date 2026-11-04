# PrédiVol : prédiction des retards de vols

PrédiVol prédit le **retard à l'arrivée (en minutes)** des vols intérieurs américains de 2023, uniquement à partir d'informations **connues avant le départ** : compagnie, aéroports, horaire, avion, trafic prévu, jours fériés et météo.

Les expériences de modélisation sont suivies avec **MLflow**, hébergé sur **DagsHub**.

## Liens

| | |
|---|---|
| **Interface MLflow (publique)** | https://dagshub.com/MedRBenmansour/PrediVol.mlflow |
| Dépôt DagsHub | https://dagshub.com/MedRBenmansour/PrediVol |
| Expériences | https://dagshub.com/MedRBenmansour/PrediVol/experiments |
| Modèle enregistré | https://dagshub.com/MedRBenmansour/PrediVol/models |

## Contenu

| Fichier | Rôle |
|---|---|
| `PrediVol.ipynb` | Notebook principal : données, exploration, préparation, modèles et suivi MLflow |
| `PrediVol_avant_mlflow.ipynb` | Version du notebook avant l'ajout de MLflow |

Les données ne sont pas versionnées (trop volumineuses). Elles viennent du jeu Kaggle [2023 US Civil Flights, Delay, Meteo and Aircraft](https://www.kaggle.com/datasets/bordanova/2023-us-civil-flights-delay-meteo-and-aircraft), téléchargé automatiquement par le notebook avec `kagglehub`.

## Démarche

1. **Jalon 1** : collecte, exploration, jointure de la météo, variables dérivées (effet domino, trafic prévu, jours fériés), dictionnaire de données et nettoyage.
2. **Jalon 2** : prétraitement, séparation entraînement / validation / test (70 / 15 / 15), modèles de référence naïfs, puis Ridge, forêt aléatoire et gradient boosting.

## Suivi des expériences avec MLflow

Chaque exécution crée sur DagsHub :

- un **run parent** « comparaison … » avec les paramètres globaux, les figures et le journal des expériences ;
- un **run enfant par modèle** avec ses hyperparamètres et ses métriques de validation (MAE, RMSE, R², capture des gros retards, temps d'entraînement et de prédiction) ;
- le **meilleur modèle**, sauvegardé avec sa signature et enregistré dans le Model Registry sous le nom `PrediVol`.

## Relancer le notebook

```bash
pip install mlflow dagshub scikit-learn skops pandas kagglehub
```

Ouvrez ensuite `PrediVol.ipynb` (Jupyter, VS Code ou Colab) et exécutez les cellules dans l'ordre. Au premier appel de `dagshub.init`, un lien de connexion s'affiche : ouvrez-le pour autoriser l'accès. Vous pouvez aussi définir la variable d'environnement `DAGSHUB_USER_TOKEN` avec un token DagsHub.

Pour suivre les expériences dans **votre propre** dépôt, remplacez `repo_owner` et `repo_name` dans l'appel `dagshub.init(...)`.

Pour charger le modèle enregistré :

```python
import mlflow, dagshub

dagshub.init(repo_owner="MedRBenmansour", repo_name="PrediVol", mlflow=True)
modele = mlflow.pyfunc.load_model("models:/PrediVol/1")
```
