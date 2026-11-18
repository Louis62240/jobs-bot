# Reprise de session : état du bot au 2026-11-18

> À coller en début de nouvelle session : « Lis CLAUDE.md, REPRISE.md et ETAPES.md, puis on reprend. »

## Ce que fait le bot
Lit les alertes e-mail (Gmail dédiée, IMAP, relit les 3 derniers jours) → détecte ville + contrat → filtre **par profil** (`profiles.yaml`) → score 0–100 → dédoublonne (SQLite, par profil + empreinte titre/entreprise/ville + lien canonique) → Discord, un salon par profil (récap si ≥ 8 offres).

3 profils : `alternance-data` (#offres-data), `dev` junior Angular/Java CDI/CDD (#dev), `stage-asso` RSE/ESS/public, stage avril 2027 (#stage-asso).

## Où on en est
- **En prod** sur le VPS louishanquiez.fr : `/home/ubuntu/bot-offres-data`, service `perso-jobbot` + timer toutes les 15 min depuis le 2026-11-15. Mise à jour : `./deploy/deploy.sh`.
- **Tests** : 270 OK, ruff OK (2026-11-18).
- **Parsers e-mail** : Indeed, HelloWork, LinkedIn, Jobs that make sense, Coordination SUD, Les Jeudis (2026-11-18 ; `links.py` nettoyage des liens, `canonical.py` id depuis le lien). Free-Work, WTTJ, APEC : pas encore de parser (pas encore de mails d'alerte).
- **Pages carrières** (2026-11-18) : 28 entreprises (`config.yaml` → `carrieres`), API publiques Greenhouse/Lever/Ashby/Workable/Recruitee/SmartRecruiters, 1 passage/heure. Le profil `alternance-data` cherche aussi dans l'annonce complète (`fiche:` : SQL, métiers et outils data) et fait confiance aux alertes data/SQL des sites (`alertes_fiche:`).
- **Alertes créées** : Indeed, HelloWork, LinkedIn (16), Jobs that make sense, Coordination SUD, Les Jeudis (⚠️ expirent vers le 2026-12-15).
- **Page stages** : https://louishanquiez.fr/stages/ (dépôt wii-portfolio, commit `ca4c314`), 57 stages triés à la main depuis 525 ; liste statique, non branchée au bot.
- **Git** : branche `main`, remote `origin` = git@github.com:Louis62240/jobs-bot.git (SSH, **dépôt public**), à jour au 2026-11-18. Les `.eml` de `tests/fixtures/` ne sont jamais commités.

## À faire, par priorité
1. 🚀 **Déployer les nouveaux parsers** (`./deploy/deploy.sh`) : le 1er passage enverra d'un coup les offres LinkedIn / makesense / Les Jeudis des 3 derniers jours (en récap si ≥ 8).
2. 🧑 **Coordination SUD** : ses offres n'indiquent que « Europe, France » → écartées sauf si le titre cite Paris/Lille. Décider : les garder toutes (ville inconnue) pour stage-asso, ou laisser ainsi. Parser générique à faire quand Free-Work / APEC / JobTeaser enverront des alertes.
3. 💻 **Durée / date de début des stages** : les mails ne la donnent pas, des stages de 6 mois arrivent sur #stage-asso. Idée validée en discussion : ouvrir l'annonce pour lire début/durée/gratification avant d'envoyer (attention à la règle « pas de scraping », à rediscuter).
4. 💻 **2B.12** : `--dry-run --profil <id>` sur les nouveaux mails, ajuster `profiles.yaml`.
5. 🧑 **#bot-logs** : créer le salon + webhook → `DISCORD_LOGS_WEBHOOK_URL` (vide dans `.env`, les alertes de `health.py` ne partent que dans le journal).
6. 🧑 **La bonne alternance** : cliquer le lien reçu dans la boîte, générer la clé → `LBA_API_KEY` dans `.env`, puis `sources.labonnealternance: true` et `--dry-run --profil alternance-data` (code déjà écrit et testé).
7. 🧑 Alertes à faire à la main : APEC, PASS, Carenews (mot de passe/CAPTCHA), Free-Work (formulaire perso), JobTeaser Dauphine (par l'amie, voir INSTRUCTIONS_ALERTES.md), WTTJ (alertes indisponibles, réessayer).
8. 💻 **2B.14** récap hebdo `--recap` ; Phase 6 (retries HTTP, ping healthchecks.io, purge > 90 j, sauvegarde `jobs.db`).
9. 💻 Option : brancher la page /stages sur les données du bot (mise à jour auto au lieu d'une liste figée).

## Commandes utiles
```bash
uv run pytest -q && uv run ruff check .
uv run jobbot --dry-run --profil stage-asso                    # montre aussi les rejets
./deploy/deploy.sh                                            # pousse le code sur le VPS
ssh <vps> 'journalctl -u perso-jobbot.service -n 50'
```

## Rappels des règles
Pas de scraping LinkedIn/Indeed/WTTJ/HelloWork (exception ponctuelle validée pour la liste /stages). Secrets uniquement dans `.env`. Toujours `--dry-run` avant un vrai envoi. Cocher `ETAPES.md` au fur et à mesure. France Travail retiré volontairement : ne pas le remettre.

Session d'origine : `claude --resume 6b1f5f4b-471b-466b-985e-c541a2bcffaf` (dans ~/bot-offres-data).
