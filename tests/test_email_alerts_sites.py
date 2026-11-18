"""Parsers LinkedIn, Jobs that make sense, Coordination SUD, Les Jeudis + routage des expéditeurs."""

import base64
import json
import re
from pathlib import Path

import pytest
from imap_tools import MailMessage

from jobbot.sources.email_alerts import (
    EmailAlerts,
    coordinationsud,
    lesjeudis,
    linkedin,
    makesense,
    parser_for,
)

FIX = Path(__file__).parent / "fixtures"
BOX = "pre.nom.test@gmail.com"


def load(name):
    p = FIX / name
    if not p.exists():
        pytest.skip(f"fixture privée absente : {name}")
    return MailMessage.from_bytes(p.read_bytes())


def mail(sender, html, subject="Alerte"):
    raw = (f"From: {sender}\r\nTo: {BOX}\r\nSubject: {subject}\r\n"
           f"Date: Sun, 15 Nov 2026 08:00:00 +0000\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{html}")
    return MailMessage.from_bytes(raw.encode())


# --- LinkedIn ---------------------------------------------------------------------

LI = "https://www.linkedin.com/comm/jobs/view/{}/?trackingId=abc&refId=xyz"
LI_HTML = f"""
<table><tbody><tr><td><a href="{LI.format(4487166389)}"><img alt=""></a></td></tr>
<tr><td><a href="{LI.format(4487166389)}">Développeur Back-End (H/F)</a></td></tr>
<tr><td><p>Claranet France · Lille, Hauts-de-France, France</p></td></tr>
<tr><td><p>Recrutement actif</p></td></tr></tbody></table>
<table><tbody><tr><td><a href="{LI.format(4471203282)}">Stratégie &amp;amp; Développement</a></td></tr>
<tr><td><p>Infotel · Ville de Paris, Île-de-France, France</p></td></tr>
<tr><td><p>45 000 € - 50 000 €/an</p></td></tr></tbody></table>
<a href="https://www.linkedin.com/comm/jobs/search-results/?x=1">Voir toutes les offres d’emploi</a>"""


def test_linkedin_synthetique():
    a, b = linkedin.parse(LI_HTML)
    assert (a.source, a.source_id, a.title, a.company, a.location) == (
        "linkedin", "4487166389", "Développeur Back-End (H/F)", "Claranet France",
        "Lille, Hauts-de-France, France")
    assert a.url == "https://www.linkedin.com/jobs/view/4487166389/"   # sans suivi
    assert b.title == "Stratégie & Développement"                      # double échappement
    assert b.salary == "45 000 € - 50 000 €/an"


@pytest.mark.parametrize("i", range(1, 13))
def test_linkedin_vrais_mails(i):
    m = load(f"linkedin_{i}.eml")
    offers = linkedin.parse(m.html)
    ids = set(re.findall(r"jobs/view/(\d+)", m.html))
    assert offers and {o.source_id for o in offers} == ids     # aucune offre oubliée
    assert all(o.title and o.company and o.location for o in offers)
    assert not any("&amp;" in o.title for o in offers)


# --- Jobs that make sense ------------------------------------------------------------

def cio(url):
    seg = base64.urlsafe_b64encode(json.dumps({"href": url, "email_id": "x"}).encode()).decode().rstrip("=")
    return f"https://e.customeriomail.com/e/c/{seg}/sig"


def ms_card(href, company, title, *rest):
    ps = "".join(f"<p>{x}</p>" for x in rest)
    return (f"<table><tr><td><table><tr><td><p>{company}</p><a href='{href}'>{title}</a>{ps}"
            "</td></tr></table></td></tr></table>")


MS_HTML = ("<p>Votre alerte · Stage - Paris</p>"
           + ms_card(cio("https://jobs.makesense.org/jobs/abcDEF123?utm_source=mail"), "muto",
                     "(STAGE) Chargé·e de communication", "On lutte contre le gaspillage.", "Stage", "Paris, France")
           + ms_card(cio("https://jobs.makesense.org/jobs/zzz999"), "each One",
                     "Chargé de communication - Stage", "Inclusion.", "Stage", "9 Rue des Filles Saint-Thomas")
           + ms_card(cio("https://jobs.makesense.org/api/v1/exclusivities/K/redirect"), "Kedge",
                     "MSc Impact Finance", "2 ans", "Partenariat sponsorisé"))


def test_makesense_synthetique():
    a, b = makesense.parse(MS_HTML)       # la pub sponsorisée est ignorée
    assert (a.source_id, a.company, a.title, a.location, a.contract, a.description) == (
        "abcDEF123", "muto", "(STAGE) Chargé·e de communication", "Paris, France", "Stage",
        "On lutte contre le gaspillage.")
    assert a.url == "https://jobs.makesense.org/jobs/abcDEF123"
    assert a.city_key is None             # « Paris, France » : le filtre ville s'en charge
    assert b.city_key == "paris"          # adresse sans ville → ville de l'alerte


def test_makesense_vrai_mail():
    m = load("makesense_1.eml")
    offers = makesense.parse(m.html)
    assert len(offers) == int(m.subject.split()[0])            # « 14 nouvelles offres… »
    assert all(o.url.startswith("https://jobs.makesense.org/jobs/") for o in offers)
    assert all(o.title and o.company and o.location for o in offers)


# --- Coordination SUD ----------------------------------------------------------------

CS_HTML = """<table><tr><td><p>Votre sélection d'offres d'emplois et de missions</p>
<h2><a href="http://www.coordinationsud.org?p=111&u=999">Stage Assistant – Analyste – Paris</a></h2>
<p>Handicap International - 16/11/2026</p><p><b>Contrat</b> : Stage ou Alternance</p>
<p><b>Localisation(s)</b> : Europe, France</p>
<h2><a href="http://www.coordinationsud.org?p=222&u=999">Stage – Gestion de programme</a></h2>
<p>On Purpose - 17/11/2026</p><p><b>Contrat</b> : Stage ou Alternance</p>
<p><b>Localisation(s)</b> : Europe, France</p>
<h2><a href="https://www.coordinationsud.org/formation/reco/">RECO Module 2</a></h2><p>FORMATION - 05/11/26</p>
</td></tr></table>"""


def test_coordinationsud_synthetique():
    a, b = coordinationsud.parse(CS_HTML)
    assert (a.source_id, a.company, a.contract, a.location) == (
        "111", "Handicap International", "Stage ou Alternance", "Europe, France")
    assert a.url == "https://www.coordinationsud.org/?p=111"     # sans l'identifiant d'abonné
    assert a.city_key == "paris" and b.city_key is None


@pytest.mark.parametrize("i", [1, 2])
def test_coordinationsud_vrais_mails(i):
    offers = coordinationsud.parse(load(f"coordsud_{i}.eml").html)
    assert offers and all(o.company and o.title for o in offers)
    assert not any("u=" in o.url for o in offers)


# --- Les Jeudis ----------------------------------------------------------------------

LJ_HTML = """<table><tr><td><a href="https://lesjeudis.com/offers/119cd1c1-fcfc-43fc-913d-9b83cf95f7de"
style="display:block;"></a><p>AI Content Specialist</p><p>Voodoo SAS · Paris</p><p>60% match</p></td></tr>
<tr><td><a href="https://lesjeudis.com/offers/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"></a>
<p>Architecte Système</p><p>Thales · Lille</p><p>58% match</p></td></tr></table>
<a href="https://lesjeudis.com/alerts">Gérer mes alertes →</a>"""


def test_lesjeudis_synthetique():
    a, b = lesjeudis.parse(LJ_HTML)
    assert (a.title, a.company, a.location) == ("AI Content Specialist", "Voodoo SAS", "Paris")
    assert a.url == "https://lesjeudis.com/offers/119cd1c1-fcfc-43fc-913d-9b83cf95f7de"
    assert (b.company, b.location) == ("Thales", "Lille")


@pytest.mark.parametrize("i", [1, 2, 3])
def test_lesjeudis_vrais_mails(i):
    m = load(f"lesjeudis_{i}.eml")
    offers = lesjeudis.parse(m.html)
    assert offers and all(o.title and o.company and o.location for o in offers)
    assert len({o.source_id for o in offers}) == len(offers)


# --- Routage et santé ----------------------------------------------------------------

def test_parser_for_nouveaux_sites():
    assert parser_for("jobalerts-noreply@linkedin.com") is linkedin.parse
    assert parser_for("messages-noreply@linkedin.com") is None      # pas une alerte
    assert parser_for("jobs@makesense.org") is makesense.parse
    assert parser_for("lettre@coordinationsud.org") is coordinationsud.parse
    assert parser_for("emploi@alertes.lesjeudis.com") is lesjeudis.parse


def test_notification_linkedin_ignoree_sans_fausser_la_sante():
    src = EmailAlerts("h", BOX, "p", "INBOX")
    assert src.parse_message(mail("messages-noreply@linkedin.com", "<p>Quelqu’un…</p>")) == []
    assert not src.unknown_senders and not src.sender_stats      # ni « sans parser », ni « vivant »
    assert src.parse_message(mail("jobalerts-noreply@linkedin.com", LI_HTML))
    assert src.sender_stats["linkedin.com"]["last_offers"] == 2


def test_pub_lesjeudis_sans_offre_nest_pas_un_parser_casse():
    src = EmailAlerts("h", BOX, "p", "INBOX")
    src.parse_message(mail("emploi@alertes.lesjeudis.com", "<p>pub</p>",
                           "Plus que quelques minutes pour être visible des recruteurs — LesJeudis"))
    assert "last_offers" not in src.sender_stats["alertes.lesjeudis.com"]
    src.parse_message(mail("emploi@alertes.lesjeudis.com", "<p>vide</p>",
                           "De nouvelles offres pour votre alerte — LesJeudis"))
    assert src.sender_stats["alertes.lesjeudis.com"]["last_offers"] == 0   # là, c'est suspect


def test_liens_publies_propres():
    src = EmailAlerts("h", BOX, "p", "INBOX")
    offers = src.parse_message(mail("jobs@makesense.org", MS_HTML))
    assert [o.url for o in offers] == ["https://jobs.makesense.org/fr/jobs/abcDEF123",
                                      "https://jobs.makesense.org/fr/jobs/zzz999"]
    offers = src.parse_message(mail("lettre@coordinationsud.org", CS_HTML, "Votre alerte emploi Coordination SUD"))
    assert [o.url for o in offers] == ["https://www.coordinationsud.org/?p=111",
                                      "https://www.coordinationsud.org/?p=222"]
