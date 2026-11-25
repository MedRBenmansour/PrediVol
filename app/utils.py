"""Préparation des données d'un vol pour le modèle PrédiVol."""
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class Meteo(BaseModel):
    """Météo du jour à un aéroport (prévisions). Tous les champs sont facultatifs."""
    tavg: Optional[float] = Field(None, description="Température moyenne (°C)")
    tmin: Optional[float] = Field(None, description="Température minimale (°C)")
    tmax: Optional[float] = Field(None, description="Température maximale (°C)")
    prcp: Optional[float] = Field(None, description="Précipitations (mm)")
    snow: Optional[float] = Field(None, description="Neige (mm)")
    wdir: Optional[float] = Field(None, description="Direction du vent (degrés)")
    wspd: Optional[float] = Field(None, description="Vitesse du vent (km/h)")
    pres: Optional[float] = Field(None, description="Pression (hPa)")


class Vol(BaseModel):
    """Informations d'un vol, toutes connues AVANT le départ."""
    date_vol: date = Field(..., examples=["2023-07-14"])
    compagnie: str = Field(..., examples=["Delta Air Lines Inc"])
    aeroport_depart: str = Field(..., min_length=3, max_length=4, examples=["ATL"])
    aeroport_arrivee: str = Field(..., min_length=3, max_length=4, examples=["LGA"])
    moment_depart: str = Field(..., examples=["Evening"], description="Morning, Afternoon, Evening ou Night")
    categorie_distance: str = Field(..., examples=["Short Haul >1500Mi"])
    constructeur: Optional[str] = Field(None, examples=["BOEING"])
    modele_avion: Optional[str] = Field(None, examples=["B737"])
    age_avion: Optional[float] = Field(None, ge=0, le=60, examples=[12])
    vols_jour_avion: Optional[float] = Field(None, ge=1, examples=[4], description="Vols de cet avion ce jour-là")
    trafic_depart_jour: Optional[float] = Field(None, ge=0, examples=[950], description="Vols programmés ce jour-là au départ")
    trafic_arrivee_jour: Optional[float] = Field(None, ge=0, examples=[520], description="Vols programmés ce jour-là à l'arrivée")
    meteo_depart: Optional[Meteo] = None
    meteo_arrivee: Optional[Meteo] = None


# Jours fériés américains (comme dans le notebook, section 5)
try:
    import holidays
    _FERIES = np.sort(pd.to_datetime([d for a in range(2022, 2031) for d in holidays.US(years=a)]).values.astype("datetime64[D]"))
except Exception:  # liste de secours (2023)
    _FERIES = np.sort(pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-16", "2023-02-20", "2023-05-29", "2023-06-19",
                                      "2023-07-04", "2023-09-04", "2023-10-09", "2023-11-10", "2023-11-11", "2023-11-23",
                                      "2023-12-25"]).values.astype("datetime64[D]"))


def jours_jusqu_ferie(jour: date) -> float:
    """Nombre de jours jusqu'au jour férié le plus proche, plafonné à 15."""
    j = np.datetime64(jour, "D")
    pos = np.searchsorted(_FERIES, j)
    avant = _FERIES[max(pos - 1, 0)]
    apres = _FERIES[min(pos, len(_FERIES) - 1)]
    ecart = min(abs((j - avant).astype(int)), abs((apres - j).astype(int)))
    return float(min(ecart, 15))


def vols_vers_dataframe(vols: list[Vol]) -> pd.DataFrame:
    """Transforme les vols reçus par l'API en tableau avec les colonnes attendues par le modèle."""
    lignes = []
    for v in vols:
        ligne = {
            "Airline": v.compagnie, "Dep_Airport": v.aeroport_depart.upper(), "Arr_Airport": v.aeroport_arrivee.upper(),
            "DepTime_label": v.moment_depart, "Distance_type": v.categorie_distance,
            "Manufacturer": v.constructeur or "inconnu", "Model": v.modele_avion or "inconnu",
            "mois": float(v.date_vol.month), "jour_semaine": float(v.date_vol.isoweekday()),   # 1 = lundi … 7 = dimanche
            "Aicraft_age": v.age_avion, "vols_jour_avion": v.vols_jour_avion,
            "trafic_dep_jour": v.trafic_depart_jour, "trafic_arr_jour": v.trafic_arrivee_jour,
            "jours_ferie": jours_jusqu_ferie(v.date_vol),
        }
        for cote, meteo in [("dep", v.meteo_depart), ("arr", v.meteo_arrivee)]:
            for nom, valeur in (meteo or Meteo()).model_dump().items():
                ligne[f"{nom}_{cote}"] = valeur
        lignes.append(ligne)
    d = pd.DataFrame(lignes)
    num = [c for c in d.columns if c not in ("Airline", "Dep_Airport", "Arr_Airport", "DepTime_label",
                                             "Distance_type", "Manufacturer", "Model")]
    d[num] = d[num].astype("float64")          # valeur absente = NaN, que le modèle sait gérer
    return d