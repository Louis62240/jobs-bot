import pytest

from jobbot.config import ROOT, load
from jobbot.filters import CityResolver
from jobbot.models import Offer
from jobbot.profiles import load as load_profiles


@pytest.fixture(scope="session")
def cfg():
    return load(ROOT / "config.yaml")[0]


@pytest.fixture(scope="session")
def profils(cfg):
    return {p.id: p for p in load_profiles(ROOT / "profiles.yaml", set(cfg["villes"]))}


@pytest.fixture(scope="session")
def cities(cfg):
    return CityResolver(cfg["villes"])


@pytest.fixture
def offer(cities):
    def make(title, location="Lille - 59", contract=None, description="", company="ACME"):
        o = Offer("test", title, title, company, location, "https://x", description, contract=contract)
        o.city_key = cities.city_of(o)
        return o
    return make
