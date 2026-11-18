Fais une veille sur GitHub des projets proches de mon bot d'offres d'emploi
(dossier ~/bot-offres-data), puis dis-moi ce qu'ils ont en plus ou de différent.

Lis d'abord CLAUDE.md, ETAPES.md, PLAN.md et src/jobbot/ pour connaître le projet.

## Mon projet en bref (pour comparer)
- Python 3.12, `uv`, tests `pytest`, `ruff`.
- Sources : **alertes e-mail lues en IMAP** (boîte Gmail dédiée, relue sur N jours sans
  marquer « lu ») avec un parser par site (Indeed, HelloWork), plus un parser générique à venir.
  Pas de scraping : uniquement alertes e-mail, flux RSS officiels et API officielles.
- **Multi-profils** dans `profiles.yaml` : villes, contrats, regex inclure / exclure,
  ⭐ mise en avant, un salon Discord (webhook) par profil.
- Détection du contrat (titre, puis champ source), filtre par ville (alias), raison du rejet
  affichée en `--dry-run --profil`.
- SQLite : dédoublonnage par profil + empreinte titre / entreprise / ville entre sources.
- Liens nettoyés : paramètres de suivi retirés, jamais l'adresse de la boîte (clair, sans points,
  %-encodée, base64).
- Prévu : alerte panne dans `#bot-logs`, récap hebdo, source API La bonne alternance,
  déploiement systemd toutes les 15 min.

## Ce que je veux
1. **Trouver 10 à 15 projets pertinents.** Utilise `gh search repos` / `gh search code`
   (et la recherche web si besoin). Pistes de recherche, en anglais et en français :
   - « job alert email parser », « linkedin job alerts imap », « indeed email alert parser »,
     « gmail job alerts discord », « job alerts discord webhook », « job bot telegram »
   - « offres d'emploi bot », « alternance bot », « welcometothejungle », « hellowork »,
     « la bonne alternance api », « france travail api offres »
   - « job tracker self-hosted », « job aggregator python », « jobspy »
   Garde en priorité : actifs depuis moins de 2 ans, au moins quelques étoiles, du code lisible.
   Prends aussi 2 ou 3 projets très populaires même s'ils scrapent (pour voir leurs idées).
2. **Pour chaque projet**, lis le README et survole le code (via `gh api` ou la page web,
   **sans cloner ni exécuter quoi que ce soit**) et note :
   - sources (e-mail / RSS / API / scraping), et comment ils lisent les mails s'ils le font ;
   - filtrage et tri (regex, score, IA / LLM, mots-clés pondérés, salaire, télétravail…) ;
   - dédoublonnage, stockage, suivi des candidatures ;
   - notifications (Discord, Telegram, Slack, ntfy, e-mail récap…) et leur mise en forme ;
   - configuration (YAML, interface web, commandes de bot) ;
   - fiabilité : nouvelles tentatives, surveillance, alerte quand un parser casse, tests ;
   - déploiement (cron, systemd, Docker, GitHub Actions) ;
   - licence (pour savoir si on peut reprendre du code).
3. **Me rendre un fichier `VEILLE_GITHUB.md`** avec :
   - un tableau : projet (lien) · étoiles · dernière activité · licence · sources · points forts ;
   - **« Ce qu'ils ont en plus »** : idées absentes de mon projet, chacune avec
     le ou les projets qui la font, l'effort estimé (S / M / L) et la phase d'ETAPES.md concernée ;
   - **« Ce qu'ils font différemment »** : choix d'architecture opposés aux miens, avec avantages
     et inconvénients ;
   - **« Ce que mon projet fait déjà mieux »**, en une courte liste honnête ;
   - **« À éviter »** : ce qui est contraire à mes règles (scraping de LinkedIn / Indeed / WTTJ /
     HelloWork, identifiants stockés en clair, etc.), même si c'est populaire ;
   - pour finir, **ton top 5 des améliorations à faire**, classé par rapport intérêt / effort.

## Règles
- Lecture seule : ne clone pas, n'installe rien, n'exécute aucun code trouvé sur GitHub.
- N'ajoute aucune idée de scraping à mes étapes, même si un projet le fait.
- Si tu proposes de reprendre du code, vérifie que la licence le permet et dis-le.
- N'envoie aucune information privée dans les recherches (adresse de la boîte, noms des amis,
  contenu de .env) : uniquement des mots-clés génériques.
- Ne modifie pas le code du projet : seulement créer `VEILLE_GITHUB.md`.
  Je choisirai ensuite ce qu'on ajoute à ETAPES.md.
- Réponds en français.
