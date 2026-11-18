import base64
from pathlib import Path

import pytest
from imap_tools import MailMessage

from jobbot.sources.email_alerts import hellowork, indeed, parser_for

FIX = Path(__file__).parent / "fixtures"

def clic(n, offer_id=12345):
    payload = f"moi@example.com\U0001faa2https://www.hellowork.com/fr-fr/emplois/{offer_id}.html?utm_source=x"
    seg = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    return f"https://emails.hellowork.com/clic/c/{n}/abc/{seg}"


HW_HTML = f"""<table><tr><td>
<a href="{clic(3)}">Data Analyst H/F</a>
<p>ACME</p><a href="#">Lille - 59</a><a href="#">CDI</a><a href="#">40 000 € / an</a>
<a href="{clic(5)}">Voir l’offre</a>
</td></tr></table>
<table><tr><td><a href="https://emails.hellowork.com/clic/c/9/zzz/x">Espace candidat</a></td></tr></table>"""

INDEED_HTML = """<table><tr><td>
<h2><a href="https://fr.indeed.com/rc/clk/dl?jk=abc123&from=ja">Ingénieur SQL</a></h2>
<p>Globex</p><p>Roubaix (59)</p><p>De 40 000 € à 50 000 € par an</p><p>il y a 2 jours</p>
</td></tr><tr><td>
<h2><a href="https://fr.indeed.com/pagead/clk/dl?mo=r&ad=XYZ">Data Engineer</a></h2>
<p>Initech</p><p>Paris (75)</p><p>il y a 1 jour</p>
</td></tr></table>
<a href="https://fr.indeed.com/jobs?q=data">Afficher tous les emplois</a>"""


def test_hellowork_synthetique():
    [o] = hellowork.parse(HW_HTML)
    assert (o.title, o.company, o.location, o.contract, o.salary) == (
        "Data Analyst H/F", "ACME", "Lille - 59", "CDI", "40 000 € / an")
    assert (o.source, o.source_id) == ("hellowork", "12345")
    assert o.url == "https://www.hellowork.com/fr-fr/emplois/12345.html"


def test_hellowork_badge_entre_entreprise_et_lieu():
    html = HW_HTML.replace("<p>ACME</p>", "<p>ACME</p><span>Super recruteur</span>")
    [o] = hellowork.parse(html)
    assert (o.company, o.location, o.contract) == ("ACME", "Lille - 59", "CDI")


def test_hellowork_id_stable_malgre_lien_de_suivi_different():
    autre = HW_HTML.replace("/3/abc/", "/7/autrehash/")
    assert autre != HW_HTML
    assert hellowork.parse(HW_HTML)[0].source_id == hellowork.parse(autre)[0].source_id


def test_indeed_synthetique():
    a, b = indeed.parse(INDEED_HTML)
    assert (a.source_id, a.url, a.company, a.location) == (
        "abc123", "https://fr.indeed.com/viewjob?jk=abc123", "Globex", "Roubaix (59)")
    assert a.salary.startswith("De 40")
    assert b.title == "Data Engineer" and b.url.startswith("https://fr.indeed.com/pagead/")
    assert len(b.source_id) == 16


def test_parser_for():
    assert parser_for("Indeed <alert@jobalert.indeed.com>".strip("<>")) is indeed.parse
    assert parser_for("alerte@emails.hellowork.com") is hellowork.parse
    assert parser_for("no-reply@accounts.google.com") is None
    assert parser_for("pub@evilhellowork.com") is None


def load(name):
    p = FIX / name
    if not p.exists():
        pytest.skip(f"fixture privée absente : {name}")
    return MailMessage.from_bytes(p.read_bytes())


@pytest.mark.parametrize("i", range(1, 9))
def test_hellowork_vrais_mails(i):
    m = load(f"hellowork_{i}.eml")
    offers = hellowork.parse(m.html)
    # le sujet annonce « N nouvelles offres » ; le mail peut en ajouter d'autres (suggestions)
    n = int(m.subject.split(":")[-1].split()[0])
    assert len(offers) >= min(n, 10)
    assert all(o.title and o.company and o.location for o in offers)
    assert not any(o.location == "Super recruteur" for o in offers)
    # jamais de lien de suivi (il contient l'adresse de la boîte) dans les offres
    assert all(o.url.startswith("https://www.hellowork.com/fr-fr/emplois/") for o in offers)


@pytest.mark.parametrize("i", [1, 2])
def test_indeed_vrais_mails(i):
    offers = indeed.parse(load(f"indeed_{i}.eml").html)
    assert offers
    assert all(o.title and o.company and o.location for o in offers)
    assert len({o.source_id for o in offers}) == len(offers)
