import pytest

from jobbot.profiles import parse

VILLES = {"lille", "paris"}


def base(**kw):
    p = {"id": "x", "nom": "X", "villes": ["lille"], "contrats": ["cdi"], "inclure": ["data"],
         "webhook": "DISCORD_WEBHOOK_X"}
    p.update(kw)
    return {"profils": [p]}


def test_profil_valide():
    [p] = parse(base(), VILLES)
    assert p.contrats == {"cdi"} and p.contrat_inconnu == "garder" and p.actif


def test_vrai_fichier_profils(profils):
    assert set(profils) == {"alternance-data", "dev", "stage-asso"}


@pytest.mark.parametrize("modif,message", [
    ({"villes": ["lyon"]}, "ville"),
    ({"contrats": ["cdi", "job"]}, "contrat"),
    ({"inclure": ["data("]}, "regex invalide"),
    ({"contrat_inconnu": "peut-etre"}, "contrat_inconnu"),
    ({"webhook": ""}, "webhook"),
    ({"motscles": ["x"]}, r"champ\(s\) inconnu"),
])
def test_erreurs_claires(modif, message):
    with pytest.raises(SystemExit, match=message):
        parse(base(**modif), VILLES)


def test_id_en_double():
    d = base()
    d["profils"].append(dict(d["profils"][0]))
    with pytest.raises(SystemExit, match="double"):
        parse(d, VILLES)
