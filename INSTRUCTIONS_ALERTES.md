# Alertes à créer à la main (2026-11-15)

Toujours avec la **boîte dédiée** (celle de `IMAP_USER`). Fréquence **quotidienne** partout.
Quand c'est fait, cocher la ligne correspondante dans `ETAPES.md` (2B.10b).

---

## 1. LinkedIn (Louis) : les 3 profils

1. Navigation privée → linkedin.com → « S'inscrire » avec l'adresse de la boîte dédiée
   (ou « Continuer avec Google » en choisissant la boîte dédiée). Téléphone demandé : le tien.
2. Profil minimal (prénom, ville : Paris). Pas besoin de remplir le reste.
3. Pour chaque alerte : onglet **Emplois** → taper les mots-clés et le lieu → **Rechercher** →
   filtres → interrupteur **« Activer l'alerte »** en haut de la liste.
   Puis **Emplois → Préférences → Alertes emploi** : fréquence *Quotidienne*, notification *E-mail*.
4. Alertes (LinkedIn limite à ~20 alertes ; 12 ci-dessous) :

| Profil | Mots-clés | Lieu | Filtres |
|---|---|---|---|
| alternance-data | `alternance (data OR SQL OR BI)` | Paris, Île-de-France | — |
| alternance-data | `alternance (data OR SQL OR BI)` | Lille, Hauts-de-France | — |
| alternance-data | `apprentissage data analyst OR data engineer` | Paris | — |
| alternance-data | `apprentissage data analyst OR data engineer` | Lille | — |
| dev | `développeur` | Paris | Type : Temps plein + CDD ; Niveau : Débutant + Premier emploi |
| dev | `développeur` | Lille | idem |
| dev | `java OR angular OR "full stack"` | Paris | idem |
| dev | `java OR angular OR "full stack"` | Lille | idem |
| stage-asso | `stage ("chargé d'études" OR "chargé de mission" OR sociologie)` | Paris | Type : Stage |
| stage-asso | `stage ("chargé d'études" OR "chargé de mission" OR sociologie)` | Lille | Type : Stage |
| stage-asso | `stage (association OR ESS OR plaidoyer OR ONG)` | Paris | Type : Stage |
| stage-asso | `stage (association OR ESS OR plaidoyer OR ONG)` | Lille | Type : Stage |

5. Dans **Préférences → Communications**, couper les e-mails non liés aux alertes (invitations,
   « personnes que vous connaissez peut-être ») pour ne pas noyer la boîte.

## 2. JobTeaser Dauphine (message à envoyer à ton ami)

> Salut ! Pour le bot qui t'envoie les offres de stage sur Discord, j'aurais besoin de 5 min :
>
> **A. Créer tes alertes JobTeaser** (espace carrière Dauphine) :
> 1. Connecte-toi à JobTeaser via Dauphine → **Offres** → tape `chargé d'études`, type **Stage**,
>    lieu **Paris** (puis refais avec **Lille**) → bouton **« Créer une alerte »**, fréquence quotidienne.
> 2. Pareil avec `chargé de mission`, `sociologie`, `association OR ESS`, `plaidoyer`.
>    Si tu peux, ajoute « Date de début : avril 2027 ».
>
> **B. Transférer automatiquement les mails JobTeaser vers la boîte du bot** (Gmail) :
> 1. Gmail → ⚙️ → **Voir tous les paramètres** → onglet **Transfert et POP/IMAP** →
>    **Ajouter une adresse de transfert** → colle l'adresse que je t'envoie à part → Suivant → Continuer.
>    Gmail envoie un **code de confirmation** à cette adresse : je te le renvoie, tu le saisis au même endroit.
>    ⚠️ Laisse ensuite **« Désactiver le transfert »** coché en haut : on ne transfère pas tout, seulement JobTeaser.
> 2. Barre de recherche Gmail → icône des filtres → **De :** `jobteaser.com` → **Créer un filtre** →
>    coche **« Transférer à »** + l'adresse du bot → **Créer un filtre**.
>
> C'est tout, merci !

(Envoie-lui l'adresse de la boîte dédiée dans un message séparé. Quand il aura fait l'étape B.1,
demande-moi : je lirai le code de confirmation Gmail dans la boîte dédiée et je te le donnerai.)

## 3. Sites où il faut un mot de passe ou une info perso (Louis)

| Site | Blocage | Quoi faire ensuite |
|---|---|---|
| **La bonne alternance (API)** | lien de connexion envoyé dans la boîte dédiée (sans mot de passe) | ouvre la boîte dédiée → mail « Vous avez demandé à recevoir un lien de connexion… » → clique → **Générer une clé d'API** → mets-la dans `.env` : `LBA_API_KEY=...` (ne me la colle pas dans le chat). Usage non lucratif uniquement. |
| **Free-Work** | compte créé, mais fenêtre « Bienvenue » : civilité, prénom, nom | remplis-la (un pseudo suffit), puis dis-le-moi : je crée les alertes « développeur » CDI+CDD × Paris / Lille. Ou toi : rechercher → **Créer une alerte**. |
| **PASS** (stages fonction publique) | mot de passe + CAPTCHA | pass.fonction-publique.gouv.fr → Accès candidat → Créer un compte → recherche **Stage**, région Île-de-France puis Hauts-de-France, domaines « Études / Statistiques », « Politiques publiques », « Social » → **Créer une alerte**. |
| **APEC** | mot de passe (pas de Google) | apec.fr → Mon espace → Créer votre compte → Offres → `développeur` (Paris, puis Lille), Expérience « Débutant » → **Créer une alerte** ; idem `alternance data`. |
| **Carenews** | mot de passe | carenews.com → S'inscrire → Emplois → type **Stage** → **Ajouter une alerte** (quotidienne). |

## 4. À refaire plus tard

- **Welcome to the Jungle** : compte créé (Google), mais les alertes de recherche sont
  « en refonte » côté site. Revérifier vers début décembre : fr/me/alerts.
- **Les Jeudis** : les 3 alertes dev **expirent le ~2026-12-15** → bouton « Renouveler » dans Mes alertes.
