# FastAPI Authentication & User Management

A production-ready FastAPI application with complete user authentication and management system, built for mobile apps and admin dashboards.

## Features

### Core Authentication
- ✅ User registration with email validation
- ✅ JWT-based authentication (access + refresh tokens)
- ✅ Password hashing with bcrypt
- ✅ Token revocation/blacklisting
- ✅ Password reset via email
- ✅ Protected endpoints with middleware
- ✅ User profile management

### Tech Stack
- **FastAPI** - Modern async Python web framework
- **PostgreSQL** - Production database with async support
- **SQLAlchemy** - Async ORM with Alembic migrations
- **JWT** - Secure token-based authentication
- **Passlib + bcrypt** - Password hashing
- **SMTP** - Email sending for password resets
- **Pytest** - Comprehensive test suite

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL database
- SMTP server (optional, for emails)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd fastapi-auth-project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

Create PostgreSQL database:
```sql
CREATE DATABASE fastapi_auth;
CREATE USER fastapi_user WITH PASSWORD '200212';
GRANT ALL PRIVILEGES ON DATABASE fastapi_auth TO fastapi_user;
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:
```env
# Database (Required)
DATABASE_URL=postgresql+asyncpg://fastapi_user:your_password@localhost:5432/fastapi_auth

# JWT Secret (Required - use a strong random key)
JWT_SECRET_KEY=your-super-secret-jwt-key-generate-a-new-one
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# SMTP Configuration (Optional - for password reset emails)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Your App Name

# Application
APP_NAME=Your App Name
DEBUG=true
FRONTEND_URL=http://localhost:3000
```

### 4. Database Migration

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial tables"

# Apply migrations
alembic upgrade head
```

### 5. Run the Application

```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python -m app.main
```

Application will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📱 API Endpoints

### Authentication
```
POST /api/v1/auth/register          - User registration
POST /api/v1/auth/login             - User login
POST /api/v1/auth/refresh           - Refresh access token
POST /api/v1/auth/logout            - Logout (revoke token)
POST /api/v1/auth/request-password-reset  - Request password reset
POST /api/v1/auth/reset-password    - Reset password with token
```

### User Management
```
GET  /api/v1/users/me              - Get current user profile
PUT  /api/v1/users/language        - Update language preference
```

### ML Predictions (Child Nutrition & Health)
**Multilingual Support: English & Swahili** 🇹🇿
```
POST /api/v1/chatbot               - Ask nutrition/health/parenting questions
POST /api/v1/predict               - Predict malnutrition status & risk
POST /api/v1/recommend             - Get nutrition recommendations
POST /api/v1/analyze               - Complete analysis (predict + recommend)
```

### Child Management
**Track individual children with growth predictions**
```
POST /api/v1/children/register     - Register a new child
GET  /api/v1/children              - Get all user's children
POST /api/v1/children/{id}/records - Add growth record + predictions
GET  /api/v1/children/{id}/history - Get child's growth history
GET  /api/v1/children/{id}/trends  - Get growth trend analysis
```

### Example Usage

#### 1. Register a new user
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "pythondev355@gmail.com",
    "name": "francid Doe",
    "phone": "+1234567890",
    "password": "securepass123"
  }'
```

#### 2. Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'
```

#### 3. Access protected endpoint
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 4. Set language preference
```bash
curl -X PUT "http://localhost:8000/api/v1/users/language" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"language": "swahili"}'
```

#### 5. Ask chatbot question (English)
```bash
curl -X POST "http://localhost:8000/api/v1/chatbot" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"question": "What should I feed my 2-year-old for healthy growth?"}'
```

#### 6. Ask chatbot question (Swahili)
```bash
curl -X POST "http://localhost:8000/api/v1/chatbot" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"question": "Nimpe nini mtoto wangu wa miaka 2 kwa ukuaji mzuri?", "language": "swahili"}'
```

#### 7. Predict child nutrition status
```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
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
  }'
```

#### 8. Get nutrition recommendations
```bash
curl -X POST "http://localhost:8000/api/v1/recommend" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "malnutrition_status": "Underweight",
    "developmental_risk": "At Risk"
  }'
```

#### 9. Register a child
```bash
curl -X POST "http://localhost:8000/api/v1/children/register" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Amina",
    "sex": "Female",
    "birth_date": "2023-01-12"
  }'
```

#### 10. Add growth record with predictions
```bash
curl -X POST "http://localhost:8000/api/v1/children/CHILD_UUID/records" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "age_months": 18,
    "weight_kg": 9.2,
    "height_cm": 78.5,
    "muac_cm": 13.8,
    "diet_diversity_score": 4,
    "recent_infection": false,
    "weight_for_age_zscore": -1.2,
    "height_for_age_zscore": -0.8
  }'
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py -v
```

## 🔐 Security Features

### Current Security Measures
- ✅ Password hashing with bcrypt
- ✅ JWT tokens with expiration
- ✅ Token revocation/blacklisting
- ✅ Input validation with Pydantic
- ✅ SQL injection protection via SQLAlchemy
- ✅ CORS middleware
- ✅ Email-based password reset

### ⚠️ Production Security Notes

**Important**: This application uses intentionally simple security settings for development and demo purposes:

- **Password Policy**: Minimum 4 characters (for demo ease)
- **CORS**: Allows all origins (`allow_origins=["*"]`)
- **HTTPS**: Not enforced

### For Production Deployment:
1. **Strengthen password requirements** (min 8+ chars, complexity rules)
2. **Configure CORS properly** with specific allowed origins
3. **Enable HTTPS only** with proper SSL certificates
4. **Add rate limiting** for auth endpoints
5. **Implement account lockout** after failed attempts
6. **Add email verification** requirement
7. **Use environment-specific JWT secrets**
8. **Enable database connection pooling**
9. **Add comprehensive logging and monitoring**
10. **Implement proper error handling** without information leakage

## 📁 Project Structure

```
fastapi-auth-project/
├── app/
│   ├── api/
│   │   ├── auth.py          # Authentication endpoints
│   │   └── users.py         # User management endpoints
│   ├── core/
│   │   ├── config.py        # Application configuration
│   │   └── security.py      # JWT & password utilities
│   ├── crud/
│   │   └── user.py          # Database operations
│   ├── db/
│   │   ├── database.py      # Database connection
│   │   └── models.py        # SQLAlchemy models
│   ├── emails/
│   │   └── email_sender.py  # Email utilities
│   ├── schemas/
│   │   └── auth.py          # Pydantic models
│   └── main.py              # FastAPI application
├── alembic/                 # Database migrations
├── tests/
│   └── test_auth.py         # Test suite
├── requirements.txt         # Dependencies
├── .env.example            # Environment template
└── README.md               # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Yes | - | JWT signing secret key |
| `JWT_ALGORITHM` | No | HS256 | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | 15 | Access token expiry |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | 7 | Refresh token expiry |
| `SMTP_HOST` | No | - | Email server host |
| `SMTP_PORT` | No | 587 | Email server port |
| `SMTP_USER` | No | - | Email username |
| `SMTP_PASSWORD` | No | - | Email password |
| `APP_NAME` | No | FastAPI Auth | Application name |
| `DEBUG` | No | false | Debug mode |
| `FRONTEND_URL` | No | http://localhost:3000 | Frontend URL for emails |

## 🚢 Deployment

### Local PostgreSQL
1. Install PostgreSQL
2. Create database and user
3. Update `.env` with connection details
4. Run migrations: `alembic upgrade head`
5. Start app: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### Production Considerations
- Use a process manager (PM2, systemd, supervisor)
- Set up reverse proxy (Nginx)
- Configure SSL certificates
- Use environment-specific settings
- Set up monitoring and logging
- Implement backup strategies

## 📝 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📞 Support

For questions or issues:
1. Check the documentation
2. Review test examples
3. Open an issue with details

---

**Remember**: This is a development-ready authentication system. For production use, implement the additional security measures outlined in the Security Notes section above.
# AI_under5_backend_fastAPI
