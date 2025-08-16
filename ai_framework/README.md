# 🤖 AI Framework - Comprehensive Multi-Provider AI Integration

A production-ready AI integration system with multi-agent capabilities for automation and research.

## 🚀 Features

### **Multi-LLM Integration**
- **OpenAI**: GPT-4, GPT-4-turbo, GPT-3.5-turbo with streaming and function calling
- **Anthropic**: Claude 3.5 Sonnet and Haiku models
- **Ollama**: Local models (Llama3.1, CodeLlama, Mistral) for privacy-sensitive tasks
- **OSS-20B**: Local deployment with quantization support

### **Intelligent Model Routing**
- Automatic provider selection based on task requirements
- Cost-performance optimization
- Privacy-aware routing (local models for sensitive data)
- A/B testing and performance learning
- Fallback mechanisms and load balancing

### **Multi-Agent Framework**
- **Research Agent**: Web research and data collection
- **Analysis Agent**: Data analysis and insights
- **Automation Agent**: Task automation and workflows
- **Security Agent**: Security monitoring and threat detection
- **Content Agent**: Content generation and management
- **Reporting Agent**: Automated report generation

### **Advanced Capabilities**
- **Vector Database Integration**: ChromaDB, Pinecone, Weaviate
- **Memory Management**: Conversation history, entity tracking, context windows
- **Real-time Streaming**: WebSocket support for live interactions
- **Function Calling**: Native function execution across providers
- **Performance Monitoring**: Metrics, health checks, and analytics
- **Security**: Authentication, rate limiting, and encryption

## 🏗️ Architecture

```
ai_framework/
├── core/                    # Core framework components
│   ├── llm_manager.py      # Multi-LLM integration
│   ├── model_router.py     # Intelligent routing
│   ├── agent_orchestrator.py # Agent coordination
│   └── memory_manager.py   # Context & memory
├── agents/                  # Agent implementations
├── frameworks/              # External framework integrations
├── tools/                   # Utility tools and connectors
├── vector_db/              # Vector database integrations
├── monitoring/              # Performance monitoring
├── config/                  # Configuration management
├── api/                     # FastAPI endpoints
└── tests/                   # Comprehensive test suite
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai_framework

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file with your API keys:

```bash
# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_ORGANIZATION=your_organization

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434

# Database
DATABASE_TYPE=sqlite
DATABASE_PATH=ai_framework.db
```

### 3. Basic Usage

```python
import asyncio
from ai_framework.core import LLMManager, ModelRouter, AgentOrchestrator

async def main():
    # Initialize the framework
    llm_manager = LLMManager()
    model_router = ModelRouter()
    orchestrator = AgentOrchestrator()

    # Generate text with automatic provider selection
    response = await llm_manager.generate(
        prompt="Explain quantum computing in simple terms",
        requirements={
            "task_type": "explanation",
            "complexity": "simple",
            "max_tokens": 500
        }
    )

    print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 Configuration

### Provider Configuration

```python
from ai_framework.config import Settings

settings = Settings()

# Enable specific providers
settings.openai.enabled = True
settings.anthropic.enabled = True
settings.ollama.enabled = True

# Configure models
settings.openai.models = [
    {"name": "gpt-4", "max_tokens": 8192},
    {"name": "gpt-3.5-turbo", "max_tokens": 4096}
]

# Set rate limits
settings.openai.rate_limit = 100  # requests per minute
settings.openai.cost_limit = 10.0  # dollars per hour
```

### Routing Configuration

```python
# Configure intelligent routing
settings.routing.enabled = True
settings.routing.routing_strategy = "performance"  # or "cost", "quality", "speed"
settings.routing.cost_optimization = True
settings.routing.performance_tracking = True

# Custom routing rules
settings.routing.routing_rules = {
    "privacy_sensitive": {
        "priority": ["ollama", "oss20b"],
        "fallback": "ollama"
    },
    "cost_priority": {
        "priority": ["ollama", "anthropic", "openai"],
        "fallback": "ollama"
    }
}
```

## 🤖 Agent System

### Creating Custom Agents

```python
from ai_framework.core import BaseAgent, AgentConfig, AgentType

class CustomAnalysisAgent(BaseAgent):
    def __init__(self, config: AgentConfig, llm_manager, model_router):
        super().__init__(config, llm_manager, model_router)

    def _initialize_agent(self):
        """Initialize agent-specific components."""
        self.analysis_tools = self._load_analysis_tools()

    async def execute_task(self, task):
        """Execute analysis task."""
        # Implement task execution logic
        result = await self._analyze_data(task.data)
        return {
            "analysis_result": result,
            "confidence": 0.95,
            "metadata": {"agent": "custom_analysis"}
        }

    def get_capabilities(self):
        """Return agent capabilities."""
        return ["data_analysis", "statistical_analysis", "pattern_recognition"]

# Register agent with orchestrator
agent_config = AgentConfig(
    agent_id="custom_analysis_001",
    agent_type=AgentType.ANALYSIS,
    name="Custom Analysis Agent",
    description="Advanced data analysis capabilities",
    capabilities=["data_analysis", "statistical_analysis"],
    preferred_providers=[LLMProvider.OPENAI, LLMProvider.CLAUDE]
)

agent = CustomAnalysisAgent(agent_config, llm_manager, model_router)
await orchestrator.register_agent(agent)
```

### Agent Orchestration

```python
# Submit task to orchestrator
task = Task(
    task_id="analysis_001",
    task_type="analysis",
    description="Analyze customer feedback data",
    priority=TaskPriority.HIGH,
    requirements=TaskRequirements(
        task_type=TaskType.ANALYSIS,
        complexity=TaskComplexity.COMPLEX,
        max_tokens=2000
    )
)

task_id = await orchestrator.submit_task(task)

# Monitor task status
status = await orchestrator.get_task_status(task_id)
print(f"Task status: {status['status']}")

# Get orchestration overview
overview = await orchestrator.get_orchestration_status()
print(f"Active agents: {overview['active_agents']}")
print(f"Queued tasks: {overview['queued_tasks']}")
```

## 🧠 Memory Management

### Conversation Memory

```python
from ai_framework.core import MemoryManager

memory_manager = MemoryManager()

# Store conversation
conversation_id = await memory_manager.store_conversation(
    conversation_id="conv_001",
    participants=["user", "assistant"],
    messages=[
        {"role": "user", "content": "What is AI?"},
        {"role": "assistant", "content": "AI is artificial intelligence..."}
    ],
    context_summary="Discussion about AI basics",
    entities_mentioned=["artificial intelligence", "machine learning"],
    topics_discussed=["AI fundamentals", "technology"]
)

# Retrieve conversation context
context = await memory_manager.get_conversation_context(
    conversation_id="conv_001",
    max_tokens=1000
)

# Search memories
memories = await memory_manager.search_memories(
    query="artificial intelligence",
    memory_type=MemoryType.CONVERSATION,
    tags=["AI", "fundamentals"]
)
```

### Entity Tracking

```python
# Store entity
entity_id = await memory_manager.store_entity(
    entity_type="person",
    name="John Doe",
    attributes={"age": 30, "occupation": "engineer"},
    relationships=[
        {"type": "works_at", "target": "Tech Corp"},
        {"type": "specializes_in", "target": "machine learning"}
    ],
    source="conversation_001",
    confidence=0.9
)

# Search entities
entities = await memory_manager.search_entities(
    query="machine learning",
    entity_type="person"
)
```

## 🔍 Vector Database Integration

### ChromaDB Integration

```python
from ai_framework.vector_db import ChromaManager

chroma_manager = ChromaManager(
    collection_name="ai_framework",
    embedding_dimension=1536
)

# Store documents
documents = [
    {"id": "doc1", "content": "AI is transforming industries...", "metadata": {"source": "research"}},
    {"id": "doc2", "content": "Machine learning algorithms...", "metadata": {"source": "paper"}}
]

await chroma_manager.store_documents(documents)

# Search similar documents
results = await chroma_manager.search(
    query="artificial intelligence applications",
    n_results=5
)

# Update collection
await chroma_manager.update_document(
    document_id="doc1",
    content="Updated AI content...",
    metadata={"updated": True}
)
```

## 📊 Monitoring & Analytics

### Performance Metrics

```python
from ai_framework.monitoring import MetricsCollector

metrics = MetricsCollector()

# Track LLM performance
await metrics.track_llm_request(
    provider="openai",
    model="gpt-4",
    latency=2.5,
    tokens_used=150,
    cost=0.0045,
    success=True
)

# Get performance summary
summary = await metrics.get_performance_summary(
    time_range="24h",
    providers=["openai", "anthropic", "ollama"]
)

print(f"Total requests: {summary['total_requests']}")
print(f"Average latency: {summary['avg_latency']:.2f}s")
print(f"Total cost: ${summary['total_cost']:.4f}")
```

### Health Checks

```python
from ai_framework.monitoring import HealthChecker

health_checker = HealthChecker()

# Check provider health
provider_health = await health_checker.check_provider_health()
for provider, status in provider_health.items():
    print(f"{provider}: {'✅' if status['healthy'] else '❌'}")

# Check system health
system_health = await health_checker.check_system_health()
print(f"Memory usage: {system_health['memory']['percent_used']:.1f}%")
print(f"CPU usage: {system_health['cpu']['percent_used']:.1f}%")
```

## 🔐 Security Features

### Authentication

```python
from ai_framework.security import AuthManager

auth_manager = AuthManager()

# Create user
user = await auth_manager.create_user(
    username="john_doe",
    email="john@example.com",
    password="secure_password",
    role="analyst"
)

# Authenticate user
token = await auth_manager.authenticate_user(
    username="john_doe",
    password="secure_password"
)

# Verify token
user_info = await auth_manager.verify_token(token)
print(f"Authenticated user: {user_info['username']}")
```

### Rate Limiting

```python
from ai_framework.security import RateLimiter

rate_limiter = RateLimiter(
    default_limit=100,  # requests per minute
    burst_limit=200
)

# Check rate limit
is_allowed = await rate_limiter.is_allowed(
    client_id="user_123",
    endpoint="/api/generate"
)

if not is_allowed:
    retry_after = await rate_limiter.get_retry_after("user_123")
    print(f"Rate limit exceeded. Retry after {retry_after} seconds")
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_llm_integration.py
pytest tests/test_agents.py
pytest tests/test_frameworks.py

# Run with coverage
pytest --cov=ai_framework --cov-report=html

# Run performance tests
pytest tests/test_performance.py -v
```

### Test Examples

```python
import pytest
from ai_framework.core import LLMManager

@pytest.mark.asyncio
async def test_openai_integration():
    """Test OpenAI integration."""
    llm_manager = LLMManager()

    response = await llm_manager.generate(
        prompt="Hello, world!",
        provider="openai",
        model="gpt-3.5-turbo"
    )

    assert response.text is not None
    assert len(response.text) > 0
    assert response.provider == "openai"

@pytest.mark.asyncio
async def test_model_routing():
    """Test intelligent model routing."""
    model_router = ModelRouter()

    requirements = TaskRequirements(
        task_type=TaskType.ANALYSIS,
        complexity=TaskComplexity.COMPLEX,
        privacy_sensitive=False,
        cost_priority=True
    )

    decision = await model_router.route_request(
        request=LLMRequest(prompt="Analyze this data"),
        requirements=requirements
    )

    assert decision.provider in ["ollama", "anthropic", "openai"]
    assert decision.confidence > 0.5
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports
EXPOSE 8000 8001

# Run the application
CMD ["uvicorn", "ai_framework.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  ai-framework:
    build: .
    ports:
      - "8000:8000"
      - "8001:8001"
    environment:
      - DATABASE_TYPE=postgresql
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
      - DATABASE_NAME=ai_framework
      - DATABASE_USERNAME=ai_user
      - DATABASE_PASSWORD=ai_password
    depends_on:
      - postgres
      - redis
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=ai_framework
      - POSTGRES_USER=ai_user
      - POSTGRES_PASSWORD=ai_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-framework
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-framework
  template:
    metadata:
      labels:
        app: ai-framework
    spec:
      containers:
      - name: ai-framework
        image: ai-framework:latest
        ports:
        - containerPort: 8000
        - containerPort: 8001
        env:
        - name: DATABASE_TYPE
          value: "postgresql"
        - name: DATABASE_HOST
          value: "postgres-service"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: ai-framework-service
spec:
  selector:
    app: ai-framework
  ports:
  - name: http
    port: 8000
    targetPort: 8000
  - name: websocket
    port: 8001
    targetPort: 8001
  type: LoadBalancer
```

## 📚 API Documentation

### FastAPI Endpoints

The framework provides a comprehensive REST API:

- **POST** `/api/generate` - Generate text with automatic provider selection
- **POST** `/api/stream` - Stream text generation
- **POST** `/api/function-call` - Execute function calling
- **GET** `/api/providers` - List available providers
- **GET** `/api/models` - List available models
- **POST** `/api/agents/register` - Register new agent
- **POST** `/api/tasks/submit` - Submit task for execution
- **GET** `/api/tasks/{task_id}` - Get task status
- **GET** `/api/memory/search` - Search memories
- **GET** `/api/health` - Health check
- **GET** `/api/metrics` - Performance metrics

### WebSocket Endpoints

- **WS** `/ws/chat` - Real-time chat interface
- **WS** `/ws/stream` - Streaming text generation
- **WS** `/ws/monitoring` - Real-time monitoring data

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd ai_framework

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linting
black .
isort .
flake8 .

# Run type checking
mypy .

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Full Documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/ai-framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/ai-framework/discussions)
- **Email**: support@ai-framework.com

## 🙏 Acknowledgments

- OpenAI for GPT models
- Anthropic for Claude models
- Ollama for local model deployment
- The open-source AI community

---

**Built with ❤️ for the AI community**
