#!/usr/bin/env bash
set -e

############################################
# CONFIG — adjust ONLY if paths change
############################################
APP_NAME="saarnews-backend"
APP_DIR="/var/www/saarnews/backend"
VENV_DIR="$APP_DIR/venv"
PYTHON="$VENV_DIR/bin/python"
GUNICORN_SERVICE="saarnews-backend"
REQUIREMENTS_FILE="requirements.prod.txt"

############################################
# INPUT VALIDATION
############################################
if [ -z "$1" ]; then
  echo "❌ ERROR: No git tag provided."
  echo "Usage: ./deploy.sh <git-tag>"
  exit 1
fi

TAG="$1"

echo "🚀 Deploying tag: $TAG"
echo "📁 App directory: $APP_DIR"

############################################
# PRE-FLIGHT CHECKS
############################################
cd "$APP_DIR"

echo "🔎 Checking git tag exists..."
git fetch --tags
git rev-parse "$TAG" >/dev/null 2>&1 || {
  echo "❌ ERROR: Git tag '$TAG' does not exist."
  exit 1
}

############################################
# STOP SERVICE
############################################
echo "🛑 Stopping backend service..."
systemctl stop "$GUNICORN_SERVICE"

############################################
# CHECKOUT TAG
############################################
echo "📦 Checking out tag $TAG..."
git checkout -f "$TAG"

############################################
# PYTHON ENV
############################################
echo "🐍 Activating virtualenv..."
source "$VENV_DIR/bin/activate"

############################################
# DEPENDENCIES
############################################
if [ -f "$REQUIREMENTS_FILE" ]; then
  echo "📚 Installing production dependencies..."
  pip install --upgrade pip
  pip install -r "$REQUIREMENTS_FILE"
else
  echo "⚠️ WARNING: $REQUIREMENTS_FILE not found. Skipping dependency install."
fi

############################################
# DATABASE MIGRATIONS
############################################
else
  echo "⚠️ Alembic not found. Skipping migrations."
fi

############################################
# PRE-LOAD MODELS
############################################
echo "🧠 Pre-loading ML models..."
$PYTHON -c "from app.services.embedding_service import preload_model; preload_model()" || {
  echo "❌ ERROR: Model pre-loading failed."
  exit 1
}

############################################
# START SERVICE
############################################
echo "▶️ Starting backend service..."
systemctl start "$GUNICORN_SERVICE"

############################################
# HEALTH CHECK
############################################
echo "🩺 Waiting for service to become healthy..."
sleep 3

curl -f http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1 && {
  echo "✅ Deployment successful!"
  systemctl status "$GUNICORN_SERVICE" --no-pager
  exit 0
}

echo "❌ ERROR: Health check failed."
journalctl -u "$GUNICORN_SERVICE" -n 50 --no-pager
exit 1
