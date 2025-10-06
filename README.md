# FastAPI Auth Service

This is a FastAPI migration of the original Flask Auth Service, maintaining all business logic while leveraging FastAPI's modern features and performance benefits.

## Key Changes from Flask Version

### Technology Stack

- **Flask → FastAPI**: Modern async web framework
- **Flask-JWT-Extended → python-jose**: JWT handling
- **Flask CORS → FastAPI CORS Middleware**: CORS handling
- **Blueprints → APIRouter**: Route organization
- **@app.route → @router.{method}**: Route decorators
- **Flask error handlers → FastAPI exception handlers**: Error handling

### Architecture Improvements

- **Dependency Injection**: FastAPI's built-in DI system for database sessions, auth, etc.
- **Pydantic Models**: Request/response validation and serialization
- **Async Support**: Ready for async database operations
- **Automatic API Documentation**: Built-in Swagger/OpenAPI docs
- **Type Hints**: Full typing support throughout

## Project Structure

```
auth service new/
├── src/
│   ├── core/                   # Core configuration and utilities
│   │   ├── config.py          # Environment configuration
│   │   ├── database.py        # Database connection setup
│   │   ├── redis_client.py    # Redis client configuration
│   │   ├── jwt_config.py      # JWT authentication utilities
│   │   ├── auth_dependencies.py # FastAPI auth dependencies
│   │   └── app_config.py      # FastAPI app configuration
│   ├── models/                # Data models
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── users.py          # SQLAlchemy user model
│   │   └── __init__.py
│   ├── routers/               # API routes
│   │   ├── auth.py           # Authentication endpoints
│   │   └── __init__.py
│   ├── handlers/              # Business logic handlers
│   │   ├── users.py          # User management logic
│   │   ├── settings.py       # Settings management
│   │   ├── newsletter.py     # Newsletter management
│   │   └── __init__.py
│   ├── utils/                # Utilities
│   │   ├── wrappers/         # Response/error wrappers
│   │   ├── status_codes.py   # HTTP status codes
│   │   ├── http_messages.py  # HTTP messages
│   │   └── __init__.py
│   ├── dependencies.py       # FastAPI dependencies
│   └── main.py              # FastAPI application
├── app.py                   # Application entry point
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
├── .env.sample             # Environment variables template
└── README.md               # This file
```

## Key Features Preserved

- ✅ User authentication (register, login, logout)
- ✅ JWT token management with Redis blacklist
- ✅ Role-based access control (ADMIN, HOSPITAL, DOCTOR)
- ✅ Password reset functionality
- ✅ User profile management
- ✅ Newsletter subscription
- ✅ Cloudflare Turnstile integration
- ✅ Azure Blob Storage integration
- ✅ PostgreSQL database support
- ✅ Docker containerization

## Setup Instructions

### 1. Environment Configuration

```bash
# Copy environment template
cp .env.sample .env

# Edit .env with your actual values
# Update database credentials, JWT secrets, etc.
```

### 2. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Or using uvicorn directly
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Docker Development

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in background
docker-compose up -d
```

### 4. Database Setup

The application will automatically:

- Initialize database connections
- Create admin user if it doesn't exist
- Set up database tables (ensure your database exists)

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Authentication Flow

### 1. Register User

```http
POST /api/auth/register
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "user_type": "ADMIN"
}
```

### 2. Login

```http
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
```

### 3. Access Protected Routes

```http
GET /api/auth/validate
Authorization: Bearer <access_token>
```

### 4. Refresh Token

```http
GET /api/auth/refresh
Authorization: Bearer <refresh_token>
```

### 5. Logout

```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

## Key Differences in Usage

### Flask vs FastAPI Route Definition

**Flask (old):**

```python
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    # ...
```

**FastAPI (new):**

```python
@router.post("/register")
async def register(user_data: UserRegisterRequest):
    # ...
```

### Authentication Dependencies

**Flask (old):**

```python
@token_required
def protected_route():
    user = request.user_info
```

**FastAPI (new):**

```python
async def protected_route(current_user: CurrentUser = Depends(get_current_user)):
    # user data available in current_user
```

## Migration Status

### ✅ Completed

- Core FastAPI application setup
- Configuration management
- JWT authentication system
- Auth router (register, login, logout, etc.)
- Database dependencies
- Docker configuration
- Pydantic request/response models
- Basic user management

### 🚧 In Progress / TODO

- Complete all handler classes migration
- Migrate remaining routers (user, doctor, hospital, patient, profile, settings)
- Copy all SQLAlchemy models
- Azure Blob Storage integration testing
- Complete error handling
- Async optimization
- Integration testing

## Performance Benefits

- **Async Support**: Ready for async database operations
- **Better Concurrency**: FastAPI's async nature handles more concurrent requests
- **Pydantic Validation**: Faster serialization/validation than manual JSON handling
- **Automatic Documentation**: No separate documentation maintenance

## Development Notes

1. **Import Structure**: All imports use relative imports within the package
2. **Dependency Injection**: Database sessions and auth handled via FastAPI dependencies
3. **Error Handling**: Centralized error handling with consistent response format
4. **Type Safety**: Full type hints throughout the codebase
5. **Testing Ready**: Structure supports easy unit and integration testing

## Next Steps

1. **Complete Migration**: Finish migrating all routers and handlers
2. **Testing**: Add comprehensive test suite
3. **Documentation**: Complete API documentation
4. **Deployment**: Set up production deployment configuration
5. **Monitoring**: Add logging and monitoring integration

## Environment Variables

See `.env.sample` for all required environment variables. Key variables include:

- `DEPLOYMENT`: DEVELOPMENT/PRODUCTION
- `DB_*`: Database connection settings
- `SECRET_KEY` / `JWT_SECRET_KEY`: Security keys
- `REDIS_*`: Redis configuration for JWT blacklist
- `ADMIN_USER_*`: Default admin user settings
- `AZURE_*`: Azure Blob Storage settings

## Support

For issues or questions about this migration, refer to:

1. FastAPI documentation: https://fastapi.tiangolo.com/
2. Original Flask codebase for business logic reference
3. This README for migration-specific information
# auth-service-new
