import sqlite3
from datetime import UTC, datetime, timedelta

from imap_tools import MailMessage

from jobbot import health as health_mod
from jobbot import main
from jobbot.health import Health
from jobbot.models import Offer
from jobbot.sources.email_alerts import EmailAlerts

T0 = datetime(2026, 11, 15, 8, 0, tzinfo=UTC)


def h(db, heures=0):
    return Health(db, now=T0 + timedelta(hours=heures))


def test_expediteur_muet_alerte_une_fois_puis_retabli():
    db = sqlite3.connect(":memory:")
    h(db).record_senders({"lesjeudis.com": {"last": T0, "last_offers": None}})
    assert h(db, 47).sender_problems(["lesjeudis.com"], 48) == {}

    later = h(db, 50)
    msgs = later.update(later.sender_problems(["lesjeudis.com"], 48))
    assert len(msgs) == 1 and msgs[0].startswith("⚠️") and "50 h" in msgs[0]
    again = h(db, 60)
    assert again.update(again.sender_problems(["lesjeudis.com"], 48)) == []   # pas de spam

    back = h(db, 61)
    back.record_senders({"lesjeudis.com": {"last": T0 + timedelta(hours=61), "last_offers": None}})
    msgs = back.update(back.sender_problems(["lesjeudis.com"], 48))
    assert len(msgs) == 1 and msgs[0].startswith("✅ **Rétabli**")


def test_expediteur_jamais_vu_compte_a_partir_du_premier_passage():
    db = sqlite3.connect(":memory:")
    assert h(db).sender_problems(["makesense.org"], 48) == {}
    p = h(db, 49).sender_problems(["makesense.org"], 48)
    assert "jamais reçu de mail" in p["muet:makesense.org"]


def test_sous_domaine_compte_pour_le_domaine_attendu():
    db = sqlite3.connect(":memory:")
    h(db).record_senders({"emails.hellowork.com": {"last": T0, "last_offers": 12}})
    assert h(db, 10).sender_problems(["hellowork.com"], 48) == {}


def test_dernier_mail_sans_offre_signale_et_ancien_mail_ignore():
    db = sqlite3.connect(":memory:")
    hh = h(db)
    hh.record_senders({"jobalert.indeed.com": {"last": T0, "last_offers": 0}})
    assert "zero:jobalert.indeed.com" in hh.sender_problems([], 48)
    # un mail plus ancien avec des offres ne masque pas le dernier mail vide…
    hh.record_senders({"jobalert.indeed.com": {"last": T0 - timedelta(days=1), "last_offers": 9}})
    assert "zero:jobalert.indeed.com" in hh.sender_problems([], 48)
    # …mais un mail plus récent avec des offres règle le problème
    hh.record_senders({"jobalert.indeed.com": {"last": T0 + timedelta(hours=1), "last_offers": 9}})
    assert hh.sender_problems([], 48) == {}


def test_lecture_imap_remplit_les_stats():
    def mail(sender, date):
        return MailMessage.from_bytes(
            f"From: {sender}\r\nSubject: x\r\nDate: {date}\r\nContent-Type: text/html\r\n\r\n<p>rien</p>".encode())
    src = EmailAlerts("h", "boite@gmail.com", "p", "INBOX")
    src.parse_message(mail("alert@jobalert.indeed.com", "Sun, 15 Nov 2026 08:00:00 +0000"))
    src.parse_message(mail("alert@jobalert.indeed.com", "Sat, 14 Nov 2026 08:00:00 +0000"))
    src.parse_message(mail("hello@jobs.makesense.org", "Sun, 15 Nov 2026 09:00:00 +0000"))
    st = src.sender_stats
    assert st["jobalert.indeed.com"]["last"].day == 15 and st["jobalert.indeed.com"]["last_offers"] == 0
    assert "last_offers" not in st["jobs.makesense.org"]          # pas de parser : rien à juger


def test_mail_de_confirmation_ne_declenche_pas_zero_offre():
    def mail(subject, date, html="<p>rien</p>"):
        return MailMessage.from_bytes((f"From: alert@jobalert.indeed.com\r\nSubject: {subject}\r\n"
                                       f"Date: {date}\r\nContent-Type: text/html\r\n\r\n{html}").encode())
    src = EmailAlerts("h", "boite@gmail.com", "p", "INBOX")
    src.parse_message(mail("Votre alerte emploi développeur (Paris (75)) est maintenant active",
                           "Sun, 15 Nov 2026 09:49:00 +0000"))
    st = src.sender_stats["jobalert.indeed.com"]
    assert st["last"].hour == 9 and "last_offers" not in st
    db = sqlite3.connect(":memory:")
    hh = h(db)
    hh.record_senders({"jobalert.indeed.com": {"last": T0 - timedelta(days=1), "last_offers": 13}})
    hh.record_senders({"jobalert.indeed.com": st})                # garde les 13 offres connues
    assert hh.sender_problems(["jobalert.indeed.com"], 48) == {}


class StatSource:
    name = "email"

    def __init__(self, stats=None, offers=(), fail=False):
        self.sender_stats, self.offers, self.fail = stats or {}, list(offers), fail

    def fetch(self):
        if self.fail:
            raise ConnectionError("IMAP injoignable")
        return self.offers


def run_full(monkeypatch, tmp_path, source, env=None, webhook_logs="https://logs"):
    cfg, _ = main.load()
    cfg["notifications"] = {"discord": True}
    cfg["sante"] = {"expediteurs": [], "silence_max_heures": 48}
    published = []
    env = {"DISCORD_LOGS_WEBHOOK_URL": webhook_logs, **(env or {})}
    monkeypatch.setattr(main, "load", lambda: (cfg, env))
    monkeypatch.setattr(main, "build_sources", lambda c, e: [source])
    monkeypatch.setattr(main, "publish", lambda msgs, wh: published.append((msgs, wh)))
    main.run(db_path=str(tmp_path / "t.db"))
    return published


def test_passage_complet_signale_source_en_echec_et_webhook_vide(monkeypatch, tmp_path):
    [(msgs, wh)] = run_full(monkeypatch, tmp_path, StatSource(fail=True))
    assert wh == "https://logs"
    assert any("source email en échec : ConnectionError" in m for m in msgs)
    assert any("DISCORD_WEBHOOK_DEV vide" in m for m in msgs)
    # passage suivant : mêmes problèmes → aucun nouveau message
    [(msgs2, _)] = run_full(monkeypatch, tmp_path, StatSource(fail=True))
    assert msgs2 == []


def test_envoi_discord_en_echec_signale(monkeypatch, tmp_path):
    from jobbot.notifiers import discord

    def boom(*a, **k):
        raise RuntimeError("HS")
    monkeypatch.setattr(discord, "send", boom)
    d = Offer("hellowork", "2", "Développeur Java", "ACME", "Lille - 59", "https://b", contract="CDI")
    env = {"DISCORD_WEBHOOK_URL": "a", "DISCORD_WEBHOOK_DEV": "b", "DISCORD_WEBHOOK_STAGE": "c"}
    [(msgs, _)] = run_full(monkeypatch, tmp_path, StatSource(offers=[d]), env=env)
    assert msgs == ["⚠️ **Problème** : profil dev : 1 offre(s) non envoyée(s) sur Discord"]


def test_dry_run_ne_touche_pas_a_la_sante(monkeypatch, tmp_path):
    called = []
    monkeypatch.setattr(main, "build_sources", lambda c, e: [StatSource(fail=True)])
    monkeypatch.setattr(main, "publish", lambda *a: called.append(a))
    main.run(dry_run=True, db_path=str(tmp_path / "t.db"))
    assert called == []


def test_plantage_signale_une_fois(monkeypatch, tmp_path):
    published = []
    monkeypatch.setattr(main, "load", lambda: ({}, {"DISCORD_LOGS_WEBHOOK_URL": "https://logs"}))
    monkeypatch.setattr(main, "publish", lambda msgs, wh: published.append(msgs))
    db = str(tmp_path / "t.db")
    main.report_crash(ValueError("boum"), db_path=db)
    main.report_crash(ValueError("boum"), db_path=db)
    assert published == [["⚠️ **Problème** : le bot a planté : ValueError: boum"], []]


def test_publish_sans_webhook_reste_dans_le_journal(caplog):
    health_mod.publish(["⚠️ **Problème** : x"], "")
    assert "DISCORD_LOGS_WEBHOOK_URL vide" in caplog.text
