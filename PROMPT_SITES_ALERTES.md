On ajoute des sites d'offres au bot (dossier ~/bot-offres-data). Je veux que tu
fasses un maximum de choses toi-même, y compris dans le navigateur. Tu ne
m'interromps que pour ce que tu ne peux pas faire (voir « Quand t'arrêter »).

Lis d'abord CLAUDE.md, ETAPES.md (phase 2B), PROMPT_MULTI_PROFILS.md, profiles.yaml
et src/jobbot/sources/email_alerts/.

## Contexte
- Le bot lit les alertes e-mail d'une **boîte Gmail dédiée** (IMAP_USER dans .env,
  dossier INBOX). Il gère déjà Indeed et HelloWork. Les mails des autres expéditeurs
  sont ignorés sans être supprimés : rien n'est perdu.
- Il y a 3 profils, un salon Discord chacun : `alternance-data`, `dev` (junior
  Angular/Java, CDI/CDD), `stage-asso` (stage de 2 à 4 mois en asso/ESS, début
  avril 2027, gratifié). Lille + Paris pour tous.
- **Priorité : le profil stage-asso.** Les stages d'avril se publient maintenant.

## Étape 1 : vérifier les sites (recherche web)
Pour chaque site ci-dessous, vérifie s'il propose des alertes e-mail, un flux RSS
officiel ou une API officielle gratuite, et à quelles conditions (compte, limites).
Présente-moi ensuite un tableau, puis continue sans attendre ma réponse.
- Les 3 profils : LinkedIn, Welcome to the Jungle.
- alternance-data : La bonne alternance (vérifier s'il y a une API officielle),
  APEC.
- dev : Free-Work, APEC (jeunes diplômés), Les Jeudis.
- stage-asso : Jobs that make sense, Ressources Solidaires, Coordination SUD,
  Carenews, JobTeaser (Paris-Dauphine), Animafac, PASS (stages de la fonction
  publique).
- Ajoute 2 ou 3 autres sites pertinents pour l'ESS ou les ONG si tu en trouves.

## Étape 2 : créer les alertes (Claude in Chrome)
- Charge le skill du navigateur avant de commencer. Travaille dans un nouvel onglet.
- **Compte** : toujours celui de la boîte dédiée. Utilise de préférence « Continuer
  avec Google » si cette boîte est connectée dans Chrome. Sinon, demande-moi de me
  connecter ou de créer le compte moi-même : **tu ne choisis ni ne stockes aucun mot
  de passe**.
- **Codes de vérification** : lis-les dans la boîte dédiée via IMAP (en lecture
  seule, sans les afficher en entier), puis saisis-les.
- **HelloWork et Indeed** : les comptes existent déjà. Ajoute seulement les
  alertes dev et stage-asso.
- **Alertes à créer**, chacune sur Lille et sur Paris, en fréquence quotidienne :
  - alternance-data : « alternance data analyst », « alternance data engineer »,
    « alternance SQL », « alternance BI » (contrat alternance si le filtre existe)
  - dev : « développeur », « développeur java », « développeur angular »,
    « développeur full stack » (CDI + CDD, débutant / junior si le filtre existe)
  - stage-asso : « stage chargé d'études », « stage chargé de mission »,
    « stage sociologie », « stage association », « stage ESS », « stage plaidoyer »
    (date de début avril 2027 si le filtre existe)
  Si un site limite le nombre d'alertes, regroupe les mots-clés (« data OR sql »)
  ou garde les plus importantes, et note ce que tu as laissé de côté.
- Coche au fur et à mesure dans ETAPES.md (2B.9, 2B.10, et une ligne par site).
  Tiens à jour dans ETAPES.md un tableau site × profil × alertes créées.

## Ce que je fais moi-même (prépare-moi les instructions exactes)
- **LinkedIn** : je crée moi-même le compte et les alertes. L'automatisation peut
  faire bloquer le compte, et LinkedIn demande souvent un téléphone.
- **JobTeaser Dauphine** : c'est le compte étudiant de mon ami. Rédige-lui un
  message court qui explique comment créer ses alertes, puis comment transférer
  automatiquement les mails JobTeaser vers la boîte dédiée (Gmail → Transfert, plus
  un filtre). Quand il le fera, récupère dans la boîte dédiée le code de
  confirmation du transfert et donne-le-moi.

## Quand t'arrêter et me demander
CAPTCHA, numéro de téléphone, conditions à accepter qui engagent plus qu'un compte
gratuit, offre payante, connexion qui demande un mot de passe, site qui bloque
l'automatisation. Dans ces cas, ne contourne rien : passe au site suivant et fais-moi
la liste à la fin.

## Étape 3 : attendre les mails, puis coder
- Les alertes mettent souvent 1 jour à envoyer leur premier mail. Si la boîte n'a
  encore rien reçu, dis-le-moi et propose de revérifier plus tard (/loop ou une
  tâche programmée) au lieu de coder à l'aveugle.
- Pour chaque nouveau site qui a envoyé des mails :
  1. enregistrer 2 ou 3 vrais mails dans `tests/fixtures/` (fichiers ignorés par git) ;
  2. écrire un **parser dédié** pour les sites à fort volume (LinkedIn, WTTJ,
     APEC…). Pour les autres, utiliser le **parser générique** (étape 4.6) : liens
     qui ressemblent à une offre, URL nettoyée des paramètres de suivi ;
  3. vérifier qu'**aucun lien publié ne contient l'adresse de la boîte**, ni
     encodée ni en clair (voir comment c'est fait pour HelloWork) ;
  4. écrire les tests, puis `--dry-run --profil <id>` pour chaque profil. Me montrer
     les offres retenues et rejetées, ajuster profiles.yaml, puis faire l'envoi réel.
- Si un site a un flux RSS ou une API officielle (par exemple La bonne alternance),
  écrire une source dédiée dans `src/jobbot/sources/`, avec ses tests.

## Règles (inchangées)
Avancer étape par étape et cocher ETAPES.md au fur et à mesure.
`uv run pytest -q` et `uv run ruff check .` doivent passer avant de dire qu'une
étape est finie. Toujours `--dry-run` avant un vrai envoi. Pas de scraping : on
utilise uniquement les alertes e-mail, les flux RSS officiels et les API officielles.
Ne jamais afficher de secrets (.env, webhooks, codes, adresse de la boîte dans les
liens). Ne rien commiter sans me demander. Répondre en français.
