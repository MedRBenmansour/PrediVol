"""Tests des prédictions de l'API PrédiVol (lancer avec : python -m pytest -v test)."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

# Vol de référence : Delta, Atlanta → New York LaGuardia, le soir, sans météo
VOL = {
    "date_vol": "2023-07-14", "compagnie": "Delta Air Lines Inc", "aeroport_depart": "ATL", "aeroport_arrivee": "LGA",
    "moment_depart": "Evening", "categorie_distance": "Short Haul >1500Mi", "constructeur": "BOEING",
    "modele_avion": "B737", "age_avion": 12, "vols_jour_avion": 4, "trafic_depart_jour": 950, "trafic_arrivee_jour": 520,
}
TEMPETE = {"snow": 150, "prcp": 40, "wspd": 60}      # neige, forte pluie, vent fort


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:                       # l'API (et le modèle) ne démarre qu'une fois pour tout le fichier
        yield c


def predire(client, *vols):
    r = client.post("/predict", json={"vols": list(vols)})
    assert r.status_code == 200, r.text
    return r.json()["predictions"]


# --- Résultats corrects -------------------------------------------------------

def test_valeur_de_reference(client):
    """Même vol → même résultat qu'au moment de la sérialisation (le modèle n'a pas changé)."""
    p = predire(client, VOL)[0]
    assert p["retard_prevu_min"] == pytest.approx(-4.4, abs=0.5)


def test_structure_de_la_reponse(client):
    p = predire(client, VOL)[0]
    assert set(p) == {"retard_prevu_min", "borne_basse_min", "borne_haute_min", "risque"}
    assert p["borne_basse_min"] <= p["retard_prevu_min"] <= p["borne_haute_min"]
    assert p["risque"] in {"faible", "modéré", "élevé"}


def test_valeurs_plausibles(client):
    """Un retard prévu entre −60 et 300 min, une fourchette pas trop large."""
    p = predire(client, VOL)[0]
    assert -60 <= p["retard_prevu_min"] <= 300
    assert 0 < p["borne_haute_min"] - p["borne_basse_min"] < 300


def test_prediction_deterministe(client):
    """Deux appels identiques donnent exactement la même prédiction."""
    assert predire(client, VOL) == predire(client, VOL)


def test_plusieurs_vols(client):
    """3 vols envoyés → 3 prédictions, dans le même ordre."""
    tempete = {**VOL, "meteo_depart": TEMPETE, "meteo_arrivee": TEMPETE}
    preds = predire(client, VOL, tempete, VOL)
    assert len(preds) == 3
    assert preds[0] == preds[2]
    assert preds[1]["retard_prevu_min"] > preds[0]["retard_prevu_min"]


# --- Le modèle réagit dans le bon sens ---------------------------------------------

def test_meteo_difficile_augmente_le_retard(client):
    normal = predire(client, VOL)[0]
    tempete = predire(client, {**VOL, "meteo_depart": TEMPETE, "meteo_arrivee": TEMPETE})[0]
    assert tempete["retard_prevu_min"] > normal["retard_prevu_min"]
    assert tempete["risque"] == "élevé"


def test_risque_coherent_avec_le_retard(client):
    """Règle de l'API : élevé si retard ≥ 15 min ou borne haute ≥ 60 min ; faible si retard < 0."""
    for vol in [VOL, {**VOL, "meteo_depart": TEMPETE, "meteo_arrivee": TEMPETE}]:
        p = predire(client, vol)[0]
        if p["retard_prevu_min"] >= 15 or p["borne_haute_min"] >= 60:
            assert p["risque"] == "élevé"
        elif p["retard_prevu_min"] >= 0:
            assert p["risque"] == "modéré"
        else:
            assert p["risque"] == "faible"


# --- Cas particuliers ---------------------------------------------------------

def test_compagnie_et_aeroports_inconnus(client):
    """Valeurs jamais vues à l'entraînement : le modèle prédit quand même (pas d'erreur 500)."""
    p = predire(client, {**VOL, "compagnie": "Air Numidia", "aeroport_depart": "YOW", "aeroport_arrivee": "XYZ"})[0]
    assert isinstance(p["retard_prevu_min"], float)


def test_codes_aeroport_en_minuscules(client):
    assert predire(client, {**VOL, "aeroport_depart": "atl", "aeroport_arrivee": "lga"}) == predire(client, VOL)


def test_champs_facultatifs_absents(client):
    """Seuls les champs obligatoires : l'API prédit quand même."""
    minimal = {k: VOL[k] for k in ["date_vol", "compagnie", "aeroport_depart", "aeroport_arrivee",
                                   "moment_depart", "categorie_distance"]}
    assert len(predire(client, minimal)) == 1


def test_1000_vols_en_une_requete(client):
    r = client.post("/predict", json={"vols": [VOL] * 1000})
    assert r.status_code == 200 and len(r.json()["predictions"]) == 1000
    assert r.json()["duree_ms"] < 5000


# --- Données invalides → erreur 422 -------------------------------------------------

@pytest.mark.parametrize("modif", [
    {"age_avion": 200},                 # âge > 60 ans
    {"aeroport_depart": "A"},           # code aéroport trop court
    {"date_vol": "2023-13-40"},         # date impossible
    {"trafic_depart_jour": -5},         # trafic négatif
    {"compagnie": None},                # champ obligatoire vide
])
def test_vol_invalide(client, modif):
    assert client.post("/predict", json={"vols": [{**VOL, **modif}]}).status_code == 422


@pytest.mark.parametrize("corps", [{"vols": []}, {"vols": [VOL] * 1001}, {}])
def test_requete_invalide(client, corps):
    assert client.post("/predict", json=corps).status_code == 422
