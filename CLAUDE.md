# Bot offres d'emploi multi-profils — Lille + Paris

Bot Python qui lit les alertes e-mail (Indeed, HelloWork…) d'une boîte dédiée et envoie chaque nouvelle offre pertinente sur Discord, **un salon par profil** (3 amis : alternance data/SQL, dev junior Angular/Java, stage asso/ESS). Les profils se règlent dans `profiles.yaml` (contrats, villes, mots-clés, exclusions, ⭐), les villes et sources dans `config.yaml`.

## Documents de référence
- `PLAN.md` — architecture, sources, extraits de code, déploiement (source de vérité technique)
- `PROMPT_MULTI_PROFILS.md` — cahier des charges du passage au multi-profils (décisions prises)
- `ETAPES.md` — liste des étapes à cocher, dans l'ordre. **Cocher les cases au fur et à mesure.**

## Règles de travail
- Avancer **phase par phase** selon `ETAPES.md` ; ne pas passer à la suivante tant que la précédente ne marche pas.
- Python 3.12+, gestion des dépendances avec `uv`, code dans `src/jobbot/`, tests dans `tests/`.
- Secrets uniquement dans `.env` (jamais commité, jamais affiché en entier dans le terminal).
- Pas de scraping de LinkedIn / Indeed / WTTJ / HelloWork : uniquement API officielles et alertes e-mail (IMAP).
- Chaque module a ses tests `pytest` ; lancer `uv run pytest -q` et `uv run ruff check .` avant de dire qu'une étape est finie.
- Toujours tester avec `--dry-run` avant d'envoyer de vraies notifications.
- Répondre en français.
