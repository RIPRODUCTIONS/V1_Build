# 🚀 AI Business Engine

**Your personal AI-powered business empire-in-a-box** - designed to run 24/7, learn over time, and execute at a scale and speed no human team could match.

## 🎯 What This Is

This system is **built solely for you** — a fully autonomous AI-driven business cockpit designed to replace an entire company's operations with a single operator: **you**.

Instead of being a SaaS product or something intended for small businesses or enterprises, every feature is tuned for **your own control, privacy, and rapid execution**.

The AI Business Engine is your **central command center**, integrating research, development, testing, deployment, scaling, and ongoing management into one cohesive and secure platform. All decisions, data, and automation stay entirely within your control — no external dependencies, no shared access, and no compromises.

## 🏗️ Architecture Overview

- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Backend**: FastAPI with Python 3.13, SQLAlchemy ORM
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Queue**: Redis Streams with Celery workers
- **Orchestrator**: Manager orchestrator with Redis event bus
- **Observability**: Prometheus metrics + Grafana dashboards
- **Security**: JWT-based RBAC with scope-based permissions

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- Redis (for production features)
- Docker (optional, for full stack)

### 1. Clone & Setup
```bash
git clone <your-repo>
cd "V1 of builder"
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd apps/web
npm install
```

### 4. Start Development Servers
```bash
# Terminal 1: Backend
cd backend && source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd apps/web
npm run dev
```

### 5. Access the System
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Metrics**: http://localhost:8000/metrics

## 🔐 Security & Authentication

### RBAC Scopes
The system uses JWT-based authentication with scope-based access control:

- **`life.read`** - Access to life management features
- **`runs.read`** - View automation runs and status
- **`runs.write`** - Modify run status and metadata
- **`departments.read`** - View department information
- **`artifacts.read`** - Access run artifacts
- **`admin.*`** - Full administrative access

### Getting a Token
```bash
# Generate a JWT token with specific scopes
cd backend
source .venv/bin/activate
python scripts/mint_jwt.py --scopes "runs.read,runs.write,departments.read"
```

## 📊 Core Endpoints

### Health & Status
- `GET /health` - Basic health check
- `GET /health/manager` - Manager orchestrator health
- `GET /metrics` - Prometheus metrics

### Automation & Runs
- `GET /runs` - List automation runs with filtering
- `GET /runs/{id}` - Get specific run details
- `GET /runs/{id}/artifacts` - Get run artifacts
- `PATCH /runs/{id}` - Update run status

### Business Department
- `POST /business/idea-engine/run` - Launch Idea Engine
- `GET /business/idea-engine/results/{run_id}` - Get results

### Research Department
- `POST /research/market-gaps/run` - Run Market Gap Scanner
- `GET /research/market-gaps/results` - Get scanner results

## 🎯 Key Features

### ✅ Idea Engine (Production Ready)
- AI-powered business idea generation
- Market research and validation
- Comprehensive business analysis
- Opportunity scoring and ranking

### 🚧 Runs Console (Batch D)
- Real-time run monitoring
- Advanced filtering and search
- Live status updates
- Manager health monitoring

### 🚧 Market Gap Scanner (Batch E)
- Automated market opportunity detection
- Competitive landscape analysis
- Trend identification and scoring

## 📈 Observability

### Metrics Available
- **API Performance**: Request rate, latency (p50/p95), error rates
- **Orchestrator Health**: Redis stream lag, planning duration, step counts
- **Idea Engine**: Run counts, execution latency, ideas generated
- **System Health**: Queue depths, consumer group status

### Grafana Dashboards
- **AI Business Engine Dashboard**: Complete system overview
- **API SLO Dashboard**: Performance and reliability metrics
- **Orchestrator Dashboard**: Event processing and health

## 🔧 Development

### Running Tests
```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -v
```

### Code Quality
```bash
cd backend
source .venv/bin/activate
ruff check --fix .
black .
```

### Database Migrations
```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

## 🚀 Deployment

### Local with Docker Compose
```bash
docker-compose up -d
```

### Production (Kubernetes)
```bash
cd deploy/k8s
kubectl apply -k .
```

## 📚 Documentation

- **Architecture**: `docs/ARCHITECTURE.md` - Complete system breakdown
- **Operations**: `docs/operations.md` - Day-to-day operations guide
- **Idea Engine**: `docs/IDEA_ENGINE.md` - Detailed usage guide

## 🎯 Current Status: Batch D

**✅ Completed**
- Core infrastructure (backend, frontend, database)
- Idea Engine with full pipeline
- Basic RBAC and security
- Metrics and observability foundation
- Runs Console with filtering and live updates

**🚧 In Progress**
- Enhanced RBAC enforcement
- Grafana dashboard provisioning
- Error taxonomy and retry policies

**📋 Next: Batch E**
- Research Department integration
- Advanced automation patterns
- Self-healing capabilities

## 🤝 Contributing

This is a **personal automation platform** built for single-operator use. All contributions should focus on enhancing personal productivity and business automation capabilities.

## 📄 License

Private use only - not for distribution or commercial use.

---

**Built for maximum leverage, minimum dependency, and absolute control.**
