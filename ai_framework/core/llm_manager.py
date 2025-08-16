"""
LLM Manager - Multi-Provider AI Integration

This module provides a unified interface for multiple LLM providers:
- OpenAI (GPT-4, GPT-4-turbo, GPT-3.5-turbo)
- Ollama (local models: Llama3.1, Mistral, CodeLlama)
- Claude (Anthropic models)
- OSS-20B (local deployment)

Features:
- Streaming responses
- Function calling
- Cost tracking and optimization
- Automatic retry with exponential backoff
- Rate limiting and queue management
- Response caching
- Health monitoring
"""

import asyncio
import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import redis.asyncio as redis

# Provider-specific imports
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    OLLAMA = "ollama"
    CLAUDE = "claude"
    OSS20B = "oss20b"


@dataclass
class LLMRequest:
    """Standardized LLM request format."""
    prompt: str
    provider: LLMProvider | None = None
    model: str | None = None
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: list[str] = field(default_factory=list)
    functions: list[dict[str, Any]] | None = None
    function_call: str | dict[str, str] | None = None
    stream: bool = False
    user_id: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Standardized LLM response format."""
    content: str
    provider: LLMProvider
    model: str
    tokens_used: int
    cost: float
    latency: float
    timestamp: datetime
    request_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    function_calls: list[dict[str, Any]] | None = None
    finish_reason: str | None = None


@dataclass
class ProviderConfig:
    """Configuration for each LLM provider."""
    api_key: str | None = None
    base_url: str | None = None
    timeout: int = 30
    max_retries: int = 3
    rate_limit: int = 100  # requests per minute
    cost_per_1k_tokens: float = 0.0
    enabled: bool = True


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.health_status = "unknown"
        self.last_health_check = None
        self.request_count = 0
        self.error_count = 0
        self.total_cost = 0.0
        self.total_tokens = 0

    @abstractmethod
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from the provider."""
        pass

    @abstractmethod
    async def stream_response(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream a response from the provider."""
        pass

    @abstractmethod
    async def function_call(self, request: LLMRequest) -> LLMResponse:
        """Execute a function call with the provider."""
        pass

    async def health_check(self) -> bool:
        """Check the health of the provider."""
        try:
            # Simple health check - can be overridden by subclasses
            self.health_status = "healthy"
            self.last_health_check = datetime.now(UTC)
            return True
        except Exception as e:
            logger.error(f"Health check failed for {self.__class__.__name__}: {e}")
            self.health_status = "unhealthy"
            return False

    def get_metrics(self) -> dict[str, Any]:
        """Get provider metrics."""
        return {
            "health_status": self.health_status,
            "last_health_check": self.last_health_check,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "error_rate": self.error_count / max(self.request_count, 1)
        }


class OpenAIProvider(BaseProvider):
    """OpenAI API provider implementation."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available. Install with: pip install openai")

        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout
        )

        # Default cost per 1K tokens for OpenAI models
        self.model_costs = {
            "gpt-4": 0.03,
            "gpt-4-turbo": 0.01,
            "gpt-4-32k": 0.06,
            "gpt-3.5-turbo": 0.002,
            "gpt-3.5-turbo-16k": 0.003
        }

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate a response using OpenAI."""
        start_time = time.time()

        try:
            # Prepare OpenAI-specific parameters
            openai_params = {
                "model": request.model or "gpt-4",
                "messages": [{"role": "user", "content": request.prompt}],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "frequency_penalty": request.frequency_penalty,
                "presence_penalty": request.presence_penalty,
                "stop": request.stop_sequences if request.stop_sequences else None
            }

            # Add function calling if specified
            if request.functions:
                openai_params["functions"] = request.functions
                openai_params["function_call"] = request.function_call or "auto"

            # Make API call
            response = await self.client.chat.completions.create(**openai_params)

            # Calculate metrics
            latency = time.time() - start_time
            tokens_used = response.usage.total_tokens
            cost = self._calculate_cost(tokens_used, openai_params["model"])

            # Update provider metrics
            self.request_count += 1
            self.total_cost += cost
            self.total_tokens += tokens_used

            # Extract function calls if present
            function_calls = None
            if response.choices[0].message.function_call:
                function_calls = [response.choices[0].message.function_call.model_dump()]

            return LLMResponse(
                content=response.choices[0].message.content or "",
                provider=LLMProvider.OPENAI,
                model=openai_params["model"],
                tokens_used=tokens_used,
                cost=cost,
                latency=latency,
                timestamp=datetime.now(UTC),
                request_id=response.id,
                function_calls=function_calls,
                finish_reason=response.choices[0].finish_reason
            )

        except Exception as e:
            self.error_count += 1
            logger.error(f"OpenAI API error: {e}")
            raise

    async def stream_response(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream a response using OpenAI."""
        try:
            openai_params = {
                "model": request.model or "gpt-4",
                "messages": [{"role": "user", "content": request.prompt}],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "stream": True
            }

            stream = await self.client.chat.completions.create(**openai_params)

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            self.error_count += 1
            logger.error(f"OpenAI streaming error: {e}")
            raise

    async def function_call(self, request: LLMRequest) -> LLMResponse:
        """Execute a function call using OpenAI."""
        if not request.functions:
            raise ValueError("Functions must be specified for function calling")

        # This is essentially the same as generate_response for OpenAI
        return await self.generate_response(request)

    def _calculate_cost(self, tokens: int, model: str) -> float:
        """Calculate cost for OpenAI API usage."""
        base_cost = self.model_costs.get(model, 0.01)  # Default fallback
        return (tokens / 1000) * base_cost


class OllamaProvider(BaseProvider):
    """Ollama local provider implementation."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not OLLAMA_AVAILABLE:
            raise ImportError("Ollama package not available. Install with: pip install ollama")

        self.base_url = config.base_url or "http://localhost:11434"
        self.available_models = []
        self._load_available_models()

        # Ollama models are free (local), so cost is 0
        self.config.cost_per_1k_tokens = 0.0

    def _load_available_models(self):
        """Load available Ollama models."""
        try:
            models = ollama.list()
            self.available_models = [model['name'] for model in models['models']]
            logger.info(f"Available Ollama models: {self.available_models}")
        except Exception as e:
            logger.warning(f"Could not load Ollama models: {e}")
            self.available_models = []

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate a response using Ollama."""
        start_time = time.time()

        try:
            model = request.model or "llama3.1:8b"

            # Prepare Ollama parameters
            ollama_params = {
                "model": model,
                "prompt": request.prompt,
                "options": {
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                    "num_predict": request.max_tokens
                }
            }

            # Make API call
            response = ollama.generate(**ollama_params)

            # Calculate metrics
            latency = time.time() - start_time
            tokens_used = len(response['response'].split())  # Approximate token count
            cost = 0.0  # Ollama is free

            # Update provider metrics
            self.request_count += 1
            self.total_cost += cost
            self.total_tokens += tokens_used

            return LLMResponse(
                content=response['response'],
                provider=LLMProvider.OLLAMA,
                model=model,
                tokens_used=tokens_used,
                cost=cost,
                latency=latency,
                timestamp=datetime.now(UTC),
                request_id=response.get('id', hashlib.md5(f"{time.time()}".encode()).hexdigest()),
                finish_reason="stop"
            )

        except Exception as e:
            self.error_count += 1
            logger.error(f"Ollama API error: {e}")
            raise

    async def stream_response(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream a response using Ollama."""
        try:
            model = request.model or "llama3.1:8b"

            # Ollama streaming
            stream = ollama.generate(
                model=model,
                prompt=request.prompt,
                stream=True,
                options={
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                    "num_predict": request.max_tokens
                }
            )

            for chunk in stream:
                if 'response' in chunk:
                    yield chunk['response']

        except Exception as e:
            self.error_count += 1
            logger.error(f"Ollama streaming error: {e}")
            raise

    async def function_call(self, request: LLMRequest) -> LLMResponse:
        """Execute a function call using Ollama."""
        # Ollama doesn't natively support function calling, so we'll simulate it
        # by including function definitions in the prompt
        enhanced_prompt = self._enhance_prompt_for_function_calling(request.prompt, request.functions)

        # Create a new request with the enhanced prompt
        enhanced_request = LLMRequest(
            prompt=enhanced_prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        return await self.generate_response(enhanced_request)

    def _enhance_prompt_for_function_calling(self, prompt: str, functions: list[dict[str, Any]] | None) -> str:
        """Enhance prompt to include function calling instructions."""
        if not functions:
            return prompt

        function_definitions = "\n\nAvailable functions:\n"
        for func in functions:
            function_definitions += f"- {func['name']}: {func['description']}\n"

        function_definitions += "\nPlease respond with the function name and parameters in JSON format."

        return prompt + function_definitions


class ClaudeProvider(BaseProvider):
    """Claude (Anthropic) provider implementation."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic package not available. Install with: pip install anthropic")

        self.client = AsyncAnthropic(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout
        )

        # Default cost per 1K tokens for Claude models
        self.model_costs = {
            "claude-3.5-sonnet-20241022": 0.003,
            "claude-3.5-haiku-20240307": 0.00025,
            "claude-3-opus-20240229": 0.015
        }

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate a response using Claude."""
        start_time = time.time()

        try:
            model = request.model or "claude-3.5-sonnet-20241022"

            # Prepare Claude parameters
            claude_params = {
                "model": model,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "messages": [{"role": "user", "content": request.prompt}]
            }

            # Make API call
            response = await self.client.messages.create(**claude_params)

            # Calculate metrics
            latency = time.time() - start_time
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = self._calculate_cost(tokens_used, model)

            # Update provider metrics
            self.request_count += 1
            self.total_cost += cost
            self.total_tokens += tokens_used

            return LLMResponse(
                content=response.content[0].text,
                provider=LLMProvider.CLAUDE,
                model=model,
                tokens_used=tokens_used,
                cost=cost,
                latency=latency,
                timestamp=datetime.now(UTC),
                request_id=response.id,
                finish_reason="end_turn"
            )

        except Exception as e:
            self.error_count += 1
            logger.error(f"Claude API error: {e}")
            raise

    async def stream_response(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream a response using Claude."""
        try:
            model = request.model or "claude-3.5-sonnet-20241022"

            stream = await self.client.messages.create(
                model=model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                messages=[{"role": "user", "content": request.prompt}],
                stream=True
            )

            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    yield chunk.delta.text

        except Exception as e:
            self.error_count += 1
            logger.error(f"Claude streaming error: {e}")
            raise

    async def function_call(self, request: LLMRequest) -> LLMResponse:
        """Execute a function call using Claude."""
        # Claude supports tools (function calling) natively
        if not request.functions:
            raise ValueError("Functions must be specified for function calling")

        start_time = time.time()

        try:
            model = request.model or "claude-3.5-sonnet-20241022"

            # Convert functions to Claude tools format
            tools = []
            for func in request.functions:
                tool = {
                    "type": "function",
                    "function": {
                        "name": func["name"],
                        "description": func["description"],
                        "input_schema": func.get("parameters", {})
                    }
                }
                tools.append(tool)

            response = await self.client.messages.create(
                model=model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                messages=[{"role": "user", "content": request.prompt}],
                tools=tools,
                tool_choice="auto"
            )

            # Calculate metrics
            latency = time.time() - start_time
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = self._calculate_cost(tokens_used, model)

            # Update provider metrics
            self.request_count += 1
            self.total_cost += cost
            self.total_tokens += tokens_used

            # Extract tool calls if present
            function_calls = None
            if response.content[0].type == "tool_use":
                function_calls = [{
                    "name": response.content[0].name,
                    "arguments": response.content[0].input
                }]

            return LLMResponse(
                content=response.content[0].text if response.content[0].type == "text" else "",
                provider=LLMProvider.CLAUDE,
                model=model,
                tokens_used=tokens_used,
                cost=cost,
                latency=latency,
                timestamp=datetime.now(UTC),
                request_id=response.id,
                function_calls=function_calls,
                finish_reason="end_turn"
            )

        except Exception as e:
            self.error_count += 1
            logger.error(f"Claude function call error: {e}")
            raise

    def _calculate_cost(self, tokens: int, model: str) -> float:
        """Calculate cost for Claude API usage."""
        base_cost = self.model_costs.get(model, 0.003)  # Default fallback
        return (tokens / 1000) * base_cost


class LLMManager:
    """Main LLM manager that coordinates all providers."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.providers: dict[LLMProvider, BaseProvider] = {}
        self.cache = None
        self.rate_limiters = {}
        self.health_check_interval = 60  # seconds

        # Initialize providers
        self._initialize_providers()

        # Setup cache if Redis is available
        self._setup_cache()

        # Start health monitoring
        asyncio.create_task(self._health_monitor())

    def _initialize_providers(self):
        """Initialize all configured LLM providers."""
        try:
            # OpenAI provider
            if self.config.get("openai", {}).get("enabled", True):
                openai_config = ProviderConfig(
                    api_key=self.config["openai"].get("api_key"),
                    base_url=self.config["openai"].get("base_url"),
                    timeout=self.config["openai"].get("timeout", 30),
                    rate_limit=self.config["openai"].get("rate_limit", 100),
                    cost_per_1k_tokens=self.config["openai"].get("cost_per_1k_tokens", 0.01)
                )
                if openai_config.api_key:
                    self.providers[LLMProvider.OPENAI] = OpenAIProvider(openai_config)
                    logger.info("OpenAI provider initialized")

            # Ollama provider
            if self.config.get("ollama", {}).get("enabled", True):
                ollama_config = ProviderConfig(
                    base_url=self.config["ollama"].get("base_url", "http://localhost:11434"),
                    timeout=self.config["ollama"].get("timeout", 30),
                    rate_limit=self.config["ollama"].get("rate_limit", 1000),
                    cost_per_1k_tokens=0.0
                )
                try:
                    self.providers[LLMProvider.OLLAMA] = OllamaProvider(ollama_config)
                    logger.info("Ollama provider initialized")
                except Exception as e:
                    logger.warning(f"Ollama provider initialization failed: {e}")

            # Claude provider
            if self.config.get("claude", {}).get("enabled", True):
                claude_config = ProviderConfig(
                    api_key=self.config["claude"].get("api_key"),
                    base_url=self.config["claude"].get("base_url"),
                    timeout=self.config["claude"].get("timeout", 30),
                    rate_limit=self.config["claude"].get("rate_limit", 50),
                    cost_per_1k_tokens=self.config["claude"].get("cost_per_1k_tokens", 0.003)
                )
                if claude_config.api_key:
                    self.providers[LLMProvider.CLAUDE] = ClaudeProvider(claude_config)
                    logger.info("Claude provider initialized")

            # OSS-20B provider (will be initialized separately)
            if self.config.get("oss20b", {}).get("enabled", False):
                logger.info("OSS-20B provider will be initialized separately")

        except Exception as e:
            logger.error(f"Provider initialization failed: {e}")

    def _setup_cache(self):
        """Setup Redis cache if available."""
        try:
            redis_url = self.config.get("cache", {}).get("redis_url")
            if redis_url:
                self.cache = redis.from_url(redis_url)
                logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis cache setup failed: {e}")
            self.cache = None

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate a response using the best available provider."""
        # Check cache first
        if self.cache and not request.stream:
            cached_response = await self._get_cached_response(request)
            if cached_response:
                return cached_response

        # Select provider
        provider = self._select_provider(request)
        if not provider:
            raise ValueError("No suitable provider available")

        # Check rate limits
        if not await self._check_rate_limit(provider):
            raise Exception(f"Rate limit exceeded for {provider.__class__.__name__}")

        try:
            # Generate response
            response = await provider.generate_response(request)

            # Cache response
            if self.cache and not request.stream:
                await self._cache_response(request, response)

            return response

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            # Try fallback provider if available
            return await self._fallback_response(request, provider)

    async def stream_response(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream a response using the best available provider."""
        provider = self._select_provider(request)
        if not provider:
            raise ValueError("No suitable provider available")

        # Check rate limits
        if not await self._check_rate_limit(provider):
            raise Exception(f"Rate limit exceeded for {provider.__class__.__name__}")

        try:
            async for chunk in provider.stream_response(request):
                yield chunk
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            raise

    async def function_call(self, request: LLMRequest) -> LLMResponse:
        """Execute a function call using the best available provider."""
        # Prefer providers with native function calling support
        request.provider = request.provider or self._select_provider_for_function_calling(request)

        return await self.generate_response(request)

    def _select_provider(self, request: LLMRequest) -> BaseProvider | None:
        """Select the best provider for the request."""
        # If provider is specified, use it if available
        if request.provider and request.provider in self.providers:
            return self.providers[request.provider]

        # Select based on task type and requirements
        if request.metadata.get("privacy_sensitive") and LLMProvider.OLLAMA in self.providers:
            # Prefer local providers for privacy
            return self.providers[LLMProvider.OLLAMA]

        if request.metadata.get("cost_priority"):
            # Prefer cost-effective providers
            if LLMProvider.OLLAMA in self.providers:
                return self.providers[LLMProvider.OLLAMA]
            if LLMProvider.CLAUDE in self.providers:
                return self.providers[LLMProvider.CLAUDE]

        # Default priority: OpenAI > Claude > Ollama
        for provider in [LLMProvider.OPENAI, LLMProvider.CLAUDE, LLMProvider.OLLAMA]:
            if provider in self.providers:
                return self.providers[provider]

        return None

    def _select_provider_for_function_calling(self, request: LLMRequest) -> LLMProvider | None:
        """Select the best provider for function calling."""
        # OpenAI and Claude have native function calling
        if LLMProvider.OPENAI in self.providers:
            return LLMProvider.OPENAI
        if LLMProvider.CLAUDE in self.providers:
            return LLMProvider.CLAUDE

        # Ollama can simulate function calling
        if LLMProvider.OLLAMA in self.providers:
            return LLMProvider.OLLAMA

        return None

    async def _check_rate_limit(self, provider: BaseProvider) -> bool:
        """Check if provider is within rate limits."""
        provider_name = provider.__class__.__name__

        if provider_name not in self.rate_limiters:
            self.rate_limiters[provider_name] = {
                "requests": [],
                "limit": provider.config.rate_limit
            }

        limiter = self.rate_limiters[provider_name]
        now = time.time()

        # Remove old requests (older than 1 minute)
        RATE_LIMIT_WINDOW = 60  # 1 minute in seconds
        limiter["requests"] = [req_time for req_time in limiter["requests"] if now - req_time < RATE_LIMIT_WINDOW]

        # Check if we're under the limit
        if len(limiter["requests"]) < limiter["limit"]:
            limiter["requests"].append(now)
            return True

        return False

    async def _fallback_response(self, request: LLMRequest, failed_provider: BaseProvider) -> LLMResponse:
        """Try to get a response from a fallback provider."""
        available_providers = [p for p in self.providers.values() if p != failed_provider]

        for provider in available_providers:
            try:
                return await provider.generate_response(request)
            except Exception as e:
                logger.warning(f"Fallback provider {provider.__class__.__name__} failed: {e}")
                continue

        raise Exception("All providers failed")

    async def _get_cached_response(self, request: LLMRequest) -> LLMResponse | None:
        """Get cached response if available."""
        if not self.cache:
            return None

        cache_key = self._generate_cache_key(request)
        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return LLMResponse(**json.loads(cached_data))
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")

        return None

    async def _cache_response(self, request: LLMRequest, response: LLMResponse):
        """Cache the response."""
        if not self.cache:
            return

        cache_key = self._generate_cache_key(request)
        cache_ttl = self.config.get("cache", {}).get("ttl", 3600)  # 1 hour default

        try:
            await self.cache.setex(
                cache_key,
                cache_ttl,
                json.dumps(response.__dict__, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    def _generate_cache_key(self, request: LLMRequest) -> str:
        """Generate a cache key for the request."""
        key_data = {
            "prompt": request.prompt,
            "model": request.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"llm_response:{hashlib.md5(key_string.encode()).hexdigest()}"

    async def _health_monitor(self):
        """Monitor health of all providers."""
        while True:
            for provider_name, provider in self.providers.items():
                try:
                    await provider.health_check()
                except Exception as e:
                    logger.error(f"Health check failed for {provider_name}: {e}")

            await asyncio.sleep(self.health_check_interval)

    def get_available_models(self) -> dict[LLMProvider, list[str]]:
        """Get available models for each provider."""
        models = {}

        if LLMProvider.OPENAI in self.providers:
            models[LLMProvider.OPENAI] = [
                "gpt-4", "gpt-4-turbo", "gpt-4-32k",
                "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
            ]

        if LLMProvider.OLLAMA in self.providers:
            ollama_provider = self.providers[LLMProvider.OLLAMA]
            models[LLMProvider.OLLAMA] = ollama_provider.available_models or [
                "llama3.1:8b", "llama3.1:70b", "mistral:7b", "codellama:13b"
            ]

        if LLMProvider.CLAUDE in self.providers:
            models[LLMProvider.CLAUDE] = [
                "claude-3.5-sonnet-20241022", "claude-3.5-haiku-20240307",
                "claude-3-opus-20240229"
            ]

        return models

    def calculate_cost(self, tokens: int, model: str, provider: LLMProvider) -> float:
        """Calculate cost for a given number of tokens."""
        if provider not in self.providers:
            return 0.0

        provider_instance = self.providers[provider]
        return provider_instance.config.cost_per_1k_tokens * (tokens / 1000)

    async def health_check(self) -> dict[str, Any]:
        """Check health of all providers."""
        health_status = {}

        for provider_name, provider in self.providers.items():
            try:
                is_healthy = await provider.health_check()
                health_status[provider_name.value] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "metrics": provider.get_metrics()
                }
            except Exception as e:
                health_status[provider_name.value] = {
                    "status": "error",
                    "error": str(e)
                }

        return health_status

    def get_metrics(self) -> dict[str, Any]:
        """Get overall system metrics."""
        total_requests = sum(p.request_count for p in self.providers.values())
        total_errors = sum(p.error_count for p in self.providers.values())
        total_cost = sum(p.total_cost for p in self.providers.values())
        total_tokens = sum(p.total_tokens for p in self.providers.values())

        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "error_rate": total_errors / max(total_requests, 1),
            "providers": {
                provider_name.value: provider.get_metrics()
                for provider_name, provider in self.providers.items()
            }
        }
