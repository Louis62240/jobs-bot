import pytest

from jobbot import main
from jobbot.filters import evaluate
from jobbot.models import Offer
from jobbot.notifiers import discord
from jobbot.profiles import parse
from jobbot.storage import Store


class FakeSource:
    name = "fake"

    def __init__(self, offers):
        self.offers = offers

    def fetch(self):
        return self.offers


def test_score_explique_et_borne(profils, offer):
    o = offer("Stage chargé d'études RSE - association d'insertion (avril 2027, gratifié)", contract="Stage")
    v = evaluate(profils["stage-asso"], o)
    assert v.ok and 0 <= v.score <= 100
    assert v.score_detail[0] == "base 40"
    assert "+20 mot-clé dans le titre" in v.score_detail
    assert any("associati" in d for d in v.score_detail)        # bonus du profil
    assert v.score == 100                                       # plafonné


def test_offre_plus_ciblee_mieux_notee(profils, offer):
    p = profils["dev"]
    banale = evaluate(p, offer("Développeur PHP", contract="CDI"))
    ciblee = evaluate(p, offer("Développeur Java Angular junior", contract="CDI"))
    assert ciblee.score > banale.score
    assert "+15 ⭐" in ciblee.score_detail


def test_contrat_inconnu_penalise(profils, offer):
    p = profils["dev"]                                         # contrat_inconnu: garder
    avec = evaluate(p, offer("Développeur Python", contract="CDI"))
    sans = evaluate(p, offer("Développeur Python"))
    assert avec.score - sans.score == 10


def test_score_min_rejette_avec_explication(offer):
    [p] = parse({"profils": [{"id": "t", "nom": "T", "villes": ["lille"], "contrats": ["cdi"],
                              "inclure": ["dev"], "webhook": "X", "score_min": 70}]}, {"lille", "paris"})
    v = evaluate(p, offer("dev web", contract="CDI"))
    assert not v.ok and v.raison.startswith("score 60 < 70")


@pytest.mark.parametrize("champ,valeur", [("score_min", 120), ("bonus", {"x": "beaucoup"}),
                                          ("recap_a_partir_de", 0), ("avatar", "http://x.png")])
def test_reglages_invalides_refuses(champ, valeur):
    with pytest.raises(SystemExit, match=champ):
        parse({"profils": [{"id": "t", "nom": "T", "villes": ["lille"], "contrats": ["cdi"],
                            "inclure": ["dev"], "webhook": "X", champ: valeur}]}, {"lille"})


def test_recap_decoupe_et_trie(profils, offer):
    items = [(offer(f"Développeur {i}", contract="CDI"), evaluate(profils["dev"], offer(f"Développeur {i}",
              contract="CDI"))) for i in range(20)]
    messages = discord.build_recap(items, profils["dev"])
    assert [len(chunk) for _, chunk in messages] == [discord.RECAP_PAR_MESSAGE, 5]
    e = messages[0][0]["embeds"][0]
    assert e["title"] == "📋 20 nouvelles offres (1/2)"
    assert e["description"].count("\n-# ") == discord.RECAP_PAR_MESSAGE    # une ligne de détails par offre
    assert len(e["description"]) <= 4096 and "🔥" not in e["description"]
    assert e["footer"]["text"] == "Triées par pertinence"                   # plus le nom du profil


def test_recap_respecte_4096_caracteres(profils, offer):
    offres = [Offer("indeed", str(i), "Développeur " + "très " * 40, "ACME", "Lille - 59",
                    f"https://fr.indeed.com/viewjob?jk={i}&{'x' * 200}", contract="CDI") for i in range(15)]
    for o in offres:
        o.city_key = "lille"
    items = [(o, evaluate(profils["dev"], o)) for o in offres]
    messages = discord.build_recap(items, profils["dev"])
    assert len(messages) > 1 and sum(len(c) for _, c in messages) == 15
    assert all(len(m["embeds"][0]["description"]) <= 4096 for m, _ in messages)


def offres_dev(n):
    return [Offer("hellowork", str(i), f"Développeur Java {i}" if i % 2 else f"Développeur PHP {i}",
                  f"ACME{i}", "Lille - 59", f"https://www.hellowork.com/fr-fr/emplois/{i}.html",
                  contract="CDI") for i in range(n)]


def test_au_dela_du_seuil_un_recap_au_lieu_de_n_messages(monkeypatch, tmp_path):
    cfg, _ = main.load()
    cfg["notifications"] = {"discord": True, "recap_a_partir_de": 5, "max_par_recap": 60}
    recaps = []
    monkeypatch.setattr(main, "load", lambda: (cfg, {"DISCORD_WEBHOOK_DEV": "https://hook"}))
    monkeypatch.setattr(main, "build_sources", lambda c, e: [FakeSource(offres_dev(12))])
    monkeypatch.setattr(discord, "post", lambda url, payload, client=None: recaps.append(payload))
    db = str(tmp_path / "t.db")
    assert main.run(profil="dev", db_path=db) == 12
    assert len(recaps) == 1 and len(recaps[0]["embeds"]) == 1
    lignes = recaps[0]["embeds"][0]["description"].split("\n")
    assert "Java" in lignes[0] and "⭐" in lignes[0]            # les ⭐ (mieux notées) d'abord
    assert Store(db).count("dev") == 12


def test_sous_le_seuil_un_seul_message_groupe(monkeypatch, tmp_path):
    cfg, _ = main.load()
    cfg["notifications"] = {"discord": True, "recap_a_partir_de": 8}
    envois = []
    monkeypatch.setattr(main, "load", lambda: (cfg, {"DISCORD_WEBHOOK_DEV": "https://hook"}))
    monkeypatch.setattr(main, "build_sources", lambda c, e: [FakeSource(offres_dev(7))])
    monkeypatch.setattr(discord, "post", lambda url, payload, client=None: envois.append(payload))
    assert main.run(profil="dev", db_path=str(tmp_path / "t.db")) == 7
    assert len(envois) == 1 and len(envois[0]["embeds"]) == 7      # 7 cartes, un seul message
    couleurs = [e["color"] for e in envois[0]["embeds"]]
    assert couleurs[0] == discord.COULEURS["vert"]                   # Java ⭐ d'abord
    assert couleurs[-1] != discord.COULEURS["vert"]


def test_recap_en_echec_offres_non_enregistrees(monkeypatch, tmp_path):
    cfg, _ = main.load()
    cfg["notifications"] = {"discord": True, "recap_a_partir_de": 5}
    monkeypatch.setattr(main, "load", lambda: (cfg, {"DISCORD_WEBHOOK_DEV": "https://hook"}))
    monkeypatch.setattr(main, "build_sources", lambda c, e: [FakeSource(offres_dev(6))])

    def boom(*a, **k):
        raise RuntimeError("Discord HS")
    monkeypatch.setattr(discord, "post", boom)
    db = str(tmp_path / "t.db")
    assert main.run(profil="dev", db_path=db) == 0
    assert Store(db).count("dev") == 0                          # retentées au prochain passage
