"""Chargement du modèle PrédiVol sérialisé avec MLflow."""
import os

import mlflow.pyfunc
from dotenv import load_dotenv

load_dotenv()  # lit le fichier .env (jeton DagsHub, adresse du modèle)

# Par défaut : le dossier local models/predivol_modele.
# Pour charger depuis le registre DagsHub : MODEL_URI=models:/predivol-retard-arrivee/1 dans le .env
MODEL_URI = os.getenv("MODEL_URI", "models/predivol_modele")
_modele = None


def charger_modele():
    """Charge le modèle une seule fois (au démarrage de l'API)."""
    global _modele
    if MODEL_URI.startswith("models:/") and os.getenv("DAGSHUB_USER"):
        os.environ["MLFLOW_TRACKING_USERNAME"] = os.environ["DAGSHUB_USER"]
        os.environ["MLFLOW_TRACKING_PASSWORD"] = os.environ.get("DAGSHUB_TOKEN", "")
        mlflow.set_tracking_uri(f"https://dagshub.com/{os.environ['DAGSHUB_USER']}/predivol.mlflow")
    _modele = mlflow.pyfunc.load_model(MODEL_URI)
    return _modele


def obtenir_modele():
    return _modele


def infos_modele() -> dict:
    if _modele is None:
        return {}
    meta = _modele.metadata
    return {"source": MODEL_URI, "run_id": meta.run_id, "description": meta.metadata or {}}