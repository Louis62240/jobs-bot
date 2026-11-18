Améliore l'interface de la page https://louishanquiez.fr/stages/ pour qu'elle soit la meilleure
possible pour son usage réel. Fichiers : ~/Workspace/Personnel/wii-portfolio/stages/
(index.html, style.css, app.js, offres.js). Réponds en français.

Lis d'abord : le README de wii-portfolio, /kit/kit.css et /kit/index.html (les composants du site),
la page /veille/ (même famille de page), puis les 4 fichiers de stages/ et, dans ~/bot-offres-data,
le bloc `stage-asso` de profiles.yaml (ce qu'elle cherche).

## Pour qui, pour quoi
- Une seule utilisatrice : une étudiante en master « Politiques d'entreprises » (Paris-Dauphine),
  qui cherche un **stage de 2 à 4 mois, début avril 2027, gratifié**, à Paris ou Lille, en RSE /
  développement durable (priorité), diversité-inclusion, mécénat, relations sociales / QVT,
  associations, ESS ou secteur public. Pas de conseil, d'études ni de finance.
- Elle ouvrira surtout la page **sur son téléphone**, plusieurs fois par semaine, quelques
  minutes à chaque fois. Elle n'est pas technique.
- Ce qu'elle doit pouvoir faire, par ordre d'importance :
  1. voir en quelques secondes **ce qui est nouveau** depuis sa dernière visite ;
  2. **trier vite** chaque offre : « M'intéresse », « Pas pour moi », « J'ai postulé » ;
  3. vérifier pour une offre les 3 critères qu'on ne connaît pas d'avance (durée, date de début,
     gratification) et noter ce qu'elle a trouvé ;
  4. retrouver ses offres « M'intéresse » et « Postulé » (avec la date de candidature) ;
  5. filtrer simplement : ville (Paris / Lille), RSE ★, type d'employeur
     (entreprise / association-ESS / public).

## Données disponibles (offres.js)
`window.STAGES = { date, meilleures: [...], autres: [...], liens: [[site, libellé, url]] }`.
Chaque offre : `titre, entreprise, lieu, url, etoile (bool), salaire, note, site, pourquoi (libellés)`.
Il n'y a **ni description, ni durée, ni date de début** : on ne peut pas les afficher, seulement
aider à les vérifier. L'`url` est l'identifiant stable d'une offre.
offres.js sera bientôt **régénéré chaque jour par le bot** : ne change pas sa forme sans
l'écrire clairement dans ta réponse (nouveaux champs utiles, par exemple `vu_le` pour
« nouveau », ou `type_employeur`), afin qu'on adapte le générateur. Si un champ manque, déduis-le
côté page quand c'est fiable (le type d'employeur à partir de `pourquoi` et du nom), sinon propose-le.

## Contraintes
- **Même style que le site** : le kit `/kit/kit.css` (couleurs, cartes, k-btn, k-chip, k-check,
  k-input), aucun autre framework. Pas de build, pas de dépendance, pas de CDN : HTML/CSS/JS à
  ouvrir tel quel, comme les autres pages du site. Le déploiement lance `node --check` sur les JS.
- **Mobile d'abord** (≈ 380 px), utilisable au pouce ; doit aussi bien rendre sur ordinateur.
- **Pas de serveur pour l'instant** : son état (statuts, notes, dernière visite) est gardé en
  `localStorage`, avec un `try/catch` et une page qui marche quand même sans. Dis dans ta réponse
  ce qui serait gagné avec une synchronisation entre appareils, sans la coder.
- Page **non indexée** (`noindex`), hors menu et hors sitemap : garde ça.
- Accessibilité : contraste du kit, focus visible, vrais boutons et libellés, `prefers-reduced-motion`.
- Textes en français simple, tutoiement, sans jargon (« score », « regex » interdits à l'écran).

## Méthode
1. Commence par **3 parcours concrets** (ex. « mardi soir, 5 minutes, sur le téléphone ») et ce que
   l'interface actuelle fait mal pour chacun. Court.
2. Propose **2 maquettes** très différentes en ASCII (ex. liste + statuts vs. pile de cartes à
   trier une par une), avec leurs avantages ; choisis-en une et dis pourquoi. N'attends pas ma
   réponse pour continuer.
3. Code la version choisie dans les fichiers de stages/ ; garde offres.js inchangé.
4. Vérifie : `node --check` sur les JS ; ouvre la page en local ou sur une copie de test, en
   largeur téléphone et ordinateur ; essaie chaque parcours ; vide le localStorage et vérifie que
   rien ne casse.
5. **Ne pousse rien et ne déploie rien** : montre-moi le résultat (captures) et la liste des
   changements. Je déciderai de la mise en ligne (copie sur le serveur + commit dans wii-portfolio).
