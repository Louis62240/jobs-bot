from jobbot.filters import Verdict
from jobbot.models import Offer
from jobbot.notifiers.discord import build_payload


def test_payload(profils):
    o = Offer("hellowork", "1", "Développeur Angular", "ACME", "Lille - 59", "https://x",
              description="x" * 500, city_key="lille", contract="CDI")
    v = Verdict(True, matched_on=["titre:d[ée]veloppeu"], etoile=True, contrat="cdi")
    payload = build_payload(o, profils["dev"], v)
    e = payload["embeds"][0]
    assert e["title"].startswith("⭐ 🔥 ")
    assert e["color"] == 0xE30613
    assert len(e["description"]) <= 301
    assert {"name": "📄 Contrat", "value": "CDI", "inline": True} in e["fields"]
    assert "Dev junior" in e["footer"]["text"] and "Dev junior" in payload["username"]
