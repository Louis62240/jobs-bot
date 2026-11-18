from jobbot import main
from jobbot.models import Offer


class FakeSource:
    name = "fake"

    def __init__(self, offers):
        self.offers = offers

    def fetch(self):
        return self.offers


def test_meme_offre_sur_deux_sites_affichee_une_fois(monkeypatch, tmp_path, capsys):
    a = Offer("indeed", "jk1", "Alternance Data Analyst H/F", "ACME", "Lille (59)", "https://a")
    b = Offer("hellowork", "h1", "Alternance Data Analyst (H/F)", "Acme", "Lille - 59", "https://b")
    monkeypatch.setattr(main, "build_sources", lambda cfg, env: [FakeSource([a, b])])
    assert main.run(dry_run=True, profil="alternance-data", db_path=str(tmp_path / "t.db")) == 1


def test_une_offre_peut_aller_a_deux_profils(monkeypatch, tmp_path):
    o = Offer("hellowork", "1", "Alternance Développeur SQL", "ACME", "Lille - 59", "https://a")
    d = Offer("hellowork", "2", "Développeur Java", "ACME", "Lille - 59", "https://b", contract="CDI")
    monkeypatch.setattr(main, "build_sources", lambda cfg, env: [FakeSource([o, d])])
    db = str(tmp_path / "t.db")
    assert main.run(seed=True, db_path=db) == 2   # o → alternance-data, d → dev
    assert main.run(seed=True, db_path=db) == 0   # déjà vues


def test_profil_sans_webhook_ignore_sans_planter(monkeypatch, tmp_path, caplog):
    cfg, _ = main.load()
    d = Offer("hellowork", "2", "Développeur Java", "ACME", "Lille - 59", "https://b", contract="CDI")
    monkeypatch.setattr(main, "load", lambda: (cfg, {"DISCORD_WEBHOOK_DEV": ""}))
    monkeypatch.setattr(main, "build_sources", lambda cfg, env: [FakeSource([d])])
    assert main.run(profil="dev", db_path=str(tmp_path / "t.db")) == 0
    assert "DISCORD_WEBHOOK_DEV vide" in caplog.text



def test_url_webhook_jamais_dans_les_logs(monkeypatch, tmp_path, caplog):
    import logging

    import httpx
    import respx

    secret = "https://discord.com/api/webhooks/123/SECRET-TOKEN"
    cfg, _ = main.load()
    cfg["notifications"] = {"discord": True}
    o = Offer("indeed", "jk9", "Alternance Data Analyst H/F", "ACME", "Lille (59)", "https://a")
    monkeypatch.setattr(main, "load", lambda: (cfg, {"DISCORD_WEBHOOK_URL": secret}))
    monkeypatch.setattr(main, "build_sources", lambda cfg, env: [FakeSource([o])])
    real_run = main.run
    monkeypatch.setattr(main, "run", lambda **kw: real_run(**kw, db_path=str(tmp_path / "t.db")))
    monkeypatch.setattr("sys.argv", ["jobbot", "--profil", "alternance-data"])
    with respx.mock:
        route = respx.post(secret).mock(return_value=httpx.Response(204))
        with caplog.at_level(logging.DEBUG):
            main.main()
    assert route.called
    assert "SECRET-TOKEN" not in caplog.text
