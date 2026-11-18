import pytest

from jobbot.filters import evaluate

# ---------- villes (communes à tous les profils) ----------

@pytest.mark.parametrize("location,city", [
    ("59 - Lille", "lille"), ("59 - Villeneuve-d'Ascq", "lille"), ("Lille (59)", "lille"),
    ("Marcq-en-Barœul - 59", "lille"), ("75 - Paris 9e Arrondissement", "paris"),
    ("Paris 8e - 75", "paris"), ("92 - Puteaux", "paris"), ("La Défense", "paris"),
])
def test_villes(offer, location, city):
    assert offer("x", location=location).city_key == city


@pytest.mark.parametrize("location", ["69 - Lyon", "Saint-Ouen (93)", "Île-de-France"])
def test_villes_hors_zone(offer, profils, location):
    v = evaluate(profils["dev"], offer("Développeur Java", location=location))
    assert not v.ok and "ville" in v.raison


# ---------- profil 1 : alternance data/SQL ----------

@pytest.mark.parametrize("title,contract", [
    ("Alternance Data Analyst H/F", None),
    ("Apprenti Data Engineer H/F", "Alternance"),
    ("Data Engineer H/F", "Alternance"),
    ("Alternant Développeur SQL", None),
    ("Alternance Ingénieur Dataops", None),
    ("Alternance Analytics Engineer", None),
])
def test_alternance_data_acceptees(offer, profils, title, contract):
    assert evaluate(profils["alternance-data"], offer(title, contract=contract)).ok


@pytest.mark.parametrize("title,contract,raison", [
    ("Data Analyst H/F", "CDI", "contrat cdi"),
    ("Data Analyst H/F", None, "contrat inconnu"),
    ("Alternance Comptable", None, "aucun mot-clé"),
    ("Alternance Database administrator", None, "aucun mot-clé"),
    ("Alternance commercial Data Center", None, "exclu"),
])
def test_alternance_data_refusees(offer, profils, title, contract, raison):
    v = evaluate(profils["alternance-data"], offer(title, contract=contract))
    assert not v.ok and raison in v.raison


@pytest.mark.parametrize("company", [
    "ISCOD", "Digital School of Paris", "Studi", "OpenClassrooms", "My Digital School",
    "École IRIS", "CFA Sup 2000", "stages",
])
def test_alternance_data_ecoles_exclues(offer, profils, company):
    v = evaluate(profils["alternance-data"], offer("Alternance Data Analyst H/F", company=company))
    assert not v.ok and "entreprise exclue" in v.raison


@pytest.mark.parametrize("company", ["Decathlon", "Société Générale", "Leroy Merlin", "Auchan"])
def test_alternance_data_vraies_entreprises_gardees(offer, profils, company):
    assert evaluate(profils["alternance-data"], offer("Alternance Data Analyst H/F", company=company)).ok


def test_mot_cle_dans_description(offer, profils):
    o = offer("Alternance analyste financier", description="Maîtrise de SQL requise")
    v = evaluate(profils["alternance-data"], o)
    assert v.ok and not v.title_match and v.matched_on == ["description:sql"]


# ---------- profil 2 : dev junior ----------

@pytest.mark.parametrize("title,contract,etoile", [
    ("Développeur Angular H/F", "CDI", True),
    ("Développeur·euse Full Stack - Commerce & IA (CDI)", None, False),
    ("Ingénieur Java / Spring Boot", None, True),
    ("Software Engineer Python", "CDD", False),
    ("Développeur JavaScript / React", None, False),   # « javascript » n'est pas « java »
    ("Développeur Front-End Junior", None, False),
])
def test_dev_acceptees(offer, profils, title, contract, etoile):
    v = evaluate(profils["dev"], offer(title, contract=contract))
    assert v.ok and v.etoile is etoile


@pytest.mark.parametrize("title,contract", [
    ("Développeur Senior .NET / Blazor", None),
    ("Lead Developer Java", None),
    ("Architecte logiciel Java", None),
    ("Business Developer H/F", "CDI"),                 # commercial (Les Jeudis)
    ("Développeur Java - 5 ans d'expérience", None),
    ("Développeur Java", "Indépendant"),
    ("Stage Développeur Angular", None),
    ("Alternance Développeur Java", None),
    ("Data Analyst H/F", "CDI"),
])
def test_dev_refusees(offer, profils, title, contract):
    assert not evaluate(profils["dev"], offer(title, contract=contract)).ok


# ---------- profil 3 : stage asso / ESS ----------

@pytest.mark.parametrize("title", [
    "Stage - Chargé·e d'études sociologiques H/F",
    "Stage chargée de mission plaidoyer (4 mois)",
    "Stagiaire Évaluation d'impact social - association",
    "Stage Chargé de projet ESS - avril 2027",
    "Stage enquête qualitative 3 mois gratifié",
    "Stage 2 mois - chargé de mission (gratification légale)",
])
def test_stage_acceptees(offer, profils, title):
    assert evaluate(profils["stage-asso"], offer(title, location="Paris 11e - 75")).ok


@pytest.mark.parametrize("title,raison", [
    ("Stage chargé d'études 6 mois", "exclu"),
    ("Stage chargé de mission - non gratifié", "exclu"),
    ("Stage chargé de mission - 2 mois", "exclu"),           # 2 mois sans gratification
    ("Stage chargé d'études - janvier 2027", "exclu"),
    ("Chargé d'études H/F", "contrat inconnu"),
    ("Stage Développeur Java", "aucun mot-clé"),
])
def test_stage_refusees(offer, profils, title, raison):
    v = evaluate(profils["stage-asso"], offer(title, location="Paris 11e - 75"))
    assert not v.ok and raison in v.raison



@pytest.mark.parametrize("titre", [
    "Stage RSE - 2027",
    "Stage 2027 Chef de projets RSE et transitions durables",
    "Stage - Chargée de projet RSE",
    "Stage Responsabilité sociétale des entreprises",
    "Chargé.e de mission RSO (stage)",
])
def test_stage_asso_rse_retenu_et_mis_en_avant(profils, offer, titre):
    v = evaluate(profils["stage-asso"], offer(titre, location="Paris (75)", contract="Stage"))
    assert v.ok and v.etoile


@pytest.mark.parametrize("titre", ["STAGE - Assistant chef de projet H/F", "Stage - Chargé de projet développement",
                                   "Stage ESG - 2027"])
def test_stage_asso_chef_ou_charge_de_projet_retenu(profils, offer, titre):
    v = evaluate(profils["stage-asso"], offer(titre, location="Paris (75)", contract="Stage"))
    assert v.ok and not v.etoile


def test_rse_pas_confondu_avec_un_autre_mot(profils, offer):
    v = evaluate(profils["stage-asso"], offer("Stage course à pied - responsable des ventes", contract="Stage"))
    assert not v.etoile
