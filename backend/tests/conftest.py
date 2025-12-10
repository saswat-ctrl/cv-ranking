import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, AsyncMock
from app.main import app
from app.api import deps
from app.models.user import User
from app.services.storage_service import StorageProvider

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock()
    # Mock execute result
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result
    return session

@pytest.fixture
def mock_current_user():
    """Mock authenticated user"""
    return User(
        id="test-user-id",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password"
    )

@pytest.fixture
def mock_storage_provider():
    """Mock storage provider"""
    provider = AsyncMock(spec=StorageProvider)
    provider.upload.return_value = "/path/to/file.pdf"
    provider.generate_download_url.return_value = "http://test/download"
    return provider

@pytest.fixture
async def client(mock_db_session, mock_current_user, mock_storage_provider):
    """Async client with mocked dependencies"""
    
    # Override dependencies
    app.dependency_overrides[deps.get_db] = lambda: mock_db_session
    app.dependency_overrides[deps.get_current_user] = lambda: mock_current_user
    
    # Patch get_storage_provider
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.api.v1.endpoints.jobs.get_storage_provider", lambda: mock_storage_provider)
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
            
    # Clean up overrides
    app.dependency_overrides = {}
