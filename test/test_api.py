"""Tests de l'API PrédiVol (lancer avec : pytest)."""
from fastapi.testclient import TestClient

from app.main import app

VOL = {
    "date_vol": "2023-07-14", "compagnie": "Delta Air Lines Inc", "aeroport_depart": "ATL", "aeroport_arrivee": "LGA",
    "moment_depart": "Evening", "categorie_distance": "Short Haul >1500Mi", "constructeur": "BOEING",
    "modele_avion": "B737", "age_avion": 12, "vols_jour_avion": 4, "trafic_depart_jour": 950, "trafic_arrivee_jour": 520,
    "meteo_depart": {"tavg": 28, "prcp": 12.5, "wspd": 15}, "meteo_arrivee": {"tavg": 26, "prcp": 0},
}


def test_health():
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200 and r.json()["statut"] == "ok"


def test_ready():
    with TestClient(app) as client:
        assert client.get("/ready").status_code == 200


def test_predict_valide():
    with TestClient(app) as client:
        r = client.post("/predict", json={"vols": [VOL]})
        assert r.status_code == 200
        p = r.json()["predictions"][0]
        assert isinstance(p["retard_prevu_min"], float)
        assert p["borne_basse_min"] <= p["retard_prevu_min"] <= p["borne_haute_min"]


def test_predict_meteo_absente():
    vol = {k: v for k, v in VOL.items() if not k.startswith("meteo")}
    with TestClient(app) as client:
        assert client.post("/predict", json={"vols": [vol]}).status_code == 200


def test_predict_invalide():
    with TestClient(app) as client:
        r = client.post("/predict", json={"vols": [{"compagnie": "Delta"}]})   # champs obligatoires manquants
        assert r.status_code == 422