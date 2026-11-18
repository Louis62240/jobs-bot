"""Pages carrières (API simulées, sans réseau) + recherche dans l'annonce complète / via l'alerte."""

import os
import time

import httpx
import pytest

from jobbot.filters import evaluate
from jobbot.models import Offer
from jobbot.notifiers.discord import build_payload, found_in, recap_line
from jobbot.sources.careers import Careers, check_config, plain
from jobbot.sources.email_alerts import alert_name

FICHE_SQL = "<p>Vous écrirez des requêtes <strong>SQL</strong> sur BigQuery.</p>"

REPONSES = {
    "boards-api.greenhouse.io": {"jobs": [{
        "id": 42, "title": "Alternance Analyste Finance ", "absolute_url": "https://job-boards.greenhouse.io/acme/jobs/42",
        "location": {"name": "Paris, France"},
        "content": "&lt;p&gt;Requêtes SQL &amp;amp; reporting&lt;/p&gt;"}]},
    "api.lever.co": [{
        "id": "abc", "text": "Alternant Contrôle de gestion", "hostedUrl": "https://jobs.lever.co/acme/abc",
        "categories": {"commitment": "Alternance", "location": "Lille", "allLocations": ["Lille", "Paris"]},
        "descriptionPlain": "Rejoignez-nous.", "lists": [{"text": "Profil", "content": "<li>Power BI</li>"}],
        "additionalPlain": ""}],
    "api.ashbyhq.com": {"jobs": [
        {"id": "u1", "title": "Data Intern", "location": "Paris", "secondaryLocations": [{"location": "Lille"}],
         "jobUrl": "https://jobs.ashbyhq.com/acme/u1", "employmentType": "Intern", "descriptionPlain": "dbt",
         "isListed": True},
        {"id": "u2", "title": "Caché", "location": "Paris", "jobUrl": "x", "isListed": False}]},
    "apply.workable.com": {"name": "Acme", "jobs": [{
        "title": "Stage ESG - 2027", "shortcode": "AB12", "url": "https://apply.workable.com/j/AB12",
        "locations": [{"city": "Lille", "country": "France"}], "employment_type": "Internship",
        "description": FICHE_SQL}]},
    "acme.recruitee.com": {"offers": [{
        "id": 7, "title": "CDI - Data Analyst", "careers_url": "https://acme.recruitee.com/o/data-analyst",
        "location": "Paris, Île-de-France, France", "employment_type_code": "fulltime_permanent",
        "description": "<p>Analyse</p>", "requirements": "<p>SQL</p>"}]},
    "api.smartrecruiters.com": {"totalFound": 1, "content": [{
        "id": "999", "name": "Alternance Data Analyst (h/f)",
        "location": {"city": "Hem", "address": "Hem (59)"}, "typeOfEmployment": {"id": "apprenticeship"}}]},
}


def client(fail=()):
    def handler(req: httpx.Request):
        host = req.url.host
        if host in fail:
            return httpx.Response(500)
        if host == "api.lever.co" and "eu" in fail:
            return httpx.Response(404)
        return httpx.Response(200, json=REPONSES[host]) if host in REPONSES else httpx.Response(404)
    return httpx.Client(transport=httpx.MockTransport(handler))


ENTREPRISES = [
    {"nom": "Acme GH", "ats": "greenhouse", "id": "acme"},
    {"nom": "Acme Lever", "ats": "lever", "id": "acme"},
    {"nom": "Acme Ashby", "ats": "ashby", "id": "acme"},
    {"nom": "Acme Workable", "ats": "workable", "id": "acme"},
    {"nom": "Acme Recruitee", "ats": "recruitee", "id": "acme"},
    {"nom": "Acme SR", "ats": "smartrecruiters", "id": "acme"},
]


def by_source(offers):
    return {o.source: o for o in offers}


def test_six_outils():
    offers = Careers(ENTREPRISES, client=client()).fetch()
    assert len(offers) == 6                                     # l'offre Ashby non publiée est ignorée
    o = by_source(offers)
    gh = o["greenhouse"]
    assert (gh.source_id, gh.title, gh.company, gh.location) == ("acme:42", "Alternance Analyste Finance",
                                                                  "Acme GH", "Paris, France")
    assert gh.fiche == "Requêtes SQL & reporting"               # HTML échappé deux fois
    assert gh.description == ""                                 # l'annonce n'est pas affichée sur Discord
    assert o["lever"].location == "Lille / Paris" and "Power BI" in o["lever"].fiche
    assert o["lever"].contract == "Alternance"
    assert o["ashby"].location == "Paris / Lille" and o["ashby"].contract == "Intern"
    assert o["workable"].url == "https://apply.workable.com/j/AB12" and "SQL" in o["workable"].fiche
    assert o["recruitee"].fiche == "Analyse SQL"
    sr = o["smartrecruiters"]
    assert (sr.location, sr.contract, sr.fiche) == ("Hem (59)", "apprenticeship", "")
    assert sr.url == "https://jobs.smartrecruiters.com/acme/999"


def test_une_entreprise_en_panne_ne_bloque_pas_les_autres():
    src = Careers(ENTREPRISES, client=client(fail={"boards-api.greenhouse.io"}))
    assert len(src.fetch()) == 5
    assert set(src.failed) == {"Acme GH"}


def test_toutes_en_panne_source_en_echec():
    src = Careers(ENTREPRISES[:1], client=client(fail={"boards-api.greenhouse.io"}))
    with pytest.raises(RuntimeError):
        src.fetch()


def test_un_passage_par_heure(tmp_path):
    stamp = tmp_path / "carrieres.stamp"
    src = Careers(ENTREPRISES[:1], stamp=stamp, every_min=60, client=client())
    assert src.fetch() and stamp.exists()
    assert src.fetch() == []                                   # trop tôt
    old = time.time() - 3600
    os.utime(stamp, (old, old))
    assert src.fetch()


def test_config_invalide():
    with pytest.raises(SystemExit, match="ats parmi"):
        check_config([{"nom": "X", "ats": "workday", "id": "x"}])


def test_plain():
    assert plain("&lt;p&gt;A &amp;amp; B&lt;/p&gt;") == "A & B"
    assert plain("<li>un</li><li>deux</li>") == "un deux"


# --- Recherche dans l'annonce complète / via l'alerte du site -------------------------

def mk(cities, title, fiche="", alert="", contract="alternance", location="Paris, France"):
    o = Offer("test", title, title, "ACME", location, "https://x", contract=contract, fiche=fiche, alert=alert)
    o.city_key = cities.city_of(o)
    return o


def test_mot_cle_dans_la_fiche(profils, cities):
    p = profils["alternance-data"]
    v = evaluate(p, mk(cities, "Alternance Contrôle de gestion", fiche="Requêtes SQL et Power BI"))
    assert v.ok and v.matched_on[0].startswith("fiche:")
    assert v.score == 40                                       # pas de bonus « titre »
    # « data » seul dans l'annonce ne suffit pas (« culture data-driven »)
    assert not evaluate(p, mk(cities, "Alternance Contrôle de gestion", fiche="culture data-driven")).ok


def test_fiche_ignoree_par_les_profils_sans_reglage(profils, cities):
    o = mk(cities, "Chargé de clientèle", fiche="Angular et Java au quotidien", contract="cdi")
    assert not evaluate(profils["dev"], o).ok


def test_alerte_du_site_suffit(profils, cities):
    p = profils["alternance-data"]
    o = mk(cities, "Alternance Chargé de reporting", alert="data OR sql (Paris (75))")
    v = evaluate(p, o)
    assert v.ok and v.matched_on == ["alerte:data OR sql (Paris (75))"]
    assert v.score == 30 and any("alerte du site" in d for d in v.score_detail)
    # une alerte d'un autre sujet ne suffit pas
    assert not evaluate(p, mk(cities, "Alternance Chargé de reporting", alert="stage (RSE OR ESG) (Paris (75))")).ok
    # les autres filtres s'appliquent toujours
    assert not evaluate(p, mk(cities, "CDI Chargé de reporting", alert="data OR sql", contract="cdi")).ok


def test_discord_dit_ou_le_mot_a_ete_trouve(profils, cities):
    p = profils["alternance-data"]
    o = mk(cities, "Alternance Chargé de reporting", alert="data OR sql (Paris (75))")
    v = evaluate(p, o)
    assert "d'après l'alerte du site « data OR sql (Paris (75)) »" in found_in(v)
    assert "🔔" in recap_line(o, v)
    o2 = mk(cities, "Alternance Contrôle de gestion", fiche="SQL")
    v2 = evaluate(p, o2)
    assert found_in(v2).startswith("📄 annonce complète")
    fields = build_payload(o2, p, v2)["embeds"][0]["fields"]
    assert any(f["value"].startswith("📄") for f in fields)


@pytest.mark.parametrize("subject,attendu", [
    ("Data Analyst H/F à CA. 12 offres d'emploi supplémentaires data OR sql (Paris (75))", "data OR sql (Paris (75))"),
    ("Lead Developer H/F à Goweb. 1 offre d'emploi développeur (Lille (59))", "développeur (Lille (59))"),
    ("Votre alerte Data analyst - Lille (59) - CDI : 1 nouvelle offre", "Data analyst - Lille (59) - CDI"),
    ("Votre alerte Dev / Java - Paris - CDI\n CDD : 16 nouvelles offres", "Dev / Java - Paris - CDI CDD"),
    ("Louis\xa0: votre alerte Emploi pour Développeur (Lille Et Périphérie) a été créée", "Développeur (Lille Et Périphérie)"),
    ("14 nouvelles  offres  d'emploi qui correspondent à votre alerte (Stage - Paris) - 17/11/26", "Stage - Paris"),
    ("Bienvenue sur Hellowork", ""),
])
def test_nom_de_l_alerte(subject, attendu):
    assert alert_name(subject) == attendu
