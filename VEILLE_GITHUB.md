# Veille GitHub : projets proches du bot (2026-11-15)

Méthode : API de recherche GitHub (mots-clés génériques), lecture des README et des
arborescences, et d'un fichier de code (`alternabot/lba.py`). Rien n'a été cloné ni exécuté.
16 projets retenus sur une soixantaine de résultats ; beaucoup de résultats étaient hors sujet.

## 1. Tableau des projets

| Projet | ⭐ | Dernière activité | Licence | Sources | Points forts |
|---|---|---|---|---|---|
| [Schlaflied/career-ops-plugin-linkedin-alerts](https://github.com/Schlaflied/career-ops-plugin-linkedin-alerts) | 3 | 2026-07 | MIT | **Alertes e-mail LinkedIn** (API Gmail) | URL LinkedIn ramenées à une forme canonique `linkedin.com/jobs/view/{id}` ; accès Gmail en **lecture seule** (OAuth `gmail.readonly`) |
| [iskandarreza/job-post-email-data](https://github.com/iskandarreza/job-post-email-data) | 4 | 2023-03 | GPL-3.0 | Alertes LinkedIn (libellé Gmail) | Google Apps Script → Google Sheet ; va ensuite lire chaque page d'offre (scraping) |
| [ztancankiri/linkedin-job-alert-crawler](https://github.com/ztancankiri/linkedin-job-alert-crawler) | 1 | 2023-07 | GPL-3.0 | Alertes LinkedIn (Gmail) | petit, peu documenté |
| [roshani01/linkedin_job_ai_alert](https://github.com/roshani01/linkedin_job_ai_alert) | 1 | 2026-08 | — | **IMAP Gmail** (mails de recruteurs) | tri par LLM (Gemini), envoi Telegram, API FastAPI |
| [weberwcwei/job-scout](https://github.com/weberwcwei/job-scout) | 32 | 2026-04 | MIT | scraping (6 sites via JobSpy) | **score 0–100** par paliers de mots-clés + entreprises cibles + « dealbreakers » regex ; doublons par contenu ; **alerte si 0 résultat** ; multi-config ; `apply <id>` ; rapport quotidien |
| [Journey-512/catch-before-jobs-vanish](https://github.com/Journey-512/catch-before-jobs-vanish) | 23 | 2026-08 | MIT | agent IA qui navigue (LinkedIn, Indeed, pages carrière) | score « fondé sur des preuves » (exigences de l'offre vs CV), raison du score, un mail par jour, historique dans Google Sheet |
| [esdrassantos06/vagas-tech-pt](https://github.com/esdrassantos06/vagas-tech-pt) | 2 | 2026-11 | MIT | RSS, HTML, Playwright (Portugal) | **chaque exécution journalisée** (`scrape_runs`), parsers qui « échouent fort », alerte admin, **test canari hebdomadaire** contre les vrais sites ; `also_on` (même offre sur d'autres sites) ; digest par abonnement |
| [harshpreet4901-ux/job-hunt-tracker](https://github.com/harshpreet4901-ux/job-hunt-tracker) | 1 | 2026-08 | — | **API JSON publiques Greenhouse / Lever / Freshteam** + HTML | digest e-mail des offres **nouvelles ou modifiées** ; assistant de configuration au 1er lancement ; `max_experience_years` |
| [YChaoWang/JobOpeningNotifier](https://github.com/YChaoWang/JobOpeningNotifier) | 0 | 2026-11 | MIT | listes publiques sur GitHub | **1er passage silencieux** (comme notre `--seed`) ; `max_jobs_per_run` ; **IA de secours seulement si l'analyse du tableau échoue** ; tourne dans GitHub Actions, état sur une branche |
| [tarikanders/alternabot](https://github.com/tarikanders/alternabot) | 1 | 2026-11 | MIT | **API La bonne alternance** + Google Maps + Google Jobs (SerpAPI) | client LBA propre (`/api/job/v1/search`, codes ROME, lat/lon, rayon 10/30/60/100 km) ; lit les **réponses** dans Gmail (entretien, refus…) ; commande `verifier` qui contrôle la config ; envoie aussi des candidatures (voir « À éviter ») |
| [czM000/JobBot](https://github.com/czM000/JobBot) | 1 | 2026-07 | MIT | JobSpy (scraping) + **API La bonne alternance** | tableau de bord web local, statuts Intéressé / Postulé / Ignoré, autocomplétion des villes (geo.api.gouv.fr) |
| [speedyapply/JobSpy](https://github.com/speedyapply/JobSpy) | 4 733 | 2026-11 | MIT | **scraping** LinkedIn, Indeed, Glassdoor… et **HelloWork** | la bibliothèque que presque tous les autres utilisent ; proxies pour contourner les blocages |
| [DaKheera47/job-ops](https://github.com/DaKheera47/job-ops) | 4 139 | 2026-10 | non précisée | scraping 10+ sites | score IA 0–100, CV adapté par offre, **suivi des réponses dans Gmail** |
| [Gsync/jobsync](https://github.com/Gsync/jobsync) | 1 526 | 2026-11 | MIT | pages carrière | suivi complet des candidatures (étapes, entretiens, contacts), IA locale (Ollama), serveur MCP |
| [vesaias/JobNavigator](https://github.com/vesaias/JobNavigator) | 188 | 2026-11 | MIT | Playwright + 13 types d'ATS + JobSpy | **clé d'offre lue dans le lien** (30+ systèmes) pour fusionner les copies ; lien **direct employeur** quand il est connu ; Telegram (alertes, digest, **santé des scrapers**) ; jusqu'à 5 comptes (foyer) |
| [Francis1998/agentic-career-search](https://github.com/Francis1998/agentic-career-search) | 102 | 2026-11 | aucune | 119 adaptateurs (ATS, JSON-LD) | **score déterministe expliqué** (termes trouvés, raison) ; lexique d'alias de compétences (`k8s` → `kubernetes`) ; **flux Atom** ; serveur MCP en lecture seule |

## 2. Ce qu'ils ont en plus

| Idée | Qui le fait | Effort | Phase ETAPES |
|---|---|---|---|
| **Clé canonique d'offre tirée du lien** (LinkedIn `jobs/view/{id}`, Indeed `jk`, WTTJ slug, ATS…) : meilleur dédoublonnage et liens propres | career-ops-plugin, JobNavigator | S | 4.6 / 4.7 |
| **Journal de chaque passage par expéditeur** (mails lus, offres extraites, offres écartées) + **alerte si un mail connu donne 0 offre** + message « rétabli » | vagas-tech-pt, job-scout, JobNavigator | M | 2B.13 / 6.4 |
| **Test « canari »** : chaque semaine, rejouer les parsers sur le dernier vrai mail de chaque site et alerter si le format a changé | vagas-tech-pt | S | 6.4 |
| **Score 0–100** au lieu de « gardé / rejeté + ⭐ » : paliers de mots-clés (essentiel / fort / faible), organisations cibles (ONG, fondations pour stage-asso), « dealbreakers » ; messages triés par score, avec les termes trouvés | job-scout, agentic-career-search | M | 7.6 |
| **Digest** : un seul message Discord par passage et par profil quand il y a beaucoup d'offres (utile pour les alertes larges de stage-asso) | job-scout, JobOpeningNotifier, vagas-tech-pt | S | 2B.14 / 7 |
| **Source API La bonne alternance** : `GET /api/job/v1/search?romes=…&latitude=…&longitude=…&radius=30`, en-tête `Authorization: Bearer <jeton>` | alternabot, JobBot | S | 2B.10c |
| **Lexique d'alias** pour les mots-clés (`js` → `javascript`, `chargé·e` → `chargé`, `ESS` → `économie sociale et solidaire`) au lieu de regex écrites à la main | agentic-career-search | S | 7.3 |
| **Commande `verifier`** : contrôle `.env`, webhooks, IMAP et `profiles.yaml`, et dit quoi corriger | alternabot | S | 3.3 |
| **Accès Gmail en lecture seule** par OAuth (`gmail.readonly`) au lieu d'un mot de passe d'application (qui donne un accès complet à la boîte) | career-ops-plugin | M | 6 (sécurité) |
| **Offres modifiées** (pas seulement nouvelles) signalées dans le digest | job-hunt-tracker | S | 7 |
| **Suivi des réponses** : lire dans la boîte de chaque ami les réponses des recruteurs (entretien, refus) | job-ops, alternabot, JobNavigator | L | 7.5 |
| **API JSON publiques des ATS** (Greenhouse, Lever…) pour les entreprises cibles : ce sont des API officielles, pas du scraping | job-hunt-tracker, JobNavigator | M | 5.4 |
| **Flux Atom / RSS de sortie** par profil (un ami peut s'abonner sans Discord) | agentic-career-search | S | 7 |

## 3. Ce qu'ils font différemment

| Leur choix | Le mien | Avantages de leur choix | Inconvénients |
|---|---|---|---|
| Scraping direct (JobSpy) | alertes e-mail + API | plus de volume, filtres fins, description complète | contraire aux CGU, casse souvent, proxies, risque de blocage |
| Tri par LLM (Gemini, Claude…) | regex + ⭐ | comprend le contexte (« stage gratifié », « début avril ») | coût, latence, résultats non reproductibles, données envoyées à un tiers |
| Interface web / tableau de bord | YAML + Discord | réglages sans éditer un fichier, suivi des statuts | beaucoup plus de code et un serveur à exposer |
| Google Sheet comme base | SQLite | partage facile avec les amis | dépend de Google, moins testable |
| GitHub Actions (état sur une branche) | systemd sur une machine | gratuit, rien à héberger | les secrets IMAP sont chez GitHub ; mails relus toutes les N minutes depuis l'extérieur |
| Un message par jour (digest) | un message par offre | moins de bruit | moins réactif |

## 4. Ce que mon projet fait déjà mieux

- **Aucun scraping** : seulement des alertes e-mail, des RSS et des API officielles. Presque tous les autres scrapent.
- **Protection de l'adresse de la boîte** dans les liens publiés (en clair, sans points, %-encodée, base64) : aucun projet vu ne le fait.
- **Plusieurs personnes, un salon chacune**, avec un seul passage de collecte. Seuls JobNavigator (comptes) et job-scout (`--config`) en approchent.
- **Raison du rejet affichée** en `--dry-run --profil` : rare ailleurs (agentic-career-search seulement).
- **Contrats français** (alternance, stage) et règles propres au stage (durée, gratification, date de début) : absent de tous les projets anglophones.
- Dédoublonnage entre sources par empreinte, et des tests sur de vrais mails.

## 5. À éviter (même si c'est populaire)

- **JobSpy et tout scraping** de LinkedIn, Indeed, Glassdoor… JobSpy scrape **maintenant aussi HelloWork** : ne pas l'utiliser, même pour « compléter ».
- **Proxies pour contourner les blocages** (JobSpy).
- **Candidatures automatiques** et mails envoyés au nom des amis (alternabot, LinkedIn auto-apply) : hors du périmètre du bot, et risqué.
- **Suivre les liens de suivi** pour trouver le lien direct de l'employeur (JobNavigator) : ouvrir un lien de suivi HelloWork ou Indeed dit au site qu'on a cliqué, avec l'adresse de la boîte. On continue à **décoder** les liens sans les ouvrir.
- **Clés d'API stockées dans une interface web** ou une base (jobsync les chiffre, mais c'est une surface de plus) : rester sur `.env`.
- **API exposée sur Internet** (FastAPI sur render.com, roshani01) pour un usage entre amis.

## 6. Mon top 5 (rapport intérêt / effort)

1. **Clé canonique d'offre par site** (S) : `linkedin.com/jobs/view/{id}`, `indeed …viewjob?jk=`, slug WTTJ, id makesense. Elle sert de `source_id` stable et de lien propre ; à intégrer au parser générique (4.6) avant d'écrire les parsers LinkedIn et WTTJ.
2. **Santé des sources** (M) : une table `runs` (expéditeur, mails, offres, écartées, date). Alerte dans `#bot-logs` si un expéditeur connu est muet depuis 48 h ou si un mail donne 0 offre, puis message « rétabli ». C'est l'étape 2B.13, rendue concrète, et elle couvre les alertes qui expirent (Les Jeudis) ou disparaissent (WTTJ).
3. **Source API La bonne alternance** (S) : le schéma est connu grâce à alternabot (MIT, réutilisable en citant la licence). Codes ROME à choisir pour la data, recherche autour de Lille et de Paris, rayon 30 km.
4. **Digest par profil** (S) : au-delà de N offres dans un passage, un seul message Discord récapitulatif au lieu de N messages. Indispensable avec les alertes larges de stage-asso (Jobs that make sense sans mot-clé).
5. **Score 0–100 expliqué** (M) : remplacer « gardé + ⭐ » par un score (paliers de mots-clés + organisations cibles ESS / ONG pour stage-asso + bonus Angular / Java / Spring pour dev), afficher les termes trouvés, trier les messages. Un seuil par profil dans `profiles.yaml`.
