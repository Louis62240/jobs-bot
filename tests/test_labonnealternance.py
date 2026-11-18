import httpx
import pytest
import respx

from jobbot import main
from jobbot.filters import CityResolver, evaluate
from jobbot.sources.labonnealternance import (
    ENDPOINT,
    LaBonneAlternance,
    LBAError,
    arrondir_rayon,
    to_offer,
)

VILLES = {"lille": {"lat": 50.63, "lon": 3.06}, "paris": {"lat": 48.86, "lon": 2.35}, "lyon": {}}


def job(jid, title, company="ACME", address="10 rue de la Gare 59000 LILLE"):
    return {"identifier": {"id": jid},
            "workplace": {"name": company, "location": {"address": address}},
            "apply": {"url": f"https://labonnealternance.apprentissage.beta.gouv.fr/emploi/{jid}"},
            "offer": {"title": title, "description": "Alternance de 2 ans, SQL, Power BI."}}


@pytest.mark.parametrize("km,attendu", [(5, 10), (30, 30), (31, 60), (500, 100)])
def test_rayon(km, attendu):
    assert arrondir_rayon(km) == attendu


def test_to_offer_et_offre_incomplete():
    o = to_offer(job("a1", "Data analyst"), "lille")
    assert (o.source, o.source_id, o.title, o.company, o.contract, o.city_key) == (
        "labonnealternance", "a1", "Data analyst", "ACME", "alternance", "lille")
    assert to_offer({"offer": {"title": "Sans id"}}, "lille") is None


@respx.mock
def test_une_recherche_par_ville_avec_jeton_et_doublons_ecartes():
    route = respx.get(ENDPOINT).mock(side_effect=[
        httpx.Response(200, json={"jobs": [job("a1", "Data analyst"), job("a2", "Data engineer")],
                                  "recruiters": [job("r1", "Entreprise sans offre")]}),
        httpx.Response(200, json={"jobs": [job("a2", "Data engineer"),
                                           job("p1", "Alternance BI", address="75009 PARIS")]}),
    ])
    src = LaBonneAlternance("JETON-TEST", VILLES, ["M1805", "M1403"], rayon_km=25)
    offers = src.fetch()
    assert [o.source_id for o in offers] == ["a1", "a2", "p1"]          # lyon ignorée (pas de coordonnées)
    req = route.calls[0].request
    assert req.headers["Authorization"] == "Bearer JETON-TEST"
    assert req.url.params["romes"] == "M1805,M1403" and req.url.params["radius"] == "30"


@respx.mock
def test_jeton_refuse_message_clair():
    respx.get(ENDPOINT).mock(return_value=httpx.Response(401))
    with pytest.raises(LBAError, match="LBA_API_KEY"):
        LaBonneAlternance("mauvais", VILLES, ["M1805"]).fetch()


def test_offre_lba_retenue_pour_alternance_data_meme_sans_alternance_dans_le_titre(profils, cfg):
    o = to_offer(job("a1", "Data analyst H/F"), "lille")
    o.city_key = CityResolver(cfg["villes"]).city_of(o)
    assert evaluate(profils["alternance-data"], o).ok
    assert not evaluate(profils["dev"], o).ok                           # contrat alternance


def test_source_ignoree_sans_jeton(caplog):
    cfg, _ = main.load()
    cfg["sources"] = {"labonnealternance": True}
    assert main.build_sources(cfg, {"LBA_API_KEY": ""}) == []
    assert "LBA_API_KEY vide" in caplog.text
