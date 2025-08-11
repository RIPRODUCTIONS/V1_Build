# AI Business Engine

A complete autonomous business automation platform that replaces traditional business roles with AI agents, handling everything from idea generation to deployment and scaling.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Redis
- PostgreSQL (optional, SQLite for development)

### 1. Clone & Setup
```bash
git clone <repository>
cd "V1 of builder"
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cd apps/web && npm install
```

### 2. Environment Variables
```bash
# Backend (.env)
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
SECURE_MODE=1  # Enable RBAC enforcement
REDIS_URL=redis://localhost:6379
DATABASE_URL=sqlite:///./dev.db

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WEB_ORIGIN=http://localhost:3000
```

### 3. Start Services
```bash
# Start platform infrastructure
cd platform/infra
docker-compose up -d

# Start backend
cd ../../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start frontend
cd ../apps/web
npm run dev

# Start manager orchestrator
cd ../../platform/orchestration/manager
REDIS_URL=redis://localhost:6379 python consumer.py
```

### 4. Access Services
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Manager Health**: http://localhost:8080/health

## 🔐 Authentication & Scopes

### JWT Token Structure
```json
{
  "sub": "user_id",
  "scopes": ["life.read", "runs.write", "admin.*"],
  "exp": 1234567890
}
```

### Required Scopes by Endpoint

#### Life Automation (`/life/*`)
- **POST** `/life/health/wellness_daily` → `life.read` + `life.write`
- **POST** `/life/nutrition/plan` → `life.read` + `life.write`
- **POST** `/life/home/evening_scene` → `life.read` + `life.write`

#### Runs Management (`/runs/*`)
- **GET** `/runs` → `runs.read` (or `life.read` if SECURE_MODE=0)
- **GET** `/runs/{id}` → `runs.read`
- **PATCH** `/runs/{id}` → `runs.write`
- **GET** `/runs/{id}/artifacts` → `artifacts.read`

#### Departments (`/departments/*`)
- **GET** `/departments` → `departments.read`
- **GET** `/departments/tasks/catalog` → `departments.read`

#### Administrative
- **All admin routes** → `admin.*`
- **Health/metrics** → No auth required

## 📊 API Endpoints

### Core Endpoints
- `GET /health` - Service health check
- `GET /metrics` - Prometheus metrics
- `GET /docs` - OpenAPI documentation

### Life Automation
- `POST /life/health/wellness_daily` - Daily wellness automation
- `POST /life/nutrition/plan` - Nutrition planning
- `POST /life/home/evening_scene` - Home automation
- `POST /life/transport/commute` - Transport optimization
- `POST /life/learning/upskill` - Learning automation

### Runs & Artifacts
- `GET /runs` - List automation runs with filtering
- `GET /runs/{id}` - Get run details
- `PATCH /runs/{id}` - Update run status
- `GET /runs/{id}/artifacts` - Get run artifacts

### Departments
- `GET /departments` - List AI departments
- `GET /departments/tasks/catalog` - Get task catalog

## 🏗️ Architecture

### Core Components
1. **Backend API** (FastAPI + SQLAlchemy)
2. **Frontend Dashboard** (Next.js + TypeScript)
3. **Event Processing Engine** (Redis Streams)
4. **Manager Orchestrator** (Rule-based planning)
5. **AI Department System** (Specialized automation domains)
6. **Observability Stack** (Prometheus + Grafana)

### Event Flow
```
automation.run.requested → Manager → Department → Artifacts
```

### Data Flow
1. User triggers automation via UI
2. Backend emits `automation.run.requested` event
3. Manager consumes event and creates execution plan
4. Manager emits `run.started` and `run.status.updated` events
5. Results stored as artifacts with correlation IDs

## 📈 Monitoring & Observability

### Metrics Available
- **API Performance**: Request rate, latency (p50/p95), error rate
- **Orchestrator Health**: Redis Stream lag, queue depth, reprocessing
- **Manager Health**: Planning duration, step count, failure reasons
- **Agent Metrics**: Token usage, costs, latency (Batch E)

### Dashboards
- **API SLO**: Performance and error monitoring
- **Orchestrator**: Redis Streams and queue health
- **Manager Health**: Planning and execution metrics

### Health Checks
- Backend: `GET /health`, `GET /readyz`
- Manager: `GET /health/manager`
- Metrics: `GET /metrics`

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd apps/web
npm run test
npm run test:e2e
```

### Load Testing
```bash
# Using k6 (install separately)
k6 run scripts/load-test.js
```

## 🚀 Deployment

### Local Development
```bash
make up          # Start all services
make down        # Stop all services
make logs        # View logs
make test        # Run tests
```

### Production
```bash
# Build and deploy
docker build -t ai-business-engine .
docker run -p 8000:8000 ai-business-engine
```

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Contracts](docs/contracts/)
- [Operations Guide](docs/operations.md)
- [Contributing Guidelines](docs/CONTRIBUTING.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is proprietary and confidential.

---

**Status**: Batch D (Web UI & Docs) - In Progress
**Version**: v0.85.0-pre
**Next Milestone**: Batch E (AI Agent Integration)
