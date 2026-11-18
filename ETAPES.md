# ✅ Liste des étapes : Bot offres Data/SQL (Lille + Paris)

> Liste à cocher, dans l'ordre. Chaque étape renvoie à la partie détaillée de `PLAN.md`.
> 🧑 = à faire à la main (comptes, clics) · 💻 = code · 🚀 = mise en ligne
> Règle : **on ne passe à la phase suivante que quand la précédente marche.**

---

## PHASE 0 : Préparation (≈ 30 min)

- [x] **0.1** 🧑 Décider où le bot tournera : Raspberry Pi / PC allumé en permanence / petit serveur loué 3–5 €/mois (*PLAN § 11*) → **VPS OVH de louishanquiez.fr** (2026-11-15)
- [ ] **0.2** 🧑 Décider des options :
  - [x] CDI uniquement, ou aussi CDD / alternance / stage / freelance ? → **tous contrats** (2026-11-15)
  - [ ] Lille seule ou toute la métropole (Roubaix, Villeneuve-d'Ascq…) ?
  - [x] Paris seul ou avec La Défense et la petite couronne ? → **Paris + alias actuels** (La Défense, Puteaux, Nanterre…), pas toute la petite couronne
  - [ ] Discord seulement, ou Discord + ntfy sur le téléphone ?
- [x] **0.3** 💻 Installer sur la machine de dev : Python 3.12+, `uv`, `git`

---

## PHASE 1 : Créer les comptes (≈ 1 h)

### Boîte mail dédiée
- [x] **1.1** 🧑 Créer le Gmail dédié (ex. `alertes.data.xxx@gmail.com`)
- [x] **1.2** 🧑 Activer la validation en 2 étapes
- [x] **1.3** 🧑 Générer un **mot de passe d'application** → le noter dans un endroit sûr
- [x] **1.4** 🧑 Vérifier que l'IMAP est activé
- [x] **1.5** 🧑 Créer le libellé `jobs`

### Discord
- [x] **1.6** 🧑 Créer le serveur Discord (ou en choisir un) + salon `#offres-data`
- [ ] **1.7** 🧑 Créer le salon `#bot-logs` (erreurs + message de contrôle quotidien)
- [ ] **1.8** 🧑 Créer un webhook pour chaque salon → copier les 2 URL

### ntfy (optionnel)
- [ ] **1.9** 🧑 Installer l'app ntfy sur le téléphone
- [ ] **1.10** 💻 Générer un nom de topic aléatoire et s'y abonner dans l'app

### API
- ~~**1.11** 🧑 Créer un compte sur **francetravail.io**…~~ *(retiré le 2026-11-15 : France Travail n'est plus une source)*
- [ ] **1.12** 🧑 Créer un compte **Adzuna developer** → noter `app_id` / `app_key`

---

## PHASE 2 : MVP : source → Discord (≈ 3–4 h)

> But : **une vraie offre reçue sur Discord** à la fin de cette phase.

- [x] **2.1** 💻 Créer le dépôt git `bot-offres-data`, `uv init`, ajouter les dépendances (*PLAN § 4*)
- [x] **2.2** 💻 Créer `.gitignore`, `.env.example`, `.env` (rempli avec les clés de la phase 1)
- [x] **2.3** 💻 Créer `config.yaml` : villes, mots-clés, exclusions (*PLAN § 5*)
- [x] **2.4** 💻 Écrire `models.py` (format commun `Offer`)
- [x] **2.5** 💻 Écrire `config.py` (charge `.env` + YAML)
- ~~**2.6** 💻 Écrire le collecteur **France Travail**~~ *(retiré le 2026-11-15 : source abandonnée, code supprimé)*
  - [x] **2.6 bis** 💻 Source MVP = **alertes e-mail** (Indeed + HelloWork, *PLAN § 6.4*) → 10 premières offres affichées (93 récupérées le 2026-11-15)
- [x] **2.7** 💻 Écrire `filters.py` (ville + regex data/sql + exclusions) (*PLAN § 7*)
  - [x] Tests `pytest` : Data Analyst ✅, Dev PostgreSQL ✅, Comptable ❌, offre à Lyon ❌
- [x] **2.8** 💻 Écrire `storage.py` (SQLite + empreinte anti-doublon) (*PLAN § 8*)
  - [x] Test : la même offre 2 fois n'est notifiée qu'une fois
- [x] **2.9** 💻 Écrire `notifiers/discord.py` (message mis en forme + gestion de la limite d'envoi Discord) (*PLAN § 9.1*)
  - [x] Test : envoyer une offre bidon dans `#offres-data`
- [x] **2.10** 💻 Écrire `main.py` avec `--dry-run` et `--seed` (*PLAN § 10.1*)
- [x] **2.11** 💻 Lancer `--dry-run` → vérifier la liste des offres retenues (pas trop de bruit ? rien d'oublié ?)
- [x] **2.12** 💻 Ajuster les regex / exclusions dans `config.yaml` si besoin *(`\bdata(?!base)`, `analytics engineer`, exclusion « data center »)*
- [x] **2.13** 💻 Lancer `--seed` une fois (remplit la base sans notifier) *(50 offres, 2026-11-15)*
- [x] **2.14** 💻 Lancer normalement → seules les nouvelles offres arrivent ✅ *(1 vraie offre HelloWork reçue sur Discord, relance suivante : 0)*

---

## PHASE 2B : Multi-profils (3 amis) (*PROMPT_MULTI_PROFILS.md*)

- [x] **2B.1** 💻 `profiles.yaml` + chargement/validation (`profiles.py`) : erreurs claires (ville, contrat, regex, champ inconnu, id en double)
- [x] **2B.2** 💻 Détection du contrat (`contracts.py`) : titre prioritaire pour stage/alternance, puis champ source, puis titre
- [x] **2B.3** 💻 Filtre par profil (`filters.evaluate`) : ville → contrat → exclusions → mots-clés → ⭐, avec la raison du rejet
- [x] **2B.4** 💻 Stockage par profil + migration de la base (50 offres → `alternance-data`) ; sauvegarde `data/jobs.db.avant-multiprofils`
- [x] **2B.5** 💻 Discord : salon (webhook) par profil, ⭐ + contrat + nom du profil dans le message ; profil sans webhook = ignoré avec erreur
- [x] **2B.6** 💻 `main` : `--profil <id>` (avec `--dry-run` : montre aussi les rejets), `--seed` par profil
- [x] **2B.7** 💻 `--dry-run` sur les vrais mails, 3 profils
- [x] **2B.8** 🧑 Discord : créer les salons `#dev` et `#stage-asso` + un webhook chacun → `DISCORD_WEBHOOK_DEV` / `DISCORD_WEBHOOK_STAGE` dans `.env`
- [x] **2B.9** 🧑 Créer les alertes **dev** sur la boîte dédiée : HelloWork + Indeed (« développeur », « développeur java », « développeur angular » × Lille + Paris, CDI/CDD) *(2026-11-15, par Claude : voir tableau)*
- [x] **2B.10** 🧑 Créer les alertes **stage-asso** (HelloWork + Indeed « stage chargé d'études / de mission » × Lille + Paris) ; sources spécialisées : voir 2B.10b *(2026-11-15, par Claude : voir tableau)*
- [ ] **2B.10b** 🧑 Alertes sur les sites spécialisés (boîte dédiée, une ligne par site) :
  - [x] Jobs that make sense : compte via Google (2026-11-15), alertes « Stage · Paris » + « Stage · Lille » sans mot-clé (le bot filtre) ; pas de réglage de fréquence sur le site
  - [x] Coordination SUD : alerte emploi France · Stage ou Alternance · toutes fonctions (formulaire envoyé le 2026-11-15, pas de compte ; arrivée du 1er mail à vérifier)
  - [ ] PASS (stages fonction publique) → 🧑 inscription par mot de passe + CAPTCHA : à faire par Louis
  - [ ] Welcome to the Jungle : compte créé via Google ; **alertes indisponibles sur le site** (« makeover », retour annoncé « dans quelques semaines ») → à refaire
  - [ ] APEC → 🧑 pas de connexion Google, compte par mot de passe : à faire par Louis
  - [ ] Free-Work → compte créé via Google ; 🧑 une fenêtre « Bienvenue » obligatoire demande civilité / prénom / nom (données perso) avant de pouvoir créer l'alerte
  - [x] Les Jeudis : compte via Google ; 3 alertes Junior · CDI+CDD · Paris (75) + Lille, quotidiennes : « développeur », « développeur java », « développeur angular » ⚠️ **expirent après 30 jours** (à renouveler vers le 2026-12-15)
  - [ ] Carenews → 🧑 compte par mot de passe uniquement ; alertes quotidiennes sur critères disponibles ensuite
  - [ ] Idealist (optionnel, surtout international, peu d'offres Lille/Paris) ; Le Media Social Emploi (site en erreur 503 le 2026-11-15)
  - [x] LinkedIn : compte créé par Louis (Google, boîte dédiée) ; 16 alertes (12 + 2 « RSE / chargé de projet » + 2 « diversité / mécénat / QVT ») créées par Claude et vérifiées le 2026-11-15, quotidiennes par e-mail (Lille = geoId 90009695, Paris = geoId 90009659) → parser LinkedIn à écrire sur les premiers mails
  - [ ] JobTeaser Dauphine → fait par l'ami (message fourni) + transfert Gmail
  - ~~Ressources Solidaires~~ : écarté, domaine repris par un site de casinos/crédit (vérifié le 2026-11-15)
  - ~~Animafac~~ : pas de job board, ses offres passent par Jobs that make sense
- [ ] **2B.10c** 💻 Source API **La bonne alternance** (profil alternance-data) : lien de connexion (sans mot de passe) envoyé dans la boîte dédiée le 2026-11-15 → 🧑 cliquer le lien, générer la clé, la mettre dans `.env` (`LBA_API_KEY`) ; usage non lucratif uniquement
  - [x] 💻 Source écrite et testée (`sources/labonnealternance.py`, 2026-11-15) ; désactivée (`sources.labonnealternance: false`) tant que la clé manque
  - [ ] 🧑 Clé dans `.env`, puis `labonnealternance: true`, vérifier les codes ROME, `--dry-run --profil alternance-data`

#### Tableau site × profil × alertes créées

| Site | alternance-data | dev | stage-asso | Remarques |
|---|---|---|---|---|
| Indeed | data OR sql (Lille, Paris) | « développeur » + « développeur (java OR angular OR "full stack") » × Paris (75), Lille (59) | « stage ("chargé d'études" OR "chargé de mission" OR sociologie OR association OR ESS OR plaidoyer) » + « stage (RSE OR "chargé de projet" OR "responsabilité sociétale" OR "développement durable") » + « stage title:(diversité OR inclusion OR handicap OR mécénat OR "relations sociales" OR QVT OR RSE) » × Paris, Lille | pas de filtre contrat (le bot le déduit) |
| HelloWork | 5 alertes × Lille/Paris (tous contrats, alternance incluse) | Développeur informatique × Paris, × Lille ; Développeur full-stack × Lille ; full-stack + Java + Angular × Paris + Lille (CDI+CDD) | Sociologue + Chargé de projet + Chargé de mission sociale ; Chargé de mission insertion + Chargé d'études prospectives + Chargé de développement social ; Chargé de mission RSE (Stage, Paris + Lille) | métiers imposés par le référentiel HelloWork : pas de « chargé d'études » générique ni « plaidoyer » ; filtre expérience non conservé dans l'alerte |
| Jobs that make sense | — | — | Stage · Paris, Stage · Lille | alerte sans mot-clé |
| Coordination SUD | — | — | France · Stage · toutes fonctions | newsletter quotidienne |
| Les Jeudis | — | développeur, dév. java, dév. angular (Lille+Paris, junior, CDI/CDD) | — | « full stack » non créé : couvert par « développeur » ; expire à 30 j |
| Welcome to the Jungle | ⏳ | ⏳ | ⏳ | alertes indisponibles sur le site |
| LinkedIn | `alternance (data OR SQL OR BI)` + `apprentissage data analyst OR data engineer` × Paris, Lille | `développeur` + `java OR angular OR "full stack"` × Paris, Lille, niveau « Premier emploi » | `stage ("chargé d'études" OR "chargé de mission" OR sociologie)` + `stage (association OR ESS OR plaidoyer OR ONG)` + `stage (RSE OR "chargé de projet" OR "responsabilité sociétale")` + `stage (diversité OR inclusion OR handicap OR mécénat OR "relations sociales" OR QVT)` × Paris, Lille, filtre « Stage / Alternance » | la nouvelle recherche LinkedIn ignore les filtres passés dans l'URL ; pas de filtre « Temps plein » |

- [ ] **2B.11** 💻 Parser générique + étude des sites asso/ESS (JobTeaser Dauphine, Jobs that make sense, Coordination SUD, Ressources Solidaires…)
  - [x] Prérequis 1 : expéditeurs sans parser comptés, journalisés et affichés en `--dry-run` (2026-11-15)
  - [x] Prérequis 2 : `email_alerts/links.py`, nettoyage commun des liens (paramètres de suivi retirés, lien rejeté s'il contient l'adresse de la boîte en clair, sans points, %-encodée ou en base64), appliqué à **toutes** les offres e-mail (2026-11-15)
  - [x] (déjà en place) dédoublonnage entre sources par empreinte titre + entreprise + ville (`storage.fingerprint`)
  - [x] Identifiant unique lu dans le lien (`email_alerts/canonical.py` : LinkedIn, Indeed, HelloWork, makesense, WTTJ, APEC, JobTeaser, Free-Work) → lien publié canonique + dédoublonnage par lien reconnu (2026-11-15)
  - [x] Parsers dédiés (2026-11-18, 18 vrais `.eml` en fixtures) : **LinkedIn**, **Jobs that make sense** (lien réel décodé du suivi customer.io, pubs « Partenariat sponsorisé » ignorées, ville de l'alerte si l'adresse n'en a pas), **Coordination SUD** (identifiant d'abonné retiré du lien), **Les Jeudis** ; mails de pub/service de ces sites sans effet sur la santé
  - [ ] ⚠️ Coordination SUD ne donne que « Europe, France » : la ville n'est connue que si le titre la cite → la plupart de ses offres sont écartées par le filtre ville (à décider)
  - [ ] Parser générique (JobTeaser, Free-Work, APEC… quand leurs mails arriveront)
- [ ] **2B.12** 💻 `--dry-run --profil` sur les nouveaux mails → ajuster `profiles.yaml` → premier envoi réel par profil
- [x] **2B.13** 💻 Alerte panne dans `#bot-logs` (`health.py`, 2026-11-15) : expéditeur attendu muet > 48 h (`sante.expediteurs` dans config.yaml), dernier mail sans offre, source en échec, webhook vide, envoi Discord raté, plantage ; une alerte par problème puis « rétabli »
  - [ ] 🧑 1.7–1.8 : créer `#bot-logs` + son webhook → `DISCORD_LOGS_WEBHOOK_URL` (en attendant, les alertes restent dans le journal)
- [x] **2B.13b** 💻 Score 0–100 expliqué (barème + `bonus` par profil dans profiles.yaml, `score_min` optionnel), offres triées par score, score sur Discord et en `--dry-run` (2026-11-15)
- [x] **2B.13c** 💻 Récapitulatif : à partir de `recap_a_partir_de` offres (8 par défaut) dans un passage, un message récapitulatif trié au lieu d'un message par offre (2026-11-15)
- [x] **2B.13d** 💻 Profil stage-asso refait d'après le diaporama « Stages 2016-2024 » de la majeure Politiques d'entreprises (2026-11-15) : RSE ⭐, diversité/handicap, mécénat/fondations, relations sociales/QVT/QSE, développement durable, public, ESS ; **exclus** : conseil / expertise / études et finance responsable (intitulés + liste d'employeurs) ; 35 cas réels en tests (`tests/test_stage_asso_diapo.py`)
- [x] **2B.13e** 🧑💻 Liste unique des stages en ligne pour stage-asso (2026-11-15, exception ponctuelle à la règle « pas de scraping » validée par Louis pour Indeed et HelloWork ; LinkedIn exclu) : 525 stages lus (Jobs that make sense, Indeed, HelloWork, Coordination SUD, Carenews), triés par le profil → 67 cœur de cible + 165 à regarder, page privée sur claude.ai. Profil renforcé au passage : exclusions conseil/finance complétées, malus marketing/IT/commercial, bénévolat et service civique exclus
- [ ] **2B.14** 💻 Récap hebdo (`--recap`)

---

## PHASE 3 : Mise en ligne 24h/24 (≈ 1–2 h)

- [x] **3.1** 🚀 Préparer la machine : convention du VPS suivie (utilisateur `ubuntu`, `/home/ubuntu/bot-offres-data`, service `perso-jobbot`) ; `uv` installé dans `~/.local/share/uv-env`
- [x] **3.2** 🚀 Copier le projet + `.env` (`chmod 600 .env`) : `./deploy/deploy.sh --premiere` (puis `./deploy/deploy.sh` pour chaque mise à jour du code)
- [x] **3.3** 🚀 `uv sync` puis `--dry-run` sur la machine (IMAP OK depuis le VPS, 105 offres lues)
- [x] **3.4** 🚀 ~~`--seed`~~ : la base locale `data/jobs.db` a été copiée sur le serveur (garde l'historique, rien n'est renvoyé)
- [x] **3.5** 🚀 `deploy/perso-jobbot.service` + `.timer`, toutes les 15 min, actifs depuis le 2026-11-15
- [x] **3.6** 🚀 Vérifier : `systemctl list-timers perso-jobbot.timer` et `journalctl -u perso-jobbot.service` (1er passage réussi)
- [ ] **3.7** 🧑 Laisser tourner **48 h** et regarder ce qui arrive sur Discord

---

## PHASE 4 : Alertes e-mail (LinkedIn, Indeed, HelloWork…) (≈ 3 h, en 2 temps)

### 4A : Créer les alertes (le jour J)
- [ ] **4.1** 🧑 Créer un filtre Gmail : mails de LinkedIn / Indeed / HelloWork / WTTJ / APEC / … → libellé `jobs`
- [ ] **4.2** 🧑 Créer les alertes avec la boîte dédiée, **data** et **SQL**, **Lille** et **Paris** (*PLAN § 3.2*) :
  - [x] LinkedIn *(2026-11-18, `jobalerts-noreply@` uniquement ; les autres mails LinkedIn sont ignorés)*
  - [x] Indeed (« data OR sql », Lille 59 + Paris 75)
  - [x] HelloWork (Data analyst, Data engineer, Data scientist, Développeur SQL, Consultant BI × Lille + Paris, tous contrats, quotidienne)
  - [ ] Welcome to the Jungle : compte créé via Google ; **alertes indisponibles sur le site** (« makeover », retour annoncé « dans quelques semaines ») → à refaire
  - [ ] APEC → 🧑 pas de connexion Google, compte par mot de passe : à faire par Louis
  - [ ] (option) Cadremploi, Free-Work, LesJeudis, Glassdoor, Meteojob, Monster, Jobteaser
- [ ] **4.3** 🧑 Attendre 2–3 jours pour recevoir de vrais mails d'alerte

### 4B : Coder la lecture (quand les mails sont arrivés)
- [x] **4.4** 💻 Enregistrer 2–3 mails de chaque site en `.eml` dans `tests/fixtures/`
- [x] **4.5** 💻 Écrire la lecture IMAP (`sources/email_alerts/__init__.py`) — *choix final : relit les N derniers jours sans marquer « lu », la base SQLite dédoublonne*
- [ ] **4.6** 💻 Écrire le **parser générique** (pour n'importe quel site)
- [ ] **4.7** 💻 Écrire les parsers dédiés, chacun avec ses tests :
  - [x] LinkedIn *(2026-11-18, `jobalerts-noreply@` uniquement ; les autres mails LinkedIn sont ignorés)*
  - [x] Indeed
  - [x] HelloWork
  - [ ] WTTJ (si beaucoup de volume)
  - [x] Jobs that make sense, Coordination SUD, Les Jeudis *(2026-11-18, voir 2B.11)*
- [ ] **4.8** 💻 Brancher la source e-mail dans `main.py` → `--dry-run` → déployer

---

## PHASE 5 : Sources en plus (≈ 1–2 h)

- [ ] **5.1** 💻 Collecteur **Adzuna** (*PLAN § 6.3*)
- [ ] **5.2** 💻 Notifications **ntfy** (*PLAN § 9.2*)
- [x] **5.3** 🧑 Lister les entreprises cibles (ESN, scale-ups, grands groupes à Lille et Paris) *(2026-11-18 : 28 entreprises trouvées en sondant les API, liste dans `config.yaml` → `carrieres.entreprises` ; peu de Lillois : la plupart des grands groupes du Nord utilisent des outils sans API publique)*
- [x] **5.4** 💻 Collecteur **pages carrières** (`sources/careers.py`, 2026-11-18) : Greenhouse, Lever, Ashby, Workable, Recruitee, SmartRecruiters ; au plus 1 passage/heure ; annonce complète dans `Offer.fiche`, lue par les regex `fiche:` d'un profil (SmartRecruiters : titre seul)
- [x] **5.4b** 💻 Mot-clé dans l'annonce via l'alerte du site (2026-11-18) : nom de l'alerte lu dans le sujet du mail (`Offer.alert`) ; `alertes_fiche:` dans un profil = la recherche du site suffit (score −10, 🔔 sur Discord)
- [ ] **5.5** 🚀 Déployer + vérifier qu'il n'y a pas de doublons entre les sources

---

## PHASE 6 : Fiabilité et surveillance (≈ 1–2 h)

- [ ] **6.1** 💻 Nouvelles tentatives automatiques + délai maximal sur tous les appels HTTP
- [ ] **6.2** 💻 Envoyer les erreurs dans `#bot-logs`
- [ ] **6.3** 💻 Message de contrôle chaque matin à 9h : « ✅ Bot OK : X offres hier (par source) »
- [ ] **6.4** 💻 Alerte si un parser e-mail sort 0 offre d'un mail (= le site a changé son format)
- [ ] **6.5** 🧑 Compte **healthchecks.io** + ping à la fin de chaque exécution
- [ ] **6.6** 💻 Purge automatique des offres de plus de 90 jours dans la base
- [ ] **6.7** 💻 Sauvegarde hebdomadaire de `jobs.db`

---

## PHASE 7 : Confort (optionnel)

- [ ] **7.1** Salons séparés `#offres-lille` / `#offres-paris`
- [ ] **7.2** Filtre par contrat (CDI / alternance / stage / freelance)
- [ ] **7.3** Mise en évidence des technos (Python, Power BI, dbt, Snowflake, Airflow…)
- [ ] **7.4** Récap hebdo (nombre d'offres, top entreprises, technos les plus demandées)
- [ ] **7.5** Vrai bot Discord avec boutons ✅ Intéressé / ❌ Non / 📨 Candidaté → suivi des candidatures
- [ ] **7.6** Score de pertinence + seuil minimal
- [ ] **7.7** Dockeriser le projet

---

## 📅 Planning conseillé

| Quand        | Quoi                                                         |
|--------------|--------------------------------------------------------------|
| Jour 1       | Phases 0, 1 et **4A** (créer les alertes tôt pour recevoir des mails) |
| Jour 1–2     | Phase 2 (MVP source → Discord)                               |
| Jour 2       | Phase 3 (mise en ligne) → **le bot tourne déjà** 🎉          |
| Jour 4–5     | Phase 4B (lecture des alertes e-mail)                        |
| Semaine 2    | Phases 5 et 6                                                |
| Plus tard    | Phase 7 selon les envies                                     |

## 🔑 À rassembler avant de coder

| Info                              | Où la trouver                      | Rempli ? |
|-----------------------------------|------------------------------------|----------|
| Adresse + mot de passe d'application Gmail | Compte Google → Sécurité  | [ ]      |
| URL webhook `#offres-data`        | Discord → salon → Intégrations     | [ ]      |
| URL webhook `#bot-logs`           | Discord → salon → Intégrations     | [ ]      |
| Topic ntfy                        | généré à l'étape 1.10              | [ ]      |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY`  | developer.adzuna.com             | [ ]      |
| Accès SSH à la machine d'hébergement | fournisseur VPS / Pi            | [ ]      |
