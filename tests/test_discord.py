from datetime import UTC, datetime, timedelta, timezone

import pytest

from jobbot.filters import Verdict, evaluate
from jobbot.models import Offer
from jobbot.notifiers import discord
from jobbot.notifiers.discord import build_messages, build_payload, found_in


def mk(i=1, title="Développeur Angular", score=72, **kw):
    o = Offer(kw.pop("source", "hellowork"), str(i), title, kw.pop("company", "ACME"),
              kw.pop("location", "Lille - 59"), f"https://x/{i}", city_key="lille", **kw)
    v = Verdict(True, matched_on=["titre:d[ée]veloppeu"], matched_text=["Développeur"], etoile=False,
                contrat="cdi", score=score)
    return o, v


def test_carte_une_offre(profils):
    o, v = mk(description="x " * 300, salary="40 k€", published_at=datetime(2026, 11, 18, 8, 30, tzinfo=UTC))
    v.etoile = True
    payload = build_payload(o, profils["dev"], v)
    e = payload["embeds"][0]
    assert e["title"] == "⭐ Développeur Angular" and "🔥" not in e["title"]
    assert e["url"] == "https://x/1"
    assert e["color"] == discord.COULEURS["vert"]
    assert "fields" not in e
    lignes = e["description"].split("\n")
    assert lignes[0] == "🟢 **72**/100"                                     # le score d'abord
    assert lignes[1] == "🏢 ACME · 📍 Lille - 59 · 📄 CDI · 💰 40 k€"
    assert lignes[2].startswith("> ") and len(lignes[2]) <= 2 + discord.EXTRAIT and lignes[2].endswith("…")
    assert lignes[3] == "-# 🔎 *Développeur* dans le titre"
    assert e["footer"]["text"] == "HelloWork"                                # vrai nom, sans le profil
    assert e["timestamp"] == "2026-11-18T08:30:00+00:00"
    assert "Dev junior" in payload["username"]


def test_infos_sautent_ce_qui_manque(profils):
    o, v = mk(company=None, location="", source="linkedin")
    v.contrat = None
    e = build_payload(o, profils["dev"], v)["embeds"][0]
    assert e["description"].split("\n")[1] == "📍 Lille"
    assert "timestamp" not in e and e["footer"]["text"] == "LinkedIn"


@pytest.mark.parametrize("score,couleur,pastille", [(70, "vert", "🟢"), (69, "jaune", "🟡"),
                                                    (50, "jaune", "🟡"), (49, "gris", "⚪")])
def test_couleur_et_pastille_selon_le_score(profils, score, couleur, pastille):
    o, v = mk(score=score)
    e = build_payload(o, profils["dev"], v)["embeds"][0]
    assert e["color"] == discord.COULEURS[couleur]
    assert e["description"].startswith(f"{pastille} **{score}**/100")


def test_variante_barre(profils, monkeypatch):
    monkeypatch.setattr(discord, "VARIANTE_SCORE", "barre")
    o, v = mk(score=72)
    assert build_payload(o, profils["dev"], v)["embeds"][0]["description"].startswith("`▰▰▰▰▰▰▰▱▱▱` **72**")


def test_heure_locale_convertie_en_utc(profils):
    o, v = mk(published_at=datetime(2026, 11, 18, 9, 30, tzinfo=timezone(timedelta(hours=1))))
    assert build_payload(o, profils["dev"], v)["embeds"][0]["timestamp"] == "2026-11-18T08:30:00+00:00"


def test_texte_trouve_au_lieu_des_regex(profils, offer):
    v = evaluate(profils["dev"], offer("Développeur Back-end Java", contract="CDI"))
    assert v.ok and len(v.matched_text) == len(v.matched_on)
    txt = found_in(v)
    assert "*Développeur*" in txt and "dans le titre" in txt
    assert "[" not in txt and "\\b" not in txt                               # plus de regex


def test_mise_en_forme_discord_neutralisee(profils):
    o, v = mk(company="Halian | *Services*", title="Dev [Java]")
    e = build_payload(o, profils["dev"], v)["embeds"][0]
    assert "Halian \\| \\*Services\\*" in e["description"]


def test_regroupement_10_cartes_max_triees_par_score(profils):
    items = [mk(i, score=40 + i) for i in range(23)]
    messages = build_messages(items, profils["dev"])
    assert [len(m["embeds"]) for m, _ in messages] == [10, 10, 3]
    assert sum(len(c) for _, c in messages) == 23
    scores = [v.score for _, c in messages for _, v in c]
    assert scores == sorted(scores, reverse=True)
    assert [len(m["embeds"]) for m, _ in messages] == [len(c) for _, c in messages]


def test_regroupement_respecte_6000_caracteres(profils):
    items = [mk(i, title="Développeur " + "x" * 250, description="mot " * 400,
                company="C" * 60, salary="s" * 60) for i in range(10)]
    messages = build_messages(items, profils["dev"])
    assert len(messages) > 1
    for m, _ in messages:
        assert sum(discord.embed_size(e) for e in m["embeds"]) <= discord.MAX_TOTAL
        assert all(len(e["title"]) <= 256 and len(e["description"]) <= 4096 for e in m["embeds"])


def test_avatar_du_profil(profils):
    from dataclasses import replace
    o, v = mk()
    sans = replace(profils["dev"], avatar="")
    assert "avatar_url" not in build_payload(o, sans, v)                      # pas réglé : avatar du webhook
    p = replace(profils["dev"], avatar="https://louishanquiez.fr/jobbot/dev.png")
    assert build_payload(o, p, v)["avatar_url"] == "https://louishanquiez.fr/jobbot/dev.png"
    assert discord.build_recap([(o, v)], p)[0][0]["avatar_url"] == p.avatar
