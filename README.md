# MLOps Platform Backend

A hypervisor-like service for managing user authentication, organization membership, cluster resource allocation, and deployment scheduling in an MLOps platform.

## Features

- **User Authentication**: JWT-based authentication with role-based access control
- **Organization Management**: Invite-code based organization membership
- **Cluster Management**: Resource allocation and tracking for RAM, CPU, and GPU
- **Deployment Scheduling**: Priority-based scheduling with preemption support
- **Queue Management**: Redis-based deployment queue with priority scoring
- **Dependency Management**: Support for deployment dependencies

## Technology Stack

- **FastAPI**: Web framework
- **PostgreSQL**: Primary database
- **Redis**: Queue management and caching
- **SQLAlchemy**: ORM
- **JWT**: Authentication tokens
- **Docker**: Containerization

## Setup and Installation

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL (if running locally)
- Redis (if running locally)

### Using Docker Compose (Recommended)

1. Clone the repository
2. Navigate to the project directory
3. Run the application:

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

### Local Development Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export DATABASE_URL="postgresql://postgres:password@localhost/mlops_db"
export REDIS_URL="redis://localhost:6379"
export SECRET_KEY="your-secret-key"
```

3. Start PostgreSQL and Redis services

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the application:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the application is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage Examples

### 1. User Registration and Authentication

```bash
# Register a new user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepassword",
    "role": "developer"
  }'

# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&password=securepassword"
```

### 2. Organization Management

```bash
# Create organization (as admin)
curl -X POST "http://localhost:8000/organizations/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Company"}'

# Get invite code
curl -X GET "http://localhost:8000/organizations/1/invite-code" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Cluster Management

```bash
# Create cluster
curl -X POST "http://localhost:8000/clusters/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Cluster",
    "total_ram_gb": 64.0,
    "total_cpu_cores": 16.0,
    "total_gpu_count": 4
  }'

# List clusters
curl -X GET "http://localhost:8000/clusters/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Deployment Management

```bash
# Create deployment
curl -X POST "http://localhost:8000/deployments/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ML Model Deployment",
    "docker_image": "myregistry/ml-model:latest",
    "cluster_id": 1,
    "required_ram_gb": 8.0,
    "required_cpu_cores": 2.0,
    "required_gpu_count": 1,
    "priority": "HIGH"
  }'

# List deployments
curl -X GET "http://localhost:8000/deployments/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Architecture

### Database Schema

The system uses the following main entities:

1. **Users**: Authentication and user management
2. **Organizations**: Multi-tenancy support
3. **Clusters**: Resource pools with RAM, CPU, GPU tracking
4. **Deployments**: Containerized applications with resource requirements

### Scheduling Algorithm

The deployment scheduler optimizes for:

1. **Priority**: Higher priority deployments are scheduled first
2. **Resource Utilization**: Efficient use of available cluster resources
3. **Successful Deployments**: Maximizes the number of deployments that can run

Key features:
- Priority-based queue management using Redis sorted sets
- Preemption support for high-priority deployments
- Dependency management between deployments
- Real-time resource tracking and allocation

### Security

- JWT-based authentication
- Role-based access control (Admin, Developer, Viewer)
- Organization-level data isolation
- Secure password hashing with bcrypt

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

For coverage report:

```bash
pytest tests/ --cov=app --cov-report=html
```

## Configuration

Key configuration options in `app/core/config.py`:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing key
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License. 