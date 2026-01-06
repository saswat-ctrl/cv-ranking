# Production Notes — 2025-12-28

## Emergency Hotfixes (Permanent)

### auth.py / health.py / __init__.py
- Local code used `-> Any` return annotations without importing `Any`
- This caused runtime NameError during module import
- Production removed return type hints and/or added imports
- `__init__.py` required explicit registration of `health` router
- These changes are REQUIRED for runtime stability

⚠️ Do NOT reintroduce return type hints without validating imports.

## Configuration
- Production `.env` contains required keys not present in earlier templates
- `.env.production.template` updated to reflect required structure
- Secrets are never committed

## Policy
Production is the source of truth during incidents.
Git must reflect Production behavior after stabilization.
