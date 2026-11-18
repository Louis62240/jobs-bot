from dataclasses import dataclass
from datetime import datetime


@dataclass
class Offer:
    """Format commun à toutes les sources."""

    source: str  # "adzuna", "indeed", "hellowork"…
    source_id: str  # identifiant unique côté source
    title: str
    company: str | None
    location: str
    url: str
    description: str = ""  # vide si la source ne la fournit pas
    published_at: datetime | None = None
    contract: str | None = None
    salary: str | None = None
    city_key: str | None = None  # "lille" / "paris" (rempli par la source ou CityResolver)
