# 🚀 AI Business Engine

![Backend Doctor & Smoke](https://github.com/x/AI-COMPLETE-AUTOMATION/actions/workflows/backend-ci.yml/badge.svg)

**Your personal AI-powered business empire-in-a-box** - designed to run 24/7, learn over time, and
execute at a scale and speed no human team could match.

## 🎯 What This Is

This system is **built solely for you** — a fully autonomous AI-driven business cockpit designed to
replace an entire company's operations with a single operator: **you**.

Instead of being a SaaS product or something intended for small businesses or enterprises, every
feature is tuned for **your own control, privacy, and rapid execution**.

The AI Business Engine is your **central command center**, integrating research, development,
testing, deployment, scaling, and ongoing management into one cohesive and secure platform. All
decisions, data, and automation stay entirely within your control — no external dependencies, no
shared access, and no compromises.

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

## 🚀 Development Workflow

### One-Command Backend Control

Your backend is now **bulletproof** with multiple control options:

#### **Option 1: VS Code/Cursor Tasks (Recommended)**

```bash
Ctrl+Shift+P → "Tasks: Run Task" → "Backend: Quick Start (Detach)"
Ctrl+Shift+P → "Tasks: Run Task" → "Backend: Stop"
```

#### **Option 2: Makefile Commands (Ultra-Quick)**

```bash
# Fortress Gates (Layers 1-6)
make hooks          # ✅ Install git safety hooks
make doctor         # ✅ Pre-flight health check
make smoke          # ✅ Fast app validation
make up             # ✅ Start backend (detach, returns instantly)
make up-debug       # ✅ Start with verbose probes
make up-lifespan    # ✅ Start bypassing startup events
make logs           # ✅ Follow logs (Ctrl+C to quit)
make down           # ✅ Stop backend
make clean          # ✅ Clean up PID/log files

# Autonomous City (Layers 7-11)
make deps           # ✅ Install/upgrade dependencies
make audit          # ✅ Security audit (pip-audit + npm audit)
make lint           # ✅ Code quality check (ruff + eslint)
make fmt            # ✅ Auto-format code (ruff + prettier)
make test           # ✅ Run test suite
make coverage       # ✅ Test coverage with enforcement
make heal           # ✅ Auto-heal unhealthy services
```

#### **Option 3: Direct Scripts (Full Control)**

```bash
# Quick start (returns to Cursor immediately)
DETACH=1 scripts/dev_up.sh

# Debug mode (verbose + returns)
DEBUG_STARTUP=1 DETACH=1 scripts/dev_up.sh

# Lifespan bypass (if startup hangs)
DISABLE_LIFESPAN=1 DEBUG_STARTUP=1 DETACH=1 scripts/dev_up.sh

# Stop backend
scripts/dev_down.sh
```

### **Features:**

- **✅ No more "thinking forever"** - Detach mode returns to Cursor immediately
- **✅ Automatic doctor checks** - Pre-flight validation before every startup
- **✅ Verbose debugging** - See exactly what's happening during health probes
- **✅ Graceful cleanup** - No orphaned processes, clean PID management
- **✅ Fast smoke tests** - Lightweight validation using FastAPI TestClient
- **✅ CI integration** - Runs `doctor` + `smoke` on every push/PR
- **✅ Pre-push safety** - Blocks pushes when backend health or smoke tests fail
- **✅ Dependency Guardian** - Automated security audits and dependency scanning
- **✅ Code Quality Enforcer** - Automated linting, formatting, and style checks
- **✅ Test Coverage Sentinel** - Enforces minimum test coverage requirements
- **✅ Observability Pipeline** - Full visibility into production performance
- **✅ Auto-Healing Infrastructure** - Self-recovery from common failures

### **Git Safety Hooks (3-Tier Protection)**

#### **Tier 1: Pre-Commit (Lightning-Fast)**

- **Runs**: Smoke test only (sub-second)
- **Catches**: Broken imports, syntax errors, missing deps
- **When**: Before you even stage a commit

#### **Tier 2: Pre-Push (Full Validation)**

- **Runs**: Doctor + smoke test (comprehensive)
- **Catches**: Port conflicts, venv issues, full health problems
- **When**: Before code leaves your machine

#### **Tier 3: CI (Clean Environment)**

- **Runs**: Doctor + smoke in GitHub Actions
- **Catches**: Environment-specific issues
- **When**: On every push/PR

### **Complete 11-Layer Protection System**

#### **Layers 1-6: Development Fortress** 🏰

- **Layer 1**: Local Development Control (VS Code Tasks, Makefile, Scripts)
- **Layer 2**: Pre-Commit Safety (Lightning-fast smoke test gate)
- **Layer 3**: Pre-Push Safety (Full doctor + smoke validation gate)
- **Layer 4**: CI Validation (Clean environment checks)
- **Layer 5**: Production Readiness (Health gates, graceful degradation)
- **Layer 6**: Developer Experience (Instant feedback, verbose debugging)

#### **Layers 7-11: Autonomous Development City** 🏙️

- **Layer 7**: Automated Dependency Guardian (Security audits, vulnerability scanning)
- **Layer 8**: Code Quality Enforcer (Linting, formatting, style consistency)
- **Layer 9**: Test Coverage Sentinel (Coverage enforcement, edge case detection)
- **Layer 10**: Observability Pipeline (OpenTelemetry, Sentry, performance monitoring)
- **Layer 11**: Auto-Healing Infrastructure (Self-recovery, queue clearing, service restart)

#### **Installation & Usage**

- **Install hooks**: `make hooks`
- **Skip (emergency)**: `SKIP_HOOKS=1 git push` or `git push --no-verify`
- **Skip commit**: `SKIP_HOOKS=1 git commit` or `git commit --no-verify`

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

### **Quick Setup (All 11 Layers)**

```bash
# 1) Install git safety hooks
make hooks

# 2) Install dependencies
make deps

# 3) Pre-flight health check
make doctor

# 4) Start backend (detach mode)
make up

# 5) Test all layers
make lint          # Code quality
make coverage      # Test coverage
make audit         # Security audit
make heal          # Auto-healing
```

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

## 🎯 Current Status: Complete 11-Layer Protection System

**✅ Completed - Development Fortress (Layers 1-6)**

- Core infrastructure (backend, frontend, database)
- Idea Engine with full pipeline
- Basic RBAC and security
- Metrics and observability foundation
- Runs Console with filtering and live updates
- Git safety hooks (pre-commit + pre-push)
- CI validation and health gates

**✅ Completed - Autonomous Development City (Layers 7-11)**

- Automated dependency guardian (security audits)
- Code quality enforcer (ruff + eslint + prettier)
- Test coverage sentinel (enforced coverage)
- Observability pipeline (OpenTelemetry + Sentry)
- Auto-healing infrastructure (self-recovery)

**🚧 In Progress**

- Enhanced RBAC enforcement
- Grafana dashboard provisioning
- Error taxonomy and retry policies

**📋 Next: Advanced AI Department Integration**

- Research Department with autonomous mode
- Advanced automation patterns
- Self-healing capabilities
- Production deployment scaling

## 🤝 Contributing

This is a **personal automation platform** built for single-operator use. All contributions should
focus on enhancing personal productivity and business automation capabilities.

## 📄 License

Private use only - not for distribution or commercial use.

---

**Built for maximum leverage, minimum dependency, and absolute control.**
