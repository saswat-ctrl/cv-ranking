import sys
import os
from pathlib import Path

# Add backend to sys.path
backend_path = str(Path.cwd())
sys.path.append(backend_path)

from app.services.storage_service import LocalStorageProvider

provider = LocalStorageProvider()
print(f"Base Dir: {provider.base_dir}")
print(f"Exists: {provider.base_dir.exists()}")

# Create a test file
test_dir = provider.base_dir / "test_debug"
test_dir.mkdir(exist_ok=True)
print(f"Created test dir at: {test_dir}")
