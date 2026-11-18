"""Profil stage-asso vérifié sur les stages réels du diaporama de la majeure (promos 2016-2024).
Elle ne veut ni le monde du conseil / de l'expertise / de l'étude, ni la finance responsable."""

import pytest

from jobbot.filters import evaluate

GARDER=[("Stage - Chargée de mission RSE","Chronopost"),("Stage RSE / environnement","Vinci Construction"),
 ("Stage - Animation de la démarche RSE","MGEN"),("Stage Chargé(e) d'études RH RSE","ORSE"),
 ("Stage - Assistant(e) chargé(e) de RSE","Société Générale"),("Stage Gestion des partenariats - engagement solidaire","Chanel"),
 ("Stage Assistant relations sociales, diversité et inclusion","BNP Paribas Factor"),("Stage Chargée de mission développement durable","Suez Organique"),
 ("Stage - Animatrice du réseau national des incubateurs greentech","Ministère de la Transition écologique"),
 ("Stage collaboratrice parlementaire","Assemblée nationale"),("Stage Chargée de mission économie circulaire","Les Canaux"),
 ("Stagiaire Inclusion, Diversité et Engagement collaborateur","Kering"),("Stage - Chargée de projet vacances enfants","Secours populaire"),
 ("Stage - Animation du Dispositif Local d'Accompagnement","CRESS Île-de-France"),("Stage assistante mécénat et animation","Bouge ton Coq"),
 ("Stage Santé Sécurité au travail","SANEF"),("Stage Mission Handicap - QVCT","Orange"),("Stage chargé(e) de partenariats privés","Adie"),
 ("Stage - Chargée de mission Diversité & Inclusion","Transdev"),("Stage chargé(e) de développement RSE","Pharea")]
REJETER=[("Stage consultant junior développement durable","Deloitte Conseil"),("Stage Analyste ESG","Sagard"),
 ("Stage analyste ISR/ESG","Axylia"),("Stage - Politique de vote et ISR","Ecofi"),("Stage analyste gouvernance","LBPAM"),
 ("Stage consultante en évaluation des politiques publiques","Pluricité"),("Stage - Expertise CSE et SSCT","Syndex"),
 ("Stage - Consultant diagnostic économique, social et stratégique","Secafi"),("Stage - ESG en Private Equity","Société Générale"),
 ("Stage - Assistant chargé d'études quali et quanti","Verian"),("Stage - Assistant.e Chargé.e d'Etudes, Département Opinion","Groupe Ifop"),
 ("Stage - Assistance au chargé de financements structurés durables","Société Générale"),("Stage chargé de mission ESG - immobilier durable","Sofidy"),
 ("Stage Sustainability Strategist","Fabernovel"),("Stage Consultante Politiques publiques - Emploi-Formation","KYU Associés")]


@pytest.mark.parametrize("titre,entreprise", GARDER)
def test_missions_du_diaporama_retenues(profils, offer, titre, entreprise):
    v = evaluate(profils["stage-asso"], offer(titre, location="Paris (75)", contract="Stage", company=entreprise))
    assert v.ok, v.raison


@pytest.mark.parametrize("titre,entreprise", REJETER)
def test_conseil_etudes_et_finance_responsable_rejetes(profils, offer, titre, entreprise):
    v = evaluate(profils["stage-asso"], offer(titre, location="Paris (75)", contract="Stage", company=entreprise))
    assert not v.ok


def test_audit_rse_reste_possible(profils, offer):
    v = evaluate(profils["stage-asso"], offer("Stage - participer aux audits RSE des chantiers", location="Paris (75)",
                                              contract="Stage", company="Vinci"))
    assert v.ok and v.etoile


def test_fondation_d_un_cabinet_de_conseil_rejetee(profils, offer):
    """Décision du 2026-11-15 : pas de cabinet de conseil, même pour sa fondation (mécénat)."""
    v = evaluate(profils["stage-asso"], offer("Stage Fondation Pôle Innovation sociale F/H", location="La Défense",
                                              contract="Stage", company="Deloitte"))
    assert not v.ok and "entreprise exclue" in v.raison


@pytest.mark.parametrize("titre", ["Operations & Team Coordination Volunteer | Remote",
                                   "Chargé·e de mission Démocratie participative (Service Civique)"])
def test_benevolat_et_service_civique_ne_sont_pas_des_stages(profils, offer, titre):
    v = evaluate(profils["stage-asso"], offer(titre, location="Paris (75)", contract="Stage", company="Asso"))
    assert not v.ok


@pytest.mark.parametrize("titre", ["Chargé de Missions Durabilité H/F", "Assistant chef de projet développement durable",
                                   "Stage - Sustainability Reporting & Projects"])
def test_durabilite_mise_en_avant_comme_rse(profils, offer, titre):
    v = evaluate(profils["stage-asso"], offer(titre, location="Paris (75)", contract="Stage", company="Groupama"))
    assert v.ok and v.etoile
