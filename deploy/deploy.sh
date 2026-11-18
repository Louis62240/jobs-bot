#!/usr/bin/env bash
# Déploie le bot sur le VPS (même convention que les autres services perso-*).
#   ./deploy/deploy.sh            code seulement (mise à jour)
#   ./deploy/deploy.sh --premiere code + .env + base SQLite + service/timer (1re installation)
# Le timer n'est (ré)activé qu'avec --premiere ; ensuite il reprend le nouveau code tout seul.
set -euo pipefail
HOST="${JOBBOT_HOST:-ubuntu@51.210.97.104}"
DIR=/home/ubuntu/bot-offres-data
cd "$(dirname "$0")/.."

uv run pytest -q
uv run ruff check .

rsync -az --delete \
  --exclude .env --exclude data/ --exclude .venv/ --exclude .git/ --exclude __pycache__/ \
  --exclude '.ruff_cache/' --exclude '.pytest_cache/' --exclude 'tests/fixtures/*.eml' \
  ./ "$HOST:$DIR/"

if [[ "${1:-}" == "--premiere" ]]; then
  # Secrets et mémoire du bot : copiés une seule fois, droits restreints
  ssh "$HOST" "mkdir -p $DIR/data && chmod 700 $DIR/data"
  scp -q .env "$HOST:$DIR/.env"
  ssh "$HOST" "chmod 600 $DIR/.env"
  [[ -f data/jobs.db ]] && scp -q data/jobs.db "$HOST:$DIR/data/jobs.db"
fi

ssh "$HOST" bash -s <<REMOTE
set -euo pipefail
UV=\$HOME/.local/share/uv-env/bin/uv
if [[ ! -x \$UV ]]; then
  python3 -m venv \$HOME/.local/share/uv-env
  \$HOME/.local/share/uv-env/bin/pip install -q uv
fi
cd $DIR
\$UV sync --frozen --no-dev -q
if [[ "${1:-}" == "--premiere" ]]; then
  sudo cp deploy/perso-jobbot.service deploy/perso-jobbot.timer /etc/systemd/system/
  sudo systemctl daemon-reload
fi
REMOTE
echo "Déployé sur $HOST:$DIR"
