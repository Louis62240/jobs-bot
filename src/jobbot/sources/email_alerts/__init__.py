"""Source : alertes e-mail reçues dans la boîte dédiée (lecture IMAP).

On relit les mails des N derniers jours à chaque passage, sans modifier la boîte
(pas de marquage « lu ») : le dédoublonnage est fait par la base SQLite. Ainsi
--dry-run ne touche à rien, et une offre dont l'envoi a échoué (ou qui dépasse
max_par_execution) est reprise au passage suivant.
"""

import logging
import re
from collections import Counter
from datetime import date, timedelta

from imap_tools import AND, MailBox

from jobbot.models import Offer
from jobbot.sources.email_alerts import hellowork, indeed
from jobbot.sources.email_alerts.canonical import canonical
from jobbot.sources.email_alerts.links import safe_url

log = logging.getLogger(__name__)

# Mails de service d'un site d'alertes (confirmation, bienvenue…) : sans offre, et c'est normal.
# Ils prouvent que l'expéditeur est vivant, mais ne comptent pas pour « 0 offre = format changé ».
SERVICE_SUBJECT = re.compile(
    r"est maintenant active|a bien été (créée|enregistrée)|confirm|bienvenue|welcome|"
    r"v[ée]rifie[rz]? votre|activez|mot de passe|password|d[ée]sinscri|unsubscribe",
    re.IGNORECASE,
)

PARSERS = {
    "jobalert.indeed.com": indeed.parse,
    "hellowork.com": hellowork.parse,
}


def parser_for(sender: str):
    domain = sender.rsplit("@", 1)[-1].lower()
    return next((p for d, p in PARSERS.items() if domain == d or domain.endswith("." + d)), None)


def sender_domain(sender: str) -> str:
    return sender.rsplit("@", 1)[-1].lower().strip("<> ")


def publishable(offers: list[Offer], mailbox: str) -> tuple[list[Offer], int]:
    """Nettoie les URL (suivi retiré, forme canonique si le site est reconnu) et écarte
    les offres dont le lien trahit la boîte."""
    kept, dropped = [], 0
    for o in offers:
        url = safe_url(o.url, mailbox)
        if url is None:
            dropped += 1
            continue
        c = canonical(url)
        o.url = c.url if c else url
        kept.append(o)
    return kept, dropped


class EmailAlerts:
    name = "email"

    def __init__(self, host: str, user: str, password: str, folder: str, days: int = 3):
        self.host, self.user, self.password, self.folder = host, user, password, folder
        self.days = days
        # Expéditeurs sans parser vus au dernier passage : domaine → nombre de mails
        self.unknown_senders: Counter[str] = Counter()
        # Pour la santé : domaine → {"last": date du mail le plus récent, "last_offers": offres
        # extraites de ce mail (None si pas de parser)}
        self.sender_stats: dict[str, dict] = {}

    def fetch(self) -> list[Offer]:
        since = date.today() - timedelta(days=self.days)
        offers = []
        self.unknown_senders, self.sender_stats = Counter(), {}
        with MailBox(self.host).login(self.user, self.password, initial_folder=self.folder) as mb:
            for msg in mb.fetch(AND(date_gte=since), mark_seen=False, bulk=True):
                offers += self.parse_message(msg)
        if self.unknown_senders:
            log.info("Expéditeurs sans parser (ignorés) : %s",
                     ", ".join(f"{d} ×{n}" for d, n in self.unknown_senders.most_common()))
        return offers

    def _stat(self, msg, offers: int | None) -> None:
        """Statistiques pour la santé. `offers` None : mail qui ne dit rien sur le parser
        (pas de parser, ou mail de service) → seul « dernier mail reçu » est mis à jour."""
        st = self.sender_stats.setdefault(sender_domain(msg.from_), {"last": msg.date})
        st["last"] = max(st["last"], msg.date)
        if offers is not None and msg.date >= st.get("_alert_date", msg.date):
            st["_alert_date"], st["last_offers"] = msg.date, offers

    def parse_message(self, msg) -> list[Offer]:
        parser = parser_for(msg.from_)
        if parser is None:
            self.unknown_senders[sender_domain(msg.from_)] += 1
            self._stat(msg, None)
            return []
        try:
            got = parser(msg.html or "")
        except Exception:
            log.exception("Mail illisible : %s", msg.subject)
            self._stat(msg, 0)
            return []
        got, dropped = publishable(got, self.user)
        if dropped:
            log.warning("%s : %d offre(s) écartée(s), lien contenant l'adresse de la boîte",
                        sender_domain(msg.from_), dropped)
        self._stat(msg, None if not got and SERVICE_SUBJECT.search(msg.subject or "") else len(got))
        for o in got:
            o.published_at = msg.date
        log.info("%s : %d offres", sender_domain(msg.from_), len(got))
        return got
