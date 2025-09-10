import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_async_session, Base

# Test database URL (SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_ml.db"

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


@pytest.fixture
async def auth_token(client: AsyncClient):
    """Get authentication token for testing."""
    # Register and login to get auth token
    user_data = {
        "email": "testuser@example.com",
        "name": "Test User",
        "password": "testpass123"
    }
    
    await client.post("/api/v1/auth/register", json=user_data)
    
    login_data = {
        "email": "testuser@example.com",
        "password": "testpass123"
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    tokens = response.json()
    return tokens["access_token"]


@pytest.mark.asyncio
async def test_chatbot_endpoint(client: AsyncClient, auth_token: str):
    """Test chatbot endpoint."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    chatbot_data = {
        "question": "What should I feed my 2-year-old child for healthy growth?"
    }
    
    response = await client.post("/api/v1/chatbot", json=chatbot_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 20  # Should be a substantial answer
    assert isinstance(data["answer"], str)


@pytest.mark.asyncio
async def test_prediction_endpoint(client: AsyncClient, auth_token: str):
    """Test nutrition prediction endpoint."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    prediction_data = {
        "Age_Months": 24,
        "Sex": "Male",
        "Weight_kg": 11.2,
        "Height_cm": 84.0,
        "HeadCircumference_cm": 46.0,
        "MUAC_cm": 14.0,
        "BMI": 15.5,
        "Diet_Diversity_Score": 5,
        "Recent_Infection": "No",
        "Weight_for_Age_ZScore": -0.5,
        "Height_for_Age_ZScore": -1.2,
        "BMI_for_Age_ZScore": 0.3,
        "MUAC_for_Age_ZScore": -0.2,
        "Weight_for_Age_Percentile": 40.0,
        "Height_for_Age_Percentile": 30.0,
        "BMI_for_Age_Percentile": 55.0,
        "MUAC_for_Age_Percentile": 45.0
    }
    
    response = await client.post("/api/v1/predict", json=prediction_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "malnutrition_status" in data
    assert "developmental_risk" in data
    
    # Check valid status values
    valid_malnutrition_statuses = ["Normal", "Stunting", "Underweight", "Overweight", "Severe"]
    valid_risk_levels = ["No Risk", "At Risk", "High Risk"]
    
    assert data["malnutrition_status"] in valid_malnutrition_statuses
    assert data["developmental_risk"] in valid_risk_levels


@pytest.mark.asyncio
async def test_recommendation_endpoint(client: AsyncClient, auth_token: str):
    """Test recommendation endpoint."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    recommendation_data = {
        "malnutrition_status": "Underweight",
        "developmental_risk": "At Risk"
    }
    
    response = await client.post("/api/v1/recommend", json=recommendation_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "recommendation" in data
    assert len(data["recommendation"]) > 50  # Should be a detailed recommendation
    assert isinstance(data["recommendation"], str)


@pytest.mark.asyncio
async def test_analyze_endpoint(client: AsyncClient, auth_token: str):
    """Test combined analyze endpoint."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    analysis_data = {
        "Age_Months": 18,
        "Sex": "Female",
        "Weight_kg": 9.5,
        "Height_cm": 78.0,
        "HeadCircumference_cm": 44.0,
        "MUAC_cm": 13.5,
        "BMI": 15.6,
        "Diet_Diversity_Score": 4,
        "Recent_Infection": "Yes",
        "Weight_for_Age_ZScore": -1.5,
        "Height_for_Age_ZScore": -2.1,
        "BMI_for_Age_ZScore": -0.8,
        "MUAC_for_Age_ZScore": -1.0,
        "Weight_for_Age_Percentile": 25.0,
        "Height_for_Age_Percentile": 15.0,
        "BMI_for_Age_Percentile": 35.0,
        "MUAC_for_Age_Percentile": 30.0
    }
    
    response = await client.post("/api/v1/analyze", json=analysis_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "prediction" in data
    assert "recommendation" in data
    assert "child_info" in data
    
    # Check prediction structure
    prediction = data["prediction"]
    assert "malnutrition_status" in prediction
    assert "developmental_risk" in prediction
    
    # Check child info
    child_info = data["child_info"]
    assert child_info["age_months"] == 18
    assert child_info["sex"] == "Female"
    assert child_info["weight_kg"] == 9.5
    assert child_info["height_cm"] == 78.0
    
    # Check recommendation
    assert isinstance(data["recommendation"], str)
    assert len(data["recommendation"]) > 50


@pytest.mark.asyncio
async def test_prediction_validation(client: AsyncClient, auth_token: str):
    """Test input validation for prediction endpoint."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test invalid age
    invalid_data = {
        "Age_Months": 0,  # Invalid age
        "Sex": "Male",
        "Weight_kg": 11.2,
        "Height_cm": 84.0,
        "HeadCircumference_cm": 46.0,
        "MUAC_cm": 14.0,
        "BMI": 15.5,
        "Diet_Diversity_Score": 5,
        "Recent_Infection": "No",
        "Weight_for_Age_ZScore": -0.5,
        "Height_for_Age_ZScore": -1.2,
        "BMI_for_Age_ZScore": 0.3,
        "MUAC_for_Age_ZScore": -0.2,
        "Weight_for_Age_Percentile": 40.0,
        "Height_for_Age_Percentile": 30.0,
        "BMI_for_Age_Percentile": 55.0,
        "MUAC_for_Age_Percentile": 45.0
    }
    
    response = await client.post("/api/v1/predict", json=invalid_data, headers=headers)
    assert response.status_code == 400
    
    # Test invalid weight
    invalid_data["Age_Months"] = 24
    invalid_data["Weight_kg"] = 0  # Invalid weight
    
    response = await client.post("/api/v1/predict", json=invalid_data, headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test that ML endpoints require authentication."""
    
    # Test chatbot without auth
    chatbot_data = {"question": "Test question"}
    response = await client.post("/api/v1/chatbot", json=chatbot_data)
    assert response.status_code == 401
    
    # Test prediction without auth
    prediction_data = {
        "Age_Months": 24, "Sex": "Male", "Weight_kg": 11.2, "Height_cm": 84.0,
        "HeadCircumference_cm": 46.0, "MUAC_cm": 14.0, "BMI": 15.5,
        "Diet_Diversity_Score": 5, "Recent_Infection": "No",
        "Weight_for_Age_ZScore": -0.5, "Height_for_Age_ZScore": -1.2,
        "BMI_for_Age_ZScore": 0.3, "MUAC_for_Age_ZScore": -0.2,
        "Weight_for_Age_Percentile": 40.0, "Height_for_Age_Percentile": 30.0,
        "BMI_for_Age_Percentile": 55.0, "MUAC_for_Age_Percentile": 45.0
    }
    response = await client.post("/api/v1/predict", json=prediction_data)
    assert response.status_code == 401
    
    # Test recommendation without auth
    recommendation_data = {
        "malnutrition_status": "Normal",
        "developmental_risk": "No Risk"
    }
    response = await client.post("/api/v1/recommend", json=recommendation_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chatbot_edge_cases(client: AsyncClient, auth_token: str):
    """Test chatbot with various question types."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test nutrition-related question
    nutrition_question = {"question": "What foods are good for my baby?"}
    response = await client.post("/api/v1/chatbot", json=nutrition_question, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "nutrition" in data["answer"].lower() or "food" in data["answer"].lower()
    
    # Test growth-related question
    growth_question = {"question": "Is my child developing normally?"}
    response = await client.post("/api/v1/chatbot", json=growth_question, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["answer"]) > 20
    
    # Test empty question (should fail validation)
    empty_question = {"question": ""}
    response = await client.post("/api/v1/chatbot", json=empty_question, headers=headers)
    assert response.status_code == 422  # Validation error
