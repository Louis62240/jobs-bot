On fait évoluer le bot d'offres (dossier ~/bot-offres-data) : il passe d'un seul
profil « Data/SQL Lille + Paris » à un bot **multi-profils**, pour aider 3 amis
à trouver un job, une alternance ou un stage.

Lis d'abord CLAUDE.md, ETAPES.md, PLAN.md, config.yaml et src/jobbot/.

## Ce qui existe déjà (ne pas casser)
- Source unique : alertes e-mail lues en IMAP (boîte dédiée, dossier INBOX).
  Parsers Indeed + HelloWork dans src/jobbot/sources/email_alerts/. Le bot relit les
  N derniers jours sans marquer les mails comme lus ; c'est SQLite qui dédoublonne.
- Filtre regex (ville + mots-clés + exclusions), stockage SQLite, envoi Discord,
  main.py avec --dry-run / --seed. 44 tests verts.
- France Travail a été retiré volontairement : ne pas le remettre.
- Acquis à garder : on ne publie jamais un lien de suivi qui contient l'adresse
  de la boîte (HelloWork : on décode la vraie URL), et httpx ne doit jamais
  journaliser l'URL du webhook.

## Les 3 profils
**Villes : Lille et Paris pour les 3 profils**, avec la même définition que le
config.yaml actuel (métropole lilloise + Paris + La Défense, Puteaux, Nanterre…).
Les villes restent un réglage propre à chaque profil, pour pouvoir changer plus tard.

1. **Alternance data/SQL** : c'est **l'actuel profil « Data/SQL Lille + Paris »**,
   qui devient ce profil. On reprend ses regex de config.yaml (`\bdata(?!base)`,
   `analytics engineer`, `sql`, exclusion « data center ») et on ajoute le filtre
   de contrat. Contrat : alternance / apprentissage uniquement.
2. **Développeur junior, profil Angular / Java** : sorti de master en décembre 2025,
   donc moins d'un an d'expérience. Garder toutes les offres de développeur
   (développeur, developer, software engineer, full stack, back-end, front-end…),
   mais **mettre en avant** celles qui citent Angular, Java ou Spring (badge ⭐ dans
   le message). Exclure les postes senior, lead, principal, architecte, staff,
   et ceux qui demandent 5 ans d'expérience ou plus.
   Contrat : **CDI ou CDD** (pas de freelance, ni de stage, ni d'alternance).
3. **Stage, Master de sociologie (Paris-Dauphine)** : stage dans une association,
   une ONG, une fondation, l'ESS, le public ou un think tank. Missions : chargé·e
   d'études, de mission ou de projet, enquête, recherche, évaluation d'impact,
   plaidoyer, coordination…
   Contrat : stage uniquement, **début vers avril 2027**. Les offres de stage pour
   le printemps 2027 paraissent surtout entre novembre 2026 et mars 2027 : le
   profil doit être actif dès maintenant. Écarter les stages qui commencent
   clairement avant mars 2027 (« dès que possible », « janvier 2027 ») quand la
   date apparaît dans le titre.
   **Durée : 2 à 4 mois.** Écarter les stages de 5 ou 6 mois quand la durée est
   indiquée. Si elle n'est pas indiquée, garder l'offre.
   **Gratification obligatoire.** Écarter les offres qui disent « non gratifié »,
   « non rémunéré » ou « bénévole ». Rappel légal : la gratification n'est
   obligatoire qu'au-delà de 2 mois de stage. Un stage de 2 mois pile peut donc
   être non payé : il faut l'écarter s'il ne mentionne aucune gratification.

## Ce que je veux
- **Tout se règle dans un fichier `profiles.yaml`, sans toucher au code.** Pour
  chaque profil :
  `id`, `nom`, `description` (texte libre qui décrit la recherche),
  `contrats`, `villes` (+ option télétravail), `inclure` / `exclure` (regex),
  `secteurs` (optionnel), et la destination des notifications, donnée par le nom
  d'une variable de .env (ex. `DISCORD_WEBHOOK_PROFIL_DEV`). Aucune URL secrète
  dans le YAML.
- Ajouter un profil = ajouter un bloc YAML + créer ses alertes e-mail. Rien d'autre.
- On collecte **une fois**, puis on filtre **pour chaque profil**. Une même offre
  peut aller à plusieurs profils. Le dédoublonnage se fait **par profil**
  (clé = profil + offre).
- **Contrat** : le détecter à partir du champ fourni par la source (HelloWork le
  donne), sinon à partir du titre (stage, stagiaire, intern, alternance, alternant,
  apprenti, CDD, freelance). Si on ne sait pas : réglage par profil
  (`contrat_inconnu: garder | rejeter`).
- **Secteur associatif** (profil 3) : le titre ne suffit pas. Il faut s'appuyer sur
  des sources spécialisées (voir ci-dessous) et sur une liste d'organisations ou
  de mots-clés de secteur.
- **Notifications** : **un seul serveur Discord commun**, avec un salon et un
  webhook par profil. L'actuel `#offres-data` (DISCORD_WEBHOOK_URL) devient le
  salon du profil 1. On pourra passer plus tard à un serveur par ami : il suffira
  de changer le webhook dans .env.
  ntfy par profil en option. Le message indique le profil, le contrat, le lieu et
  le lien direct.
- `--dry-run --profil <id>` : afficher les offres retenues **et rejetées** (avec la
  raison) pour un seul profil, afin de régler ses regex.
- `--seed` par profil, pour qu'un nouveau profil ne reçoive pas tout l'historique.
- **Migration** : il n'y a pas de 4e profil. config.yaml (villes, mots-clés) est
  absorbé par profiles.yaml, et le profil Data/SQL devient le profil 1. La base
  data/jobs.db contient 50 offres amorcées (tous contrats confondus) : les
  rattacher au profil 1 pendant la migration pour qu'il ne les reçoive pas une
  seconde fois. Les profils 2 et 3 partent de zéro et passent par --seed.

## Améliorations retenues (à faire après le multi-profils)
- **Alerte panne** dans `#bot-logs` (DISCORD_LOGS_WEBHOOK_URL, encore vide : faire
  d'abord les étapes 1.7–1.8). Envoyer un message si :
  - une source (expéditeur) n'a envoyé aucun mail depuis 48 h ;
  - un mail d'un expéditeur connu donne 0 offre (son HTML a sans doute changé) ;
  - un envoi Discord échoue, ou le bot plante.
  Une seule alerte par problème (pas de spam à chaque passage), puis un message
  « rétabli » quand le problème disparaît. Stocker l'état dans SQLite.
- **Récap hebdo** : chaque lundi matin, un message par salon de profil avec le
  nombre d'offres de la semaine, les entreprises qui en ont publié le plus et les
  offres ⭐ de la semaine (profil 2). Commande `jobbot --recap` lancée par un
  timer séparé, testable avec `--dry-run`.
- Écartées pour l'instant : tri par IA, réactions 👍👎, commandes Discord
  (ces deux dernières demandent un vrai bot Discord à la place des webhooks).

## Sources à ajouter (alertes e-mail, toujours sans scraping)
- **Parser générique** (étape 4.6 de ETAPES.md) : indispensable, car le profil 3
  dépendra de sites variés.
- À étudier, puis à me proposer, avec la façon de créer l'alerte sur la boîte
  dédiée : JobTeaser (Dauphine y a un espace carrière), Welcome to the Jungle,
  Jobs that make sense, Coordination SUD, Ressources Solidaires, APEC, LinkedIn,
  et les alertes HelloWork / Indeed par profil.
  Si un site propose un flux RSS officiel, une source RSS est acceptable.

## Décisions déjà prises (2026-11-15)
- Villes : Lille + Paris pour les 3 profils.
- Profil 2 : toutes les offres de développeur, avec ⭐ pour Angular / Java / Spring.
  CDI ou CDD.
- Profil 3 : stage de 2 à 4 mois, début vers avril 2027, gratification obligatoire.
- Discord : un serveur commun, un salon par profil.
- Pas de 4e profil : Data/SQL = profil 1 (alternance).

## Seule question encore ouverte
- Les amis modifient-ils eux-mêmes leur profil (fichier YAML partagé, ou plus tard
  une commande Discord) ? Ce n'est pas bloquant : commencer avec le YAML édité par moi.

## Méthode
1. Mettre à jour PLAN.md (architecture
   multi-profils) et ajouter à ETAPES.md une nouvelle phase « Multi-profils »,
   avec des étapes à cocher (🧑 / 💻 / 🚀). Inclure les étapes manuelles : créer
   les salons `#alternance-data`, `#dev`, `#stage-asso` et leurs webhooks, et
   créer les alertes de chaque profil sur la boîte dédiée.
2. Coder dans cet ordre : profiles.yaml + chargement/validation → filtre par
   profil (contrat, ville, mots-clés) → stockage par profil → notification par
   profil → main (--profil) → parser générique → nouvelles sources →
   alerte panne → récap hebdo.
3. Pour chaque profil, faire un --dry-run sur les vrais mails, me montrer les offres
   retenues et rejetées, ajuster, puis --seed, puis un envoi réel.

## Règles (inchangées)
Avancer étape par étape et cocher ETAPES.md au fur et à mesure.
`uv run pytest -q` et `uv run ruff check .` doivent passer avant de dire qu'une
étape est finie. Toujours --dry-run avant un vrai envoi. Ne jamais afficher de
secrets : ni valeurs de .env, ni URL de webhook, ni adresse de la boîte dans les
liens publiés. Ne rien commiter sans me demander.
