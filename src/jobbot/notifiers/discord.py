"""Envoi d'une offre sur Discord via webhook (message « embed »)."""

import time

import httpx

from jobbot.filters import Verdict
from jobbot.models import Offer
from jobbot.profiles import Profile

LIBELLES_CONTRAT = {"cdi": "CDI", "cdd": "CDD", "stage": "Stage", "alternance": "Alternance",
                    "freelance": "Freelance", "interim": "Intérim"}
COLORS = {"lille": 0xE30613, "paris": 0x1E3A8A}


def found_in(v: Verdict) -> str:
    """Où le mot-clé a été trouvé, lisible : titre / description / annonce complète / alerte."""
    out = []
    for m in v.matched_on:
        kind, _, what = m.partition(":")
        if kind == "fiche":
            out.append(f"📄 annonce complète ({what})")
        elif kind == "alerte":
            out.append(f"🔔 dans l'annonce, d'après l'alerte du site « {what} »")
        else:
            out.append(m)
    return ", ".join(out)


def recap_mark(v: Verdict) -> str:
    """Petit repère dans le récapitulatif quand le titre ne contient pas le mot-clé."""
    kinds = {m.partition(":")[0] for m in v.matched_on}
    return "📄 " if "fiche" in kinds else "🔔 " if "alerte" in kinds else ""


def build_payload(o: Offer, p: Profile, v: Verdict) -> dict:
    fields = [
        {"name": "🏢 Entreprise", "value": (o.company or "—")[:1024], "inline": True},
        {"name": "📍 Lieu", "value": (o.location or o.city_key or "—")[:1024], "inline": True},
    ]
    if contrat := LIBELLES_CONTRAT.get(v.contrat or "") or o.contract:
        fields.append({"name": "📄 Contrat", "value": contrat[:1024], "inline": True})
    if o.salary:
        fields.append({"name": "💰 Salaire", "value": o.salary[:1024], "inline": True})
    if v.score:
        fields.append({"name": "🎯 Pertinence", "value": f"**{v.score}**/100", "inline": True})
    if v.matched_on:
        fields.append({"name": "🔎 Trouvé dans", "value": found_in(v)[:1024], "inline": False})

    embed = {
        "title": f"{'⭐ ' if v.etoile else ''}{'🔥 ' if v.title_match else ''}{o.title}"[:256],
        "url": o.url,
        "color": COLORS.get(o.city_key or "", 0x808080),
        "fields": fields,
        "footer": {"text": f"Profil : {p.nom} · Source : {o.source}"},
    }
    if o.description:
        d = " ".join(o.description.split())
        embed["description"] = d[:300] + ("…" if len(d) > 300 else "")
    return {"username": f"Offres · {p.nom}"[:80], "embeds": [embed]}


RECAP_PAR_MESSAGE = 15  # lignes par embed (la description d'un embed est limitée à 4096 caractères)


def recap_line(o: Offer, v: Verdict) -> str:
    contrat = LIBELLES_CONTRAT.get(v.contrat or "") or o.contract or "?"
    titre = o.title.replace("[", "(").replace("]", ")")[:120]
    return (f"**{v.score}** · {'⭐ ' if v.etoile else ''}{recap_mark(v)}[{titre}]({o.url})\n"
            f"　{(o.company or '?')[:60]} · {(o.location or o.city_key or '?')[:40]} · {contrat}")


def build_recap(items: list[tuple[Offer, Verdict]], p: Profile) -> list[dict]:
    """Récapitulatif : les offres (déjà triées) regroupées par paquets de RECAP_PAR_MESSAGE."""
    payloads, total = [], len(items)
    for start in range(0, total, RECAP_PAR_MESSAGE):
        chunk = items[start:start + RECAP_PAR_MESSAGE]
        part = f" ({start // RECAP_PAR_MESSAGE + 1}/{-(-total // RECAP_PAR_MESSAGE)})" if total > RECAP_PAR_MESSAGE else ""
        embed = {
            "title": f"📋 {total} nouvelles offres{part}"[:256],
            "description": "\n".join(recap_line(o, v) for o, v in chunk)[:4096],
            "color": 0x2B9348,
            "footer": {"text": f"Profil : {p.nom} · triées par pertinence"},
        }
        payloads.append({"username": f"Offres · {p.nom}"[:80], "embeds": [embed]})
    return payloads


def post(webhook_url: str, payload: dict, client: httpx.Client | None = None) -> None:
    """POST d'un message, en respectant la limite de débit de Discord."""
    client = client or httpx.Client(timeout=15)
    for _ in range(5):
        r = client.post(webhook_url, json=payload)
        if r.status_code == 429:  # limite de débit Discord
            time.sleep(float(r.json().get("retry_after", 2)))
            continue
        r.raise_for_status()
        time.sleep(1)  # reste sous ~30 messages/min
        return
    raise RuntimeError("Discord : trop de refus (429)")


def send(webhook_url: str, o: Offer, p: Profile, v: Verdict, client: httpx.Client | None = None) -> None:
    post(webhook_url, build_payload(o, p, v), client)
