import pytest

from jobbot.models import Offer
from jobbot.sources.email_alerts import publishable
from jobbot.sources.email_alerts.canonical import canonical
from jobbot.storage import Store


@pytest.mark.parametrize("url,key,canon", [
    ("https://www.linkedin.com/comm/jobs/view/4123456789/?trackingId=abc&refId=x",
     "linkedin:4123456789", "https://www.linkedin.com/jobs/view/4123456789/"),
    ("https://fr.linkedin.com/jobs/view/data-analyst-alternance-at-acme-4123456789",
     "linkedin:4123456789", "https://www.linkedin.com/jobs/view/4123456789/"),
    ("https://www.linkedin.com/jobs/search/?currentJobId=4123456789&geoId=1",
     "linkedin:4123456789", "https://www.linkedin.com/jobs/view/4123456789/"),
    ("https://fr.indeed.com/rc/clk?jk=0123456789abcdef&from=ja",
     "indeed:0123456789abcdef", "https://fr.indeed.com/viewjob?jk=0123456789abcdef"),
    ("https://www.hellowork.com/fr-fr/emplois/85495357.html?utm_source=alerte",
     "hellowork:85495357", "https://www.hellowork.com/fr-fr/emplois/85495357.html"),
    ("https://jobs.makesense.org/en/jobs/le-collectif-stage-coordinateur-5sbvIVLD5zl2rs0WvGLj?source=mail",
     "makesense:5sbvIVLD5zl2rs0WvGLj",
     "https://jobs.makesense.org/fr/jobs/le-collectif-stage-coordinateur-5sbvIVLD5zl2rs0WvGLj"),
    ("https://www.welcometothejungle.com/en/companies/acme/jobs/stage-charge-detudes_paris?q=1",
     "wttj:acme/stage-charge-detudes_paris",
     "https://www.welcometothejungle.com/fr/companies/acme/jobs/stage-charge-detudes_paris"),
])
def test_liens_reconnus(url, key, canon):
    c = canonical(url)
    assert c is not None and (c.key, c.url) == (key, canon)


@pytest.mark.parametrize("url", [
    "https://www.linkedin.com/feed/",
    "https://fr.indeed.com/jobs?q=data",            # page de recherche, pas une offre
    "https://www.hellowork.com/fr-fr/candidat/mes-alertes.html",
    "https://exemple.fr/offre/42",
])
def test_liens_non_reconnus(url):
    assert canonical(url) is None


def test_publishable_rend_le_lien_canonique():
    o = Offer("x", "1", "Dev", "A", "Paris",
              "https://www.linkedin.com/comm/jobs/view/4123456789/?trackingId=abc")
    [kept], _ = publishable([o], "boite@gmail.com")
    assert kept.url == "https://www.linkedin.com/jobs/view/4123456789/"


def test_meme_lien_canonique_deja_vu_meme_si_autre_source(tmp_path):
    s = Store(tmp_path / "t.db")
    url = "https://www.linkedin.com/jobs/view/4123456789/"
    s.save("dev", Offer("generic", "a", "Développeur Java", "ACME", "Paris", url), notified=True)
    autre = Offer("linkedin", "b", "Dév Java (H/F) - CDI", "Acme SAS", "Paris 9e", url)
    assert not s.is_new("dev", autre)
    assert s.is_new("stage-asso", autre)   # dédoublonnage par profil
