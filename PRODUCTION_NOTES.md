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

## Verification Timeline — Dec 28 2025

### Context
- **Phase**: Post-deploy verification
- **Branch**: `chore/prod-sync-2025-12-28`
- **Environment**: Python 3.12, updated `transformers`, ML dependencies unaligned post-hotfix.
- **State**: Main behind production.

### Event
- **Observation**: "Embedding generation failed: Could not find BertModel…"
- **Detection Method**: Manual functional validation of "Generate AI Score".
- **Impact**: Zero user impact. Not a Sev incident.

### Resolution
- Issue classified as environment/dependency mismatch.
- Resolved via Prod sync, dependency alignment (pinning), and tagging `prod-2025-12-28-stable`.

### Key Takeaway
This was a **verification finding**, not a production failure during user traffic. It occurred in the intended validation window.
