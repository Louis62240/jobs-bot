import base64
from urllib.parse import quote

import pytest
from imap_tools import MailMessage

from jobbot import main
from jobbot.config import ROOT
from jobbot.models import Offer
from jobbot.sources.email_alerts import EmailAlerts, hellowork, indeed, publishable
from jobbot.sources.email_alerts.links import contains_mailbox, safe_url, strip_tracking

BOX = "pre.nom.test@gmail.com"


def b64(s: str, urlsafe=True) -> str:
    enc = base64.urlsafe_b64encode if urlsafe else base64.b64encode
    return enc(s.encode()).decode().rstrip("=")


@pytest.mark.parametrize("url", [
    f"https://x.com/o?to={BOX}",                                    # en clair
    f"https://x.com/o?to={quote(BOX)}",                              # %40
    f"https://x.com/o?to={quote(quote(BOX))}",                       # double encodage
    "https://x.com/o?to=prenomtest@gmail.com",                       # sans points (Gmail, Indeed)
    "https://x.com/o?u=PRE.NOM.TEST",                                # partie locale seule, majuscules
    f"https://x.com/clic/{b64(BOX + '|https://site/offre/1')}",      # base64 URL (HelloWork)
    f"https://x.com/c?d={quote(b64('id=9&mail=' + BOX, False))}",    # base64 standard, décalé, %-encodé
])
def test_adresse_detectee_sous_toutes_ses_formes(url):
    assert contains_mailbox(url, BOX)
    assert safe_url(url, BOX) is None


@pytest.mark.parametrize("url", [
    "https://fr.indeed.com/viewjob?jk=abc123",
    "https://www.hellowork.com/fr-fr/emplois/12345.html",
    "https://jobs.makesense.org/fr/jobs/asso-stage-charge-detudes-AbCdEfGhIjKlMnOp1234",
])
def test_liens_normaux_conserves(url):
    assert not contains_mailbox(url, BOX)
    assert safe_url(url, BOX) == url


def test_parametres_de_suivi_retires():
    url = "https://site.fr/offre/42?id=42&utm_source=mail&utm_campaign=x&trk=a&from=ja&ref=b#top"
    assert strip_tracking(url) == "https://site.fr/offre/42?id=42"


def test_lien_non_http_refuse():
    assert safe_url("mailto:rh@site.fr", BOX) is None
    assert safe_url("javascript:alert(1)", BOX) is None


def test_offre_ecartee_si_lien_fuite_sinon_nettoyee():
    fuite = Offer("indeed", "1", "Dev", "A", "Paris", "https://fr.indeed.com/pagead/clk?ad=X&u=prenomtest")
    ok = Offer("indeed", "2", "Dev", "A", "Paris", "https://fr.indeed.com/viewjob?jk=2&utm_source=a")
    kept, dropped = publishable([fuite, ok], BOX)
    assert dropped == 1
    assert [o.url for o in kept] == ["https://fr.indeed.com/viewjob?jk=2"]


def mail(sender: str, html: str, subject="Alerte") -> MailMessage:
    raw = (f"From: {sender}\r\nTo: {BOX}\r\nSubject: {subject}\r\n"
           f"Date: Sun, 15 Nov 2026 08:00:00 +0000\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{html}")
    return MailMessage.from_bytes(raw.encode())


def test_expediteurs_sans_parser_comptes():
    src = EmailAlerts("h", BOX, "p", "INBOX")
    assert src.parse_message(mail("alertes@jobs.makesense.org", "<a href='https://x'>x</a>")) == []
    src.parse_message(mail("Jobs <alertes@jobs.makesense.org>", ""))
    src.parse_message(mail("noreply@lesjeudis.com", ""))
    assert src.unknown_senders == {"jobs.makesense.org": 2, "lesjeudis.com": 1}


def test_lien_sponsorise_indeed_qui_fuit_ecarte_a_la_lecture():
    html = """<table><tr><td>
    <h2><a href="https://fr.indeed.com/pagead/clk/dl?mo=r&ad=XYZ&u=pre.nom.test%40gmail.com">Dev Java</a></h2>
    <p>Initech</p><p>Paris (75)</p><p>il y a 1 jour</p></td></tr></table>"""
    src = EmailAlerts("h", BOX, "p", "INBOX")
    assert indeed.parse(html)                       # le parser la trouve…
    assert src.parse_message(mail("alert@jobalert.indeed.com", html)) == []   # …mais elle n'est pas publiée


def test_dry_run_signale_les_expediteurs_sans_parser(monkeypatch, tmp_path, capsys):
    class Fake:
        name = "email"
        def __init__(self):
            self.unknown_senders = {"jobs.makesense.org": 3}

        def fetch(self):
            return []
    monkeypatch.setattr(main, "build_sources", lambda cfg, env: [Fake()])
    main.run(dry_run=True, profil="stage-asso", db_path=str(tmp_path / "t.db"))
    assert "jobs.makesense.org : 3 mail(s)" in capsys.readouterr().out


# --- Vrais mails (fixtures privées) avec la vraie adresse de la boîte ---------------

def real_mailbox() -> str:
    from dotenv import dotenv_values
    box = (dotenv_values(ROOT / ".env").get("IMAP_USER") or "").strip()
    if not box:
        pytest.skip(".env absent : pas d'adresse de boîte")
    return box


@pytest.mark.parametrize("name,parse", [
    *[(f"hellowork_{i}.eml", hellowork.parse) for i in range(1, 9)],
    ("indeed_1.eml", indeed.parse), ("indeed_2.eml", indeed.parse),
])
def test_vrais_mails_aucun_lien_publie_ne_contient_la_boite(name, parse):
    p = ROOT / "tests" / "fixtures" / name
    if not p.exists():
        pytest.skip(f"fixture privée absente : {name}")
    box = real_mailbox()
    kept, _ = publishable(parse(MailMessage.from_bytes(p.read_bytes()).html), box)
    assert kept
    assert not any(contains_mailbox(o.url, box) for o in kept)
