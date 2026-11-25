"""API PrédiVol : prédit le retard d'un vol à l'arrivée, avant le départ."""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.model_loader import charger_modele, infos_modele, obtenir_modele
from app.utils import Vol, vols_vers_dataframe

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("predivol")


@asynccontextmanager
async def demarrage(app: FastAPI):
    try:
        charger_modele()
        log.info("Modèle chargé : %s", infos_modele().get("source"))
    except Exception as e:                     # l'API démarre quand même : /ready dira que le modèle manque
        log.error("Modèle non chargé : %s", e)
    yield


app = FastAPI(title="API PrédiVol", version="1.0",
              description="Prédit, avant le départ, le retard d'un vol à l'arrivée (en minutes), avec une fourchette 10 %–90 %.",
              lifespan=demarrage)


class Requete(BaseModel):
    vols: list[Vol] = Field(..., min_length=1, max_length=1000)


class Prediction(BaseModel):
    retard_prevu_min: float
    borne_basse_min: float | None = None
    borne_haute_min: float | None = None
    risque: str


class Reponse(BaseModel):
    predictions: list[Prediction]
    modele: str
    duree_ms: float


@app.get("/health")
def health():
    """L'API répond (elle est en marche)."""
    return {"statut": "ok"}


@app.get("/ready")
def ready():
    """Le modèle est chargé et prêt à prédire."""
    if obtenir_modele() is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    return {"statut": "prêt", **infos_modele()}


@app.post("/predict", response_model=Reponse)
def predict(requete: Requete):
    """Envoie un ou plusieurs vols et reçoit le retard prévu (minutes) et sa fourchette."""
    modele = obtenir_modele()
    if modele is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    debut = time.perf_counter()
    try:
        sortie = modele.predict(vols_vers_dataframe(requete.vols))
    except Exception as e:
        log.exception("Erreur de prédiction")
        raise HTTPException(status_code=500, detail=f"Erreur de prédiction : {e}") from e
    predictions = []
    for _, ligne in sortie.iterrows():
        retard = float(ligne["retard_prevu_min"])
        haut = float(ligne["borne_haute_min"]) if "borne_haute_min" in ligne else None
        risque = "élevé" if retard >= 15 or (haut is not None and haut >= 60) else "modéré" if retard >= 0 else "faible"
        predictions.append(Prediction(retard_prevu_min=retard, risque=risque, borne_haute_min=haut,
                                      borne_basse_min=float(ligne["borne_basse_min"]) if "borne_basse_min" in ligne else None))
    duree = (time.perf_counter() - debut) * 1000
    log.info("%d vol(s) prédit(s) en %.1f ms", len(predictions), duree)
    return Reponse(predictions=predictions, modele=infos_modele().get("source", ""), duree_ms=round(duree, 1))