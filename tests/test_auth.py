import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_async_session, Base
from app.core.config import settings

# Test database URL (SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# Test session factory
test_async_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def override_get_async_session():
    """Override database session for testing."""
    async with test_async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Override dependency
app.dependency_overrides[get_async_session] = override_get_async_session


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def setup_database():
    """Set up test database before each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "phone": "+1234567890",
        "password": "testpass123"
    }
    
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    """Test user login."""
    # First register a user
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpass123"
    }
    
    await client.post("/api/v1/auth/register", json=user_data)
    
    # Then login
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_access_protected_endpoint(client: AsyncClient):
    """Test accessing protected endpoint with token."""
    # Register and login first
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpass123"
    }
    
    await client.post("/api/v1/auth/register", json=user_data)
    
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    login_response = await client.post("/api/v1/auth/login", json=login_data)
    tokens = login_response.json()
    
    # Access protected endpoint
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == "test@example.com"
    assert user_data["name"] == "Test User"


@pytest.mark.asyncio
async def test_invalid_login(client: AsyncClient):
    """Test login with invalid credentials."""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "wrongpass"
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_registration(client: AsyncClient):
    """Test registering with duplicate email."""
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpass123"
    }
    
    # Register first user
    response1 = await client.post("/api/v1/auth/register", json=user_data)
    assert response1.status_code == 201
    
    # Try to register again with same email
    response2 = await client.post("/api/v1/auth/register", json=user_data)
    assert response2.status_code == 400


@pytest.mark.asyncio
async def test_token_refresh(client: AsyncClient):
    """Test refreshing access token."""
    # Register and login first
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpass123"
    }
    
    await client.post("/api/v1/auth/register", json=user_data)
    
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    login_response = await client.post("/api/v1/auth/login", json=login_data)
    tokens = login_response.json()
    
    # Refresh token
    refresh_data = {"refresh_token": tokens["refresh_token"]}
    refresh_response = await client.post("/api/v1/auth/refresh", json=refresh_data)
    
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens
    assert new_tokens["access_token"] != tokens["access_token"]  # Should be different


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    """Test user logout."""
    # Register and login first
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpass123"
    }
    
    await client.post("/api/v1/auth/register", json=user_data)
    
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    login_response = await client.post("/api/v1/auth/login", json=login_data)
    tokens = login_response.json()
    
    # Logout
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    logout_response = await client.post("/api/v1/auth/logout", headers=headers)
    
    assert logout_response.status_code == 200
    assert "message" in logout_response.json()
    
    # Try to access protected endpoint with logged out token
    me_response = await client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_password_reset_request(client: AsyncClient):
    """Test password reset request."""
    # Register user first
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpass123"
    }
    
    await client.post("/api/v1/auth/register", json=user_data)
    
    # Request password reset
    reset_data = {"email": "test@example.com"}
    response = await client.post("/api/v1/auth/request-password-reset", json=reset_data)
    
    assert response.status_code == 200
    assert "message" in response.json()
