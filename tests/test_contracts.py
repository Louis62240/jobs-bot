import pytest

from jobbot.contracts import detect
from jobbot.models import Offer


def mk(title, contract=None):
    return Offer("t", "1", title, None, "", "", contract=contract)


@pytest.mark.parametrize("title,contract,attendu", [
    ("Data Analyst H/F", "CDI", "cdi"),
    ("Data Analyst H/F", "Indépendant", "freelance"),
    ("Data Platform Intern - Paris H/F", "CDI", "stage"),       # le titre prime
    ("Apprenti Data Engineer H/F", "Alternance", "alternance"),
    ("Alternance Chargé(e) de projets Data & IA (F/H)", None, "alternance"),
    ("Stage - Chargé d'études H/F", None, "stage"),
    ("Data scientist CDD (F/H)", None, "cdd"),
    ("Développeur Java", None, None),
])
def test_detect(title, contract, attendu):
    assert detect(mk(title, contract)) == attendu
