# 🤖 Bot d'alertes emploi « Data / SQL » : Lille et Paris

> **Objectif** : recevoir **chaque nouvelle offre d'emploi** publiée à **Lille** ou **Paris** qui contient **« data »** ou **« SQL »** dans l'intitulé **ou** dans la fiche de poste, avec une notification **Discord** (et/ou **ntfy** sur le téléphone).
> Pas de doublons, pas de spam, pas d'offre ratée, et un fonctionnement autonome 24h/24.

---

> 🔀 **2026-11-15 : passage au multi-profils.** Le bot sert désormais 3 profils (un salon Discord chacun). Ce qui change par rapport à la suite du document :
> - `profiles.yaml` (nouveau) porte, par profil : contrats, villes, `inclure` / `exclure` / `etoile` (regex), `contrat_inconnu`, nom de la variable du webhook. `config.yaml` ne garde que les villes, les sources et les réglages globaux (la section `mots_cles` a disparu).
> - Pipeline : collecte **une fois** → `CityResolver` (ville) → pour chaque profil `filters.evaluate()` (ville → contrat via `contracts.detect` → exclusions → mots-clés → ⭐) → `Store.is_new(profil, offre)` → Discord du profil.
> - SQLite : clé `(profile, source, source_id)` + empreinte par profil ; migration automatique v0 → v1 (`PRAGMA user_version`).
> - Source principale : alertes e-mail (France Travail retiré, Adzuna non branché).

## Sommaire

1. [Vue d'ensemble et architecture](#1-vue-densemble-et-architecture)
2. [Les sources d'offres : ce qui est faisable proprement](#2-les-sources-doffres--ce-qui-est-faisable-proprement)
3. [Étape 0 : Créer les comptes (boîte mail dédiée, API, Discord, ntfy)](#3-étape-0--créer-les-comptes)
4. [Étape 1 : Structure du projet](#4-étape-1--structure-du-projet)
5. [Étape 2 : Configuration (.env + config.yaml)](#5-étape-2--configuration)
6. [Étape 3 : Les collecteurs](#6-étape-3--les-collecteurs)
7. [Étape 4 : Le filtre « data / SQL »](#7-étape-4--le-filtre-data--sql)
8. [Étape 5 : Dédoublonnage (SQLite)](#8-étape-5--dédoublonnage-sqlite)
9. [Étape 6 : Notifications Discord et ntfy](#9-étape-6--notifications-discord--ntfy)
10. [Étape 7 : Orchestration et planification](#10-étape-7--orchestration--planification)
11. [Étape 8 : Hébergement](#11-étape-8--hébergement)
12. [Étape 9 : Supervision, logs et robustesse](#12-étape-9--supervision-logs-robustesse)
13. [Étape 10 : Tests](#13-étape-10--tests)
14. [Sécurité, légalité et CGU](#14-sécurité-légalité-cgu)
15. [Améliorations possibles](#15-roadmap--améliorations)
16. [Checklist finale](#16-checklist-finale)

---

## 1. Vue d'ensemble et architecture

```
                ┌──────────────────────────── SOURCES ────────────────────────────┐
                │                                                                  │
   API France Travail ──┐                                                          │
   API Adzuna ──────────┤                                                          │
   (autres API…) ───────┤                                                          │
                        │                                                          │
   Alertes e-mail ──────┤  LinkedIn / Indeed / WTTJ / APEC / HelloWork…            │
   (boîte mail dédiée,  │  envoient leurs alertes dans la boîte → lue en IMAP      │
    lue en IMAP)        │                                                          │
                └───────┼──────────────────────────────────────────────────────────┘
                        ▼
              ┌───────────────────┐
              │  1. COLLECTE      │  chaque source → format commun `Offer`
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │  2. FILTRE        │  ville ∈ {Lille, Paris} ET regex data|sql
              └─────────┬─────────┘     (titre = priorité haute, description = normale)
                        ▼
              ┌───────────────────┐
              │  3. DÉDOUBLONNAGE │  SQLite : id source + empreinte (titre+entreprise+ville)
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │  4. NOTIFICATION  │──► Discord (webhook, embed joli)
              └───────────────────┘──► ntfy (push téléphone)
                        ▲
              cron / systemd timer / GitHub Actions toutes les 15 min
```

**Choix techniques recommandés**

| Élément        | Choix                                   | Pourquoi                                         |
|----------------|-----------------------------------------|--------------------------------------------------|
| Langage        | **Python 3.12+**                        | Simple, plein de libs HTTP/IMAP/HTML             |
| Gestion deps   | **uv** (ou pip + venv)                  | Rapide, reproductible (`uv.lock`)                |
| HTTP           | `httpx`                                 | Timeouts et retries propres                      |
| IMAP           | `imap-tools`                            | Bien plus simple que `imaplib` brut              |
| Parsing HTML   | `beautifulsoup4` + `lxml`               | Pour lire les mails d'alerte                     |
| Stockage       | **SQLite** (fichier unique)             | Zéro serveur, parfait pour du dédoublonnage      |
| Config         | `.env` (secrets) + `config.yaml` (règles)| Séparer secrets et paramètres                    |
| Planification  | **systemd timer** ou cron               | Fiable, relance auto, logs dans journald         |
| Notifications  | Webhook **Discord** + **ntfy**          | Aucun bot Discord à coder, 1 requête HTTP chacun |

---

## 2. Les sources d'offres : ce qui est faisable proprement

> ⚠️ **Règle d'or** : on privilégie les **API officielles** et les **alertes e-mail** que les sites envoient eux-mêmes.
> On **ne scrape pas** LinkedIn ni Indeed : leurs CGU l'interdisent, ils bloquent vite, et le code casse à chaque changement de leur site.
> C'est justement pour ça qu'une **boîte mail dédiée** est une très bonne idée : elle permet de récupérer LinkedIn, Indeed, etc. **légalement**, via leurs propres alertes.

| Source                     | Méthode                    | Gratuit | Description complète ?            | Fiabilité | Priorité |
|----------------------------|----------------------------|---------|-----------------------------------|-----------|----------|
| **France Travail** (ex-Pôle emploi) | API officielle « Offres d'emploi v2 » | ✅ | ✅ Oui                  | ⭐⭐⭐⭐⭐     | **P1**   |
| **Adzuna** (agrégateur)    | API officielle             | ✅ (quota) | 🟡 Extrait (~500 caractères)   | ⭐⭐⭐⭐      | **P1**   |
| **LinkedIn**               | Alerte e-mail → IMAP       | ✅      | ❌ Titre / entreprise / ville      | ⭐⭐⭐⭐      | **P1**   |
| **Indeed**                 | Alerte e-mail → IMAP       | ✅      | 🟡 Titre + court extrait          | ⭐⭐⭐⭐      | **P1**   |
| **Welcome to the Jungle**  | Alerte e-mail → IMAP       | ✅      | ❌ Titre / entreprise             | ⭐⭐⭐       | P2       |
| **APEC** (cadres)          | Alerte e-mail → IMAP       | ✅      | 🟡                                | ⭐⭐⭐       | P2       |
| **HelloWork**              | Alerte e-mail → IMAP       | ✅      | 🟡 Titre / entreprise / ville     | ⭐⭐⭐⭐      | **P1**   |
| **Cadremploi**             | Alerte e-mail → IMAP       | ✅      | 🟡                                | ⭐⭐⭐       | P2       |
| **Free-Work** (spécialisé IT/data) | Alerte e-mail → IMAP | ✅    | 🟡                                | ⭐⭐⭐⭐      | P2       |
| **LesJeudis** (IT)         | Alerte e-mail → IMAP       | ✅      | 🟡                                | ⭐⭐⭐       | P2       |
| **Glassdoor**              | Alerte e-mail → IMAP       | ✅      | ❌                                | ⭐⭐⭐       | P3       |
| **Meteojob / Monster**     | Alerte e-mail → IMAP       | ✅      | ❌                                | ⭐⭐⭐       | P3       |
| **Jobteaser** (étudiants / alternance) | Alerte e-mail → IMAP | ✅  | ❌                                | ⭐⭐⭐       | P3 (si alternance/stage) |
| **Pages carrières d'entreprises ciblées** | API publiques des outils de recrutement (Greenhouse, Lever, Workable, Teamtailor…) | ✅ | ✅ Oui | ⭐⭐⭐⭐⭐ | Bonus |

**Pourquoi pas d'API pour HelloWork, Cadremploi, etc. ?** Ces sites n'ont pas d'API publique, mais **tous** envoient des alertes e-mail. La boîte dédiée les centralise toutes. Ajouter un site revient donc à **créer une alerte** dessus, sans écrire de nouveau code (voir le parser générique, § 6.4).

**Pages carrières d'entreprises** : beaucoup d'entreprises (scale-ups, ESN, grands groupes de la métropole lilloise) publient leurs offres via un outil de recrutement qui a une URL JSON publique, par exemple :
- Greenhouse : `https://boards-api.greenhouse.io/v1/boards/<entreprise>/jobs?content=true`
- Lever : `https://api.lever.co/v0/postings/<entreprise>?mode=json`

On peut y ajouter une liste d'entreprises cibles dans `config.yaml`. Leurs offres arrivent souvent **avant** d'apparaître sur les sites d'annonces.

**Astuce clé pour les alertes e-mail** : sur chaque site, on crée l'alerte **déjà filtrée** (mots-clés `data` et `SQL`, villes Lille + Paris, fréquence « immédiate » ou « quotidienne »). Le bot n'a plus qu'à lire le mail, extraire les offres, dédoublonner et notifier.
Pour les sources sans description complète, le filtre porte sur le **titre**, mais comme l'alerte a déjà été filtrée par le site sur « SQL »/« data » (y compris dans la description), on ne perd rien.

---

## 3. Étape 0 : Créer les comptes

### 3.1 Boîte mail dédiée (Gmail conseillé)

1. Créer un compte, par ex. `alertes.data.<nom>@gmail.com`.
2. **Activer la validation en 2 étapes** (obligatoire pour l'étape suivante).
3. Créer un **mot de passe d'application** : *Compte Google → Sécurité → Mots de passe des applications*. On obtient 16 caractères : c'est ce mot de passe que le bot utilisera (jamais le vrai mot de passe).
4. Vérifier que l'**IMAP est activé** (*Paramètres Gmail → Transfert et POP/IMAP*).
5. Créer un **libellé** `jobs` et un **filtre Gmail** qui y range automatiquement les mails venant de :
   - `jobalerts-noreply@linkedin.com`
   - `alert@indeed.com` / `*@indeed.com`
   - `*@welcometothejungle.com`
   - `*@apec.fr`, `*@hellowork.com`…
   → Le bot ne lira **que** ce libellé : propre et sans risque de traiter autre chose.

> Alternative : **Proton Mail** (nécessite Proton Bridge pour l'IMAP) ou une adresse sur un domaine perso. Gmail reste le plus simple.

### 3.2 Créer les alertes sur chaque site (avec la boîte dédiée)

| Site     | Alerte à créer                                                                 |
|----------|---------------------------------------------------------------------------------|
| LinkedIn | Recherche `data OR SQL`, lieu *Lille* → « Créer une alerte » (quotidienne). Idem pour *Paris*. |
| Indeed   | `data OR sql`, *Lille (59)* puis *Paris (75)* → « Recevoir les nouvelles offres par e-mail ». |
| WTTJ     | Recherche « data », Lille + Paris → activer l'alerte.                           |
| APEC     | Recherche « data » et « SQL », Hauts-de-France / Île-de-France → alerte.        |
| HelloWork | Recherche « data » puis « SQL », *Lille* et *Paris* → « Créer une alerte » (fréquence la plus rapide proposée). |
| Cadremploi | « data » / « SQL », Lille + Paris → alerte.                                  |
| Free-Work | « data » / « SQL », filtre CDI (et freelance si besoin), Lille + Paris → alerte. |
| LesJeudis, Glassdoor, Meteojob, Monster | Même principe : mots-clés data / SQL, Lille + Paris. |

💡 Commencer par **LinkedIn, Indeed, HelloWork, WTTJ et APEC** : ensemble ils couvrent l'essentiel du marché. Ajouter les autres ensuite si besoin. Au-delà, on reçoit surtout des doublons, que le bot supprime de toute façon.

👉 Faire un compte LinkedIn **avec la boîte dédiée** (ou ajouter la boîte dédiée comme e-mail secondaire et y envoyer les alertes).

### 3.3 API France Travail (gratuit)

> ⛔ **Retiré le 2026-11-15** : inutile, France Travail n'est plus une source.

1. Aller sur **https://francetravail.io** → créer un compte.
2. *Mon espace → Créer une application*.
3. Abonner l'application à l'API **« Offres d'emploi v2 »**.
4. Récupérer le **client_id** et le **client_secret**.

### 3.4 API Adzuna (gratuit)

1. **https://developer.adzuna.com** → *Register*.
2. Récupérer **app_id** et **app_key**. (Quota gratuit largement suffisant pour une requête toutes les 15 à 30 min.)

### 3.5 Discord

1. Créer un serveur (ou utiliser un existant) → créer un salon `#offres-data`.
2. *Paramètres du salon → Intégrations → Webhooks → Nouveau webhook* → **Copier l'URL**.
3. (Optionnel) Deux salons : `#offres-lille` et `#offres-paris`, chacun avec son webhook.

> ⚠️ L'URL du webhook est un **secret** : quiconque l'a peut poster dans le salon.

### 3.6 ntfy (notifications push sur téléphone, optionnel)

1. Installer l'app **ntfy** (Android / iOS).
2. Choisir un **nom de topic long et aléatoire** (les topics de ntfy.sh sont publics !) :
   ```bash
   python3 -c "import secrets; print('jobs-data-' + secrets.token_urlsafe(12))"
   ```
3. S'abonner à ce topic dans l'app.
4. (Option avancée) auto-héberger ntfy ou créer un compte ntfy.sh avec **token d'accès** pour un topic privé.

---

## 4. Étape 1 : Structure du projet

```
bot-offres-data/
├── PLAN.md                  ← ce document
├── README.md
├── pyproject.toml
├── .env.example             ← modèle (commité)
├── .env                     ← secrets (JAMAIS commité)
├── .gitignore
├── config.yaml              ← villes, mots-clés, exclusions, sources actives
├── data/
│   └── jobs.db              ← SQLite (créée automatiquement, non commitée)
├── src/jobbot/
│   ├── __init__.py
│   ├── main.py              ← point d'entrée : collecte → filtre → dédup → notif
│   ├── models.py            ← dataclass Offer
│   ├── config.py            ← chargement .env + YAML
│   ├── filters.py           ← regex data/sql + filtre ville
│   ├── storage.py           ← SQLite (déjà vu ?)
│   ├── notifiers/
│   │   ├── discord.py
│   │   └── ntfy.py
│   └── sources/
│       ├── base.py          ← interface commune
│       ├── francetravail.py
│       ├── adzuna.py
│       └── email_alerts/
│           ├── imap_reader.py
│           ├── linkedin.py
│           ├── indeed.py
│           └── wttj.py
├── tests/
│   ├── fixtures/            ← exemples de mails / réponses API anonymisés
│   ├── test_filters.py
│   ├── test_storage.py
│   └── test_parsers.py
└── deploy/
    ├── jobbot.service
    └── jobbot.timer
```

**Initialisation :**

```bash
mkdir bot-offres-data && cd bot-offres-data
git init
uv init --package --name jobbot
uv add httpx python-dotenv pyyaml imap-tools beautifulsoup4 lxml
uv add --dev pytest respx ruff
```

`.gitignore` minimal :

```gitignore
.env
data/
__pycache__/
.venv/
*.log
```

---

## 5. Étape 2 : Configuration

### `.env.example` (les vraies valeurs vont dans `.env`)

```dotenv
# France Travail
FT_CLIENT_ID=
FT_CLIENT_SECRET=

# Adzuna
ADZUNA_APP_ID=
ADZUNA_APP_KEY=

# Boîte mail dédiée
IMAP_HOST=imap.gmail.com
IMAP_USER=alertes.data.xxx@gmail.com
IMAP_PASSWORD=xxxx xxxx xxxx xxxx     # mot de passe d'application
IMAP_FOLDER=jobs

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# ntfy (optionnel)
NTFY_URL=https://ntfy.sh
NTFY_TOPIC=jobs-data-xxxxxxxxxxxx
NTFY_TOKEN=
```

### `config.yaml` (règles métier, modifiables sans toucher au code)

```yaml
villes:
  lille:
    libelle: "Lille"
    france_travail: { commune: "59350", distance_km: 15 }   # code INSEE Lille + rayon (métropole)
    adzuna_where: "Lille"
    alias: ["lille", "villeneuve-d'ascq", "roubaix", "tourcoing", "marcq-en-baroeul", "lambersart", "euralille"]
  paris:
    libelle: "Paris"
    france_travail: { departement: "75" }                   # tout Paris intra-muros
    adzuna_where: "Paris"
    alias: ["paris", "la défense", "la defense", "puteaux", "courbevoie", "boulogne-billancourt", "issy-les-moulineaux"]

mots_cles:
  # regex insensibles à la casse
  inclure:
    - '\bdata\b'          # data, Data Analyst, Big Data…
    - 'data[- ]?(viz|visuali[sz]ation)'
    - 'sql'               # SQL, MySQL, PostgreSQL, NoSQL, T-SQL, PL/SQL
  exclure:                # optionnel : pour réduire le bruit
    - 'data ?center technicien'
    # - '\bstage\b'
    # - '\balternance\b'

sources:
  france_travail: true
  adzuna: true
  email_alerts: true

notifications:
  discord: true
  ntfy: true
  max_par_execution: 30     # garde-fou anti-spam
```

---

## 6. Étape 3 : Les collecteurs

### 6.1 Modèle commun

```python
# src/jobbot/models.py
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Offer:
    source: str                 # "francetravail", "adzuna", "linkedin"…
    source_id: str              # identifiant unique côté source
    title: str
    company: str | None
    location: str
    url: str
    description: str = ""       # vide si la source ne la fournit pas
    published_at: datetime | None = None
    contract: str | None = None # CDI, CDD, stage…
    salary: str | None = None
    matched_on: list[str] = field(default_factory=list)  # rempli par le filtre
    city_key: str | None = None                          # "lille" / "paris"
```

Chaque source implémente simplement : `def fetch(self) -> list[Offer]`.

### 6.2 France Travail (source principale, description complète)

> ⛔ **Retiré le 2026-11-15** : France Travail n'est plus une source du bot (code et config supprimés). Section conservée pour mémoire.

**Authentification** (OAuth2 *client credentials*, token valable ~25 min, à mettre en cache) :

```python
# src/jobbot/sources/francetravail.py
import httpx, time

TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"

class FranceTravail:
    def __init__(self, client_id, client_secret, villes):
        self.cid, self.secret, self.villes = client_id, client_secret, villes
        self._token, self._exp = None, 0

    def _get_token(self):
        if self._token and time.time() < self._exp - 60:
            return self._token
        r = httpx.post(TOKEN_URL, data={
            "grant_type": "client_credentials",
            "client_id": self.cid,
            "client_secret": self.secret,
            "scope": "api_offresdemploiv2 o2dsoffre",
        }, timeout=20)
        r.raise_for_status()
        j = r.json()
        self._token, self._exp = j["access_token"], time.time() + j["expires_in"]
        return self._token

    def fetch(self):
        offers = []
        headers = {"Authorization": f"Bearer {self._get_token()}"}
        for key, ville in self.villes.items():
            for mot in ("data", "sql"):
                params = {
                    "motsCles": mot,
                    "publieeDepuis": 1,       # offres publiées depuis 1 jour
                    "range": "0-149",         # max 150 par page
                    **ville["france_travail"],
                }
                if "distance_km" in params:
                    params["distance"] = params.pop("distance_km")
                r = httpx.get(SEARCH_URL, params=params, headers=headers, timeout=30)
                if r.status_code == 204:      # aucun résultat
                    continue
                r.raise_for_status()          # 200 ou 206 (contenu partiel = pagination)
                for o in r.json().get("resultats", []):
                    offers.append(self._to_offer(o, key))
                # TODO : si 206 → paginer avec range=150-299, etc.
        return offers

    def _to_offer(self, o, city_key):
        from jobbot.models import Offer
        return Offer(
            source="francetravail",
            source_id=o["id"],
            title=o.get("intitule", ""),
            company=(o.get("entreprise") or {}).get("nom"),
            location=(o.get("lieuTravail") or {}).get("libelle", ""),
            url=(o.get("origineOffre") or {}).get("urlOrigine")
                or f"https://candidat.francetravail.fr/offres/recherche/detail/{o['id']}",
            description=o.get("description", ""),
            contract=o.get("typeContratLibelle"),
            salary=(o.get("salaire") or {}).get("libelle"),
            city_key=city_key,
        )
```

> 📌 Vérifier les noms exacts des paramètres dans la doc officielle sur francetravail.io (onglet *Documentation* de l'API Offres d'emploi v2). Les principaux : `motsCles`, `commune`, `distance`, `departement`, `publieeDepuis`, `range`, `minCreationDate`/`maxCreationDate`.

### 6.3 Adzuna

```python
# src/jobbot/sources/adzuna.py
import httpx
from jobbot.models import Offer

URL = "https://api.adzuna.com/v1/api/jobs/fr/search/{page}"

class Adzuna:
    def __init__(self, app_id, app_key, villes):
        self.id, self.key, self.villes = app_id, app_key, villes

    def fetch(self):
        offers = []
        for key, ville in self.villes.items():
            r = httpx.get(URL.format(page=1), params={
                "app_id": self.id, "app_key": self.key,
                "what_or": "data sql",          # data OU sql
                "where": ville["adzuna_where"],
                "distance": 15,
                "max_days_old": 1,
                "results_per_page": 50,
                "sort_by": "date",
            }, timeout=30)
            r.raise_for_status()
            for o in r.json().get("results", []):
                offers.append(Offer(
                    source="adzuna",
                    source_id=str(o["id"]),
                    title=o.get("title", ""),
                    company=(o.get("company") or {}).get("display_name"),
                    location=(o.get("location") or {}).get("display_name", ""),
                    url=o["redirect_url"],
                    description=o.get("description", ""),   # extrait tronqué
                    city_key=key,
                ))
        return offers
```

### 6.4 Alertes e-mail (LinkedIn, Indeed, WTTJ…)

**Lecture IMAP** : on ne lit que les mails **non lus** du libellé `jobs`, puis on les marque comme lus.

> ✏️ **Implémenté autrement (2026-11-15)** : le bot relit les mails des `email_alerts.jours` derniers jours (config.yaml) **sans les marquer lus** ; c'est la base SQLite qui écarte les doublons. Avantages : `--dry-run` ne modifie rien, et une offre non envoyée (échec Discord ou dépassement de `max_par_execution`) est reprise au passage suivant au lieu d'être perdue. Les liens HelloWork sont décodés pour publier l'URL réelle de l'offre (le lien de suivi contient l'adresse de la boîte).

```python
# src/jobbot/sources/email_alerts/imap_reader.py
from imap_tools import MailBox, AND
from . import linkedin, indeed, wttj

PARSERS = {
    "linkedin.com": linkedin.parse,
    "indeed.com": indeed.parse,
    "welcometothejungle.com": wttj.parse,
}

def fetch(host, user, password, folder):
    offers = []
    with MailBox(host).login(user, password, initial_folder=folder) as mb:
        for msg in mb.fetch(AND(seen=False), mark_seen=False):
            parser = next((p for dom, p in PARSERS.items() if dom in msg.from_), None)
            if parser is None:
                continue
            try:
                offers.extend(parser(msg.html or msg.text))
                mb.flag(msg.uid, "\\Seen", True)   # marqué lu SEULEMENT si parsing OK
            except Exception:
                # on laisse non lu → retenté au prochain passage + log d'erreur
                raise
    return offers
```

**Exemple de parser (principe, à adapter au HTML réel des mails)** :

```python
# src/jobbot/sources/email_alerts/linkedin.py
import re
from bs4 import BeautifulSoup
from jobbot.models import Offer

JOB_ID = re.compile(r"/jobs/view/(\d+)")

def parse(html: str) -> list[Offer]:
    soup = BeautifulSoup(html, "lxml")
    offers, seen = [], set()
    for a in soup.find_all("a", href=JOB_ID):
        job_id = JOB_ID.search(a["href"]).group(1)
        if job_id in seen:
            continue
        seen.add(job_id)
        bloc = a.find_parent("table") or a
        lignes = [t.strip() for t in bloc.stripped_strings]
        offers.append(Offer(
            source="linkedin",
            source_id=job_id,
            title=lignes[0] if lignes else "",
            company=lignes[1] if len(lignes) > 1 else None,
            location=lignes[2] if len(lignes) > 2 else "",
            url=f"https://www.linkedin.com/jobs/view/{job_id}/",   # URL propre, sans tracking
        ))
    return offers
```

**Parser générique (pour couvrir « tous les sites » sans coder un parser par site)** :
si aucun parser dédié ne correspond à l'expéditeur, on prend tous les liens du mail dont le texte ressemble à un intitulé de poste. On les passe dans le filtre data/SQL. L'URL nettoyée de ses paramètres de suivi sert d'identifiant. C'est moins précis qu'un parser dédié : l'entreprise et la ville peuvent manquer. En revanche, **n'importe quel nouveau site d'alertes marche tout de suite**. On n'écrit un parser dédié que pour les sources qui envoient beaucoup d'offres (LinkedIn, Indeed, HelloWork).

```python
PARSERS = {
    "linkedin.com": linkedin.parse,
    "indeed.com": indeed.parse,
    "hellowork.com": hellowork.parse,
    "welcometothejungle.com": wttj.parse,
}
parser = next((p for dom, p in PARSERS.items() if dom in msg.from_), generic.parse)
```

> 🛠️ **Méthode de travail pour les parsers** : attendre de recevoir 2–3 vrais mails d'alerte, les **enregistrer en `.eml`** dans `tests/fixtures/`, puis écrire le parser **en se basant dessus** avec des tests. Le HTML des mails change parfois : les tests montrent tout de suite ce qui casse.

---

## 7. Étape 4 : Le filtre « data / SQL »

Deux conditions : **ville OK** ET **mot-clé trouvé** (et aucun mot d'exclusion).

```python
# src/jobbot/filters.py
import re, unicodedata

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return s.lower()

class OfferFilter:
    def __init__(self, cfg):
        self.inc = [re.compile(p, re.I) for p in cfg["mots_cles"]["inclure"]]
        self.exc = [re.compile(p, re.I) for p in cfg["mots_cles"].get("exclure", [])]
        self.villes = {k: [norm(a) for a in v["alias"]] for k, v in cfg["villes"].items()}

    def city_of(self, offer):
        loc = norm(offer.location)
        for key, aliases in self.villes.items():
            if any(a in loc for a in aliases):
                return key
        # France Travail : "59 - Lille", "75 - Paris 9e Arrondissement"
        if loc.startswith("59"): return "lille"
        if loc.startswith("75"): return "paris"
        return offer.city_key   # confiance à la requête source si rien d'autre

    def match(self, offer):
        texte_titre, texte_desc = offer.title, offer.description
        if any(p.search(texte_titre) or p.search(texte_desc) for p in self.exc):
            return False
        hits = []
        for p in self.inc:
            if p.search(texte_titre): hits.append(f"titre:{p.pattern}")
            elif p.search(texte_desc): hits.append(f"description:{p.pattern}")
        offer.matched_on = hits
        offer.city_key = self.city_of(offer)
        return bool(hits) and offer.city_key in self.villes
```

**Pourquoi ces regex ?**

| Regex                    | Attrape                                               | N'attrape pas (volontairement)       |
|--------------------------|-------------------------------------------------------|--------------------------------------|
| `\bdata\b`               | Data Analyst, Big Data, Data Engineer, « data »       | « database »¹, « update »            |
| `data[- ]?viz…`          | Dataviz, Data visualisation                           |                                      |
| `sql`                    | SQL, MySQL, PostgreSQL, NoSQL, T-SQL, PL/SQL, SQLite  |                                      |

¹ Si on veut aussi « database » : ajouter `\bdatabase\b`. Pour élargir au français : `\bdonnees\b` (attention, beaucoup plus de bruit).

💡 **Priorité** : une offre avec le mot-clé **dans le titre** est plus pertinente → notification en couleur différente / priorité ntfy haute.

---

## 8. Étape 5 : Dédoublonnage (SQLite)

Deux niveaux :
1. **Même source** : clé `(source, source_id)`.
2. **Inter-sources** (la même offre sur France Travail + Indeed + LinkedIn) : **empreinte** = hash de `titre normalisé + entreprise normalisée + ville`.

```python
# src/jobbot/storage.py
import sqlite3, hashlib, re
from jobbot.filters import norm

SCHEMA = """
CREATE TABLE IF NOT EXISTS offers (
    source       TEXT NOT NULL,
    source_id    TEXT NOT NULL,
    fingerprint  TEXT NOT NULL,
    title        TEXT,
    company      TEXT,
    city         TEXT,
    url          TEXT,
    first_seen   TEXT DEFAULT (datetime('now')),
    notified     INTEGER DEFAULT 0,
    PRIMARY KEY (source, source_id)
);
CREATE INDEX IF NOT EXISTS idx_fp ON offers(fingerprint);
"""

def fingerprint(o) -> str:
    t = re.sub(r"\(.*?\)|[hf]/[hf]|[^a-z0-9 ]", " ", norm(o.title))   # retire (H/F), ponctuation
    t = " ".join(t.split())
    c = " ".join(re.sub(r"[^a-z0-9 ]", " ", norm(o.company or "")).split())
    return hashlib.sha1(f"{t}|{c}|{o.city_key}".encode()).hexdigest()

class Store:
    def __init__(self, path="data/jobs.db"):
        self.db = sqlite3.connect(path)
        self.db.executescript(SCHEMA)

    def is_new(self, o) -> bool:
        fp = fingerprint(o)
        row = self.db.execute(
            "SELECT 1 FROM offers WHERE (source=? AND source_id=?) OR fingerprint=? LIMIT 1",
            (o.source, o.source_id, fp)).fetchone()
        return row is None

    def save(self, o, notified: bool):
        self.db.execute(
            "INSERT OR IGNORE INTO offers(source, source_id, fingerprint, title, company, city, url, notified) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (o.source, o.source_id, fingerprint(o), o.title, o.company, o.city_key, o.url, int(notified)))
        self.db.commit()
```

> 🌱 **Mode amorçage (`--seed`)** : au **tout premier lancement**, on enregistre toutes les offres existantes **sans notifier**, sinon il recevra 300 notifications d'un coup. Ensuite seules les vraies nouveautés partent.

> 🧹 Purge mensuelle : `DELETE FROM offers WHERE first_seen < datetime('now','-90 days');`

---

## 9. Étape 6 : Notifications Discord + ntfy

### 9.1 Discord (webhook + embed)

```python
# src/jobbot/notifiers/discord.py
import httpx, time

COULEURS = {"lille": 0xE30613, "paris": 0x1E3A8A}   # rouge Lille, bleu Paris

def send(webhook_url, o):
    titre_match = any(m.startswith("titre:") for m in o.matched_on)
    embed = {
        "title": f"{'🔥 ' if titre_match else ''}{o.title}"[:256],
        "url": o.url,
        "color": COULEURS.get(o.city_key, 0x808080),
        "fields": [
            {"name": "🏢 Entreprise", "value": o.company or "—", "inline": True},
            {"name": "📍 Lieu",       "value": o.location or o.city_key, "inline": True},
            {"name": "📄 Contrat",    "value": o.contract or "—", "inline": True},
            {"name": "💰 Salaire",    "value": o.salary or "—", "inline": True},
            {"name": "🔎 Trouvé dans", "value": ", ".join(o.matched_on)[:1024], "inline": False},
        ],
        "description": (o.description[:300] + "…") if o.description else None,
        "footer": {"text": f"Source : {o.source}"},
    }
    payload = {"username": "Offres Data/SQL", "embeds": [embed]}
    for _ in range(3):
        r = httpx.post(webhook_url, json=payload, timeout=15)
        if r.status_code == 429:                          # rate limit Discord
            time.sleep(float(r.json().get("retry_after", 2)))
            continue
        r.raise_for_status()
        return
```

> ⏱️ Discord limite à ~30 messages/min par webhook → petite pause (`time.sleep(1)`) entre deux envois, ou regrouper jusqu'à **10 embeds par message**.

### 9.2 ntfy

```python
# src/jobbot/notifiers/ntfy.py
import httpx

def send(base_url, topic, o, token=None):
    titre_match = any(m.startswith("titre:") for m in o.matched_on)
    headers = {
        "Title": f"[{o.city_key.upper()}] {o.title}".encode("utf-8"),
        "Click": o.url,
        "Tags": "briefcase,fire" if titre_match else "briefcase",
        "Priority": "high" if titre_match else "default",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = f"{o.company or ''} · {o.location}\nSource : {o.source}"
    httpx.post(f"{base_url}/{topic}", content=body.encode(), headers=headers, timeout=15).raise_for_status()
```

**Rendu attendu sur Discord :**

```
🔥 Data Analyst SQL / Power BI (H/F)                 ← lien cliquable
🏢 Entreprise : Decathlon   📍 Lieu : 59 - Villeneuve-d'Ascq   📄 CDI   💰 40-45 k€
🔎 Trouvé dans : titre:\bdata\b, titre:sql
Source : francetravail
```

---

## 10. Étape 7 : Orchestration et planification

### 10.1 `main.py` : le pipeline

```python
# src/jobbot/main.py (simplifié)
import argparse, logging
from jobbot.config import load
from jobbot.filters import OfferFilter
from jobbot.storage import Store
from jobbot.notifiers import discord, ntfy

log = logging.getLogger("jobbot")

def run(seed=False, dry_run=False):
    cfg, env = load()
    store, flt = Store(), OfferFilter(cfg)
    sources = build_sources(cfg, env)          # FranceTravail, Adzuna, EmailAlerts…

    candidates = []
    for src in sources:
        try:
            got = src.fetch()
            log.info("%s : %d offres récupérées", src.__class__.__name__, len(got))
            candidates += got
        except Exception:
            log.exception("Source %s en échec, on continue avec les autres", src)

    nouvelles = [o for o in candidates if flt.match(o) and store.is_new(o)]
    log.info("%d nouvelles offres pertinentes", len(nouvelles))

    for o in nouvelles[: cfg["notifications"]["max_par_execution"]]:
        if not (seed or dry_run):
            if cfg["notifications"]["discord"]: discord.send(env["DISCORD_WEBHOOK_URL"], o)
            if cfg["notifications"]["ntfy"]:    ntfy.send(env["NTFY_URL"], env["NTFY_TOPIC"], o, env.get("NTFY_TOKEN"))
        if not dry_run:
            store.save(o, notified=not seed)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seed", action="store_true", help="remplit la base sans notifier")
    p.add_argument("--dry-run", action="store_true", help="affiche sans notifier ni enregistrer")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run(seed=a.seed, dry_run=a.dry_run)
```

**Principes de robustesse :**
- Une source qui plante **n'empêche pas** les autres de tourner.
- On enregistre en base **après** l'envoi réussi de la notif → si Discord est down, l'offre sera renvoyée au prochain passage (pas perdue).
- `max_par_execution` évite d'inonder Discord en cas de bug.

### 10.2 Fréquence

| Source         | Fréquence conseillée |
|----------------|----------------------|
| France Travail | toutes les 15 min    |
| Adzuna         | toutes les 30 min    |
| E-mails        | toutes les 5–15 min  |

Simple : **tout toutes les 15 min** (en journée 7h–22h suffit, éventuellement).

### 10.3 systemd timer (recommandé sur Linux / Raspberry Pi / VPS)

`deploy/jobbot.service`

```ini
[Unit]
Description=Bot offres Data/SQL Lille-Paris
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/opt/bot-offres-data
EnvironmentFile=/opt/bot-offres-data/.env
ExecStart=/opt/bot-offres-data/.venv/bin/python -m jobbot.main
User=jobbot
```

`deploy/jobbot.timer`

```ini
[Unit]
Description=Lance le bot offres toutes les 15 min

[Timer]
OnCalendar=*:0/15
Persistent=true
RandomizedDelaySec=60

[Install]
WantedBy=timers.target
```

```bash
sudo cp deploy/jobbot.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now jobbot.timer
journalctl -u jobbot.service -f        # voir les logs
```

**Alternative cron :**

```cron
*/15 * * * * cd /opt/bot-offres-data && .venv/bin/python -m jobbot.main >> logs/jobbot.log 2>&1
```

---

## 11. Étape 8 : Hébergement

| Option                         | Coût        | Avantages                                  | Inconvénients                                  |
|--------------------------------|-------------|--------------------------------------------|------------------------------------------------|
| **Raspberry Pi / PC maison**   | ~0 €        | Contrôle total, SQLite local               | Dépend de la box/électricité                   |
| **Petit VPS** (Hetzner, OVH, Scaleway) | 3–5 €/mois | Fiable 24/7, IP fixe                  | Petite admin Linux                             |
| **Oracle Cloud Free Tier**     | 0 €         | VM gratuite permanente                     | Inscription parfois pénible                    |
| **GitHub Actions** (cron)      | 0 €         | Aucun serveur                              | Cron imprécis (retards), il faut **persister la base SQLite** (commit dans une branche `state` ou cache) ; secrets dans *GitHub Secrets* |

👉 **Recommandation** : un **petit VPS** ou un **Raspberry Pi** avec systemd timer. C'est le plus simple à déboguer et le plus fiable.

Si GitHub Actions est choisi, squelette :

```yaml
# .github/workflows/jobbot.yml
on:
  schedule: [{ cron: "*/15 6-21 * * *" }]   # UTC !
  workflow_dispatch:
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: Restaurer la base
        run: git fetch origin state && git show origin/state:jobs.db > data/jobs.db || true
      - run: uv run python -m jobbot.main
        env:
          FT_CLIENT_ID: ${{ secrets.FT_CLIENT_ID }}
          # … autres secrets
      - name: Sauvegarder la base
        run: |  # pousser data/jobs.db sur la branche "state"
          …
```

---

## 12. Étape 9 : Supervision, logs et robustesse

- **Logs** : `logging` standard → journald (systemd) ou fichier avec rotation (`logging.handlers.RotatingFileHandler`).
- **Heartbeat quotidien** : un message Discord chaque matin à 9h :
  `✅ Bot OK : 14 offres envoyées hier (FT : 9, Adzuna : 3, LinkedIn : 2)`.
  → S'il n'arrive pas, c'est que le bot est mort.
- **Alerte en cas d'erreur** : salon Discord séparé `#bot-logs` (2ᵉ webhook) qui reçoit les exceptions.
- **Monitoring externe gratuit** : [healthchecks.io](https://healthchecks.io), on « ping » une URL à la fin de chaque exécution ; si plus de ping depuis 1h → e-mail/Discord.
- **Retries** avec backoff sur les appels HTTP (3 essais, 2s/4s/8s).
- **Timeouts** partout (jamais de requête sans timeout).
- **Détection de parser cassé** : si un mail LinkedIn est reçu mais 0 offre extraite → log `WARNING` + notif dans `#bot-logs`.

---

## 13. Étape 10 : Tests

```bash
uv run pytest -q
uv run ruff check .
uv run python -m jobbot.main --dry-run     # test grandeur nature sans rien envoyer
```

Tests indispensables :

| Test                   | Ce qu'on vérifie                                                                 |
|------------------------|-----------------------------------------------------------------------------------|
| `test_filters.py`      | « Data Analyst » ✅, « Développeur PostgreSQL » ✅, « Database admin » ❌ (selon config), « Comptable » ❌, offre à Lyon ❌ |
| `test_storage.py`      | même offre 2× → notifiée 1 fois ; même offre sur 2 sources → 1 fois              |
| `test_parsers.py`      | chaque `.eml` de `fixtures/` → nombre d'offres attendu, titres/URL corrects      |
| `test_francetravail.py`| réponse JSON simulée (`respx`) → `Offer` correctement construits                  |

---

## 14. Sécurité, légalité et CGU

- 🔐 **Secrets** uniquement dans `.env` (droits `chmod 600`), jamais dans Git. Sur GitHub : *Secrets*.
- 🔐 Mot de passe **d'application** Gmail, révocable à tout moment, jamais le vrai mot de passe.
- 🔐 Topic ntfy **aléatoire** (ou protégé par token).
- 🔐 Webhook Discord = secret ; s'il fuit : le supprimer et en recréer un.
- ⚖️ **APIs officielles** (France Travail, Adzuna) : respecter leurs quotas et conditions.
- ⚖️ **Pas de scraping** de LinkedIn / Indeed / WTTJ : on passe par **leurs alertes e-mail**, c'est l'usage prévu.
- ⚖️ Usage **personnel** : on ne republie pas les offres publiquement (serveur Discord privé).
- 🧾 Les données stockées sont des offres publiques ; pas de données personnelles à part la boîte mail du bot.

---

## 15. Roadmap / améliorations

**V1 (MVP, 1 week-end)**
- [ ] France Travail + Discord + SQLite + systemd timer + `--seed`

**V2**
- [ ] Adzuna
- [ ] Alertes e-mail LinkedIn + Indeed
- [ ] ntfy
- [ ] Heartbeat quotidien + healthchecks.io

**V3 (confort)**
- [ ] Salons Discord séparés Lille / Paris
- [ ] Filtres par type de contrat (CDI / alternance / stage) et par niveau
- [ ] Mise en évidence des technos détectées (Python, Power BI, dbt, Snowflake, Airflow…)
- [ ] Récap hebdo : nombre d'offres, top entreprises, techno les plus demandées
- [ ] Bot Discord « vrai » (discord.py) avec boutons ✅ *Intéressé* / ❌ *Pas pour moi* / 📨 *Candidaté* → suivi des candidatures dans SQLite
- [ ] Score de pertinence (mots-clés pondérés) et seuil minimal
- [ ] Docker (`Dockerfile` + `docker compose`) pour déployer partout en une commande

---

## 16. Checklist finale

**Comptes**
- [ ] Boîte Gmail dédiée créée, 2FA activée, mot de passe d'application généré, IMAP activé
- [ ] Libellé `jobs` + filtre Gmail en place
- [ ] Alertes créées sur LinkedIn, Indeed, HelloWork, WTTJ, APEC (Lille + Paris, data/SQL)
- [ ] (Option) Alertes Cadremploi, Free-Work, LesJeudis, Glassdoor, Meteojob, Monster
- [ ] Application francetravail.io créée et abonnée à « Offres d'emploi v2 »
- [ ] Clés Adzuna récupérées
- [ ] Salon Discord + webhook
- [ ] App ntfy installée + abonnement au topic aléatoire

**Code**
- [ ] Projet initialisé (`uv`), `.env` rempli, `.gitignore` OK
- [ ] Collecteur France Travail testé en `--dry-run`
- [ ] Filtre testé (pytest)
- [ ] Dédoublonnage testé
- [ ] Notification Discord de test reçue
- [ ] Notification ntfy de test reçue
- [ ] Parsers e-mails écrits à partir de vrais mails (fixtures)

**Mise en production**
- [ ] `python -m jobbot.main --seed` lancé **une fois**
- [ ] systemd timer activé (`systemctl list-timers` le montre)
- [ ] Heartbeat quotidien reçu le lendemain matin
- [ ] healthchecks.io configuré

---

### ⏱️ Estimation

| Bloc                                  | Temps     |
|---------------------------------------|-----------|
| Création des comptes + alertes        | 1 h       |
| France Travail + filtre + SQLite + Discord (MVP) | 3–4 h |
| Adzuna + ntfy                         | 1 h       |
| Parsers e-mails + tests               | 2–3 h     |
| Déploiement + supervision             | 1–2 h     |
| **Total**                             | **~1 week-end** |
