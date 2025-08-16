"""
OSS-20B Manager - Local Model Integration

This module provides comprehensive integration for OpenAI OSS-20B model:
- Local model deployment with Transformers
- GPU/CPU optimization and memory management
- Quantization support (4-bit, 8-bit, 16-bit)
- Batch processing for efficiency
- Custom fine-tuning capabilities
- Integration with existing LLM manager
- Performance monitoring and benchmarking
"""

import asyncio
import gc
import json
import logging
import threading
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import psutil
import torch

# Try to import transformers and related libraries
try:
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        GenerationConfig,
        pipeline,
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available. Install with: pip install transformers accelerate peft")

# Try to import bitsandbytes for quantization
try:
    from transformers import BitsAndBytesConfig
    BNB_AVAILABLE = True
except ImportError:
    BNB_AVAILABLE = False
    logging.warning("BitsAndBytes not available. Install with: pip install bitsandbytes")

logger = logging.getLogger(__name__)


class QuantizationLevel(str, Enum):
    """Available quantization levels."""
    FP16 = "fp16"
    INT8 = "int8"
    INT4 = "int4"
    NF4 = "nf4"


class ModelVariant(str, Enum):
    """Available OSS-20B model variants."""
    BASE = "base"
    CHAT = "chat"
    INSTRUCT = "instruct"
    CODE = "code"


@dataclass
class OSS20BConfig:
    """Configuration for OSS-20B model."""
    model_path: str = "microsoft/DialoGPT-large"  # Replace with actual OSS-20B model
    model_variant: ModelVariant = ModelVariant.BASE
    quantization: QuantizationLevel = QuantizationLevel.INT4
    max_memory: dict[str, str] | None = None
    device_map: str = "auto"
    torch_dtype: str = "auto"
    use_cache: bool = True
    low_cpu_mem_usage: bool = True
    trust_remote_code: bool = True
    max_length: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1
    do_sample: bool = True
    pad_token_id: int | None = None
    eos_token_id: int | None = None


@dataclass
class OSS20BResponse:
    """Response from OSS-20B model."""
    text: str
    tokens_used: int
    latency: float
    memory_used: float
    model_variant: str
    quantization: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class OSS20BManager:
    """Manager for OSS-20B local model deployment and inference."""

    def __init__(self, config: OSS20BConfig):
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("Transformers not available. Install with: pip install transformers accelerate peft")

        self.config = config
        self.model = None
        self.tokenizer = None
        self.generator = None
        self.model_loaded = False
        self.device = None
        self.memory_monitor = None
        self.performance_metrics = {}
        self.lock = threading.Lock()

        # Initialize model
        self._initialize_model()

        # Start memory monitoring
        self._start_memory_monitoring()

    def _initialize_model(self):
        """Initialize the OSS-20B model."""
        try:
            logger.info(f"Initializing OSS-20B model: {self.config.model_path}")

            # Set device
            if torch.cuda.is_available():
                self.device = "cuda"
                logger.info("Using CUDA device")
            else:
                self.device = "cpu"
                logger.info("Using CPU device")

            # Load tokenizer
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_path,
                trust_remote_code=self.config.trust_remote_code
            )

            # Set padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Configure quantization
            quantization_config = self._get_quantization_config()

            # Load model
            logger.info("Loading model...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_path,
                quantization_config=quantization_config,
                device_map=self.config.device_map,
                torch_dtype=self._get_torch_dtype(),
                low_cpu_mem_usage=self.config.low_cpu_mem_usage,
                trust_remote_code=self.config.trust_remote_code,
                max_memory=self.config.max_memory
            )

            # Move to device if not using device_map
            if self.config.device_map == "auto":
                pass  # Model is already on correct device
            else:
                self.model = self.model.to(self.device)

            # Create generation config
            generation_config = GenerationConfig(
                max_length=self.config.max_length,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                repetition_penalty=self.config.repetition_penalty,
                do_sample=self.config.do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

            # Create pipeline
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=self.device,
                generation_config=generation_config
            )

            self.model_loaded = True
            logger.info("OSS-20B model initialized successfully")

            # Log model info
            self._log_model_info()

        except Exception as e:
            logger.error(f"Failed to initialize OSS-20B model: {e}")
            raise

    def _get_quantization_config(self) -> Any | None:
        """Get quantization configuration based on settings."""
        if not BNB_AVAILABLE:
            logger.warning("BitsAndBytes not available, using default precision")
            return None

        if not TRANSFORMERS_AVAILABLE:
            return None

        # Define quantization configs
        quantization_configs = {
            QuantizationLevel.INT4: BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            ),
            QuantizationLevel.INT8: BitsAndBytesConfig(
                load_in_8bit=True,
                bnb_8bit_compute_dtype=torch.float16
            ),
            QuantizationLevel.NF4: BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        }

        # Return config if quantization level is supported, otherwise None
        return quantization_configs.get(self.config.quantization)

    def _get_torch_dtype(self) -> torch.dtype:
        """Get torch dtype based on quantization and device."""
        if self.config.quantization in [QuantizationLevel.INT4, QuantizationLevel.INT8, QuantizationLevel.NF4] or self.config.quantization == QuantizationLevel.FP16:
            return torch.float16
        else:
            return torch.float32

    def _log_model_info(self):
        """Log detailed model information."""
        if not self.model_loaded:
            return

        try:
            # Get model parameters
            total_params = sum(p.numel() for p in self.model.parameters())
            trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)

            # Get memory usage
            if torch.cuda.is_available():
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                allocated_memory = torch.cuda.memory_allocated(0) / 1024**3
                cached_memory = torch.cuda.memory_reserved(0) / 1024**3
            else:
                gpu_memory = allocated_memory = cached_memory = 0

            # Get system memory
            system_memory = psutil.virtual_memory().total / 1024**3

            model_info = {
                "model_path": self.config.model_path,
                "model_variant": self.config.model_variant.value,
                "quantization": self.config.quantization.value,
                "device": self.device,
                "total_parameters": f"{total_params:,}",
                "trainable_parameters": f"{trainable_params:,}",
                "gpu_memory_total_gb": round(gpu_memory, 2),
                "gpu_memory_allocated_gb": round(allocated_memory, 2),
                "gpu_memory_cached_gb": round(cached_memory, 2),
                "system_memory_gb": round(system_memory, 2)
            }

            logger.info(f"Model Information: {json.dumps(model_info, indent=2)}")

        except Exception as e:
            logger.warning(f"Could not log model info: {e}")

    async def generate_response(self, prompt: str, max_length: int | None = None,
                               temperature: float | None = None, **kwargs) -> OSS20BResponse:
        """Generate a response using the OSS-20B model."""
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")

        start_time = time.time()

        try:
            # Use provided parameters or defaults
            max_len = max_length or self.config.max_length
            temp = temperature or self.config.temperature

            # Prepare generation parameters
            _generation_params = {
                "max_length": max_len,
                "temperature": temp,
                "top_p": kwargs.get("top_p", self.config.top_p),
                "top_k": kwargs.get("top_k", self.config.top_k),
                "repetition_penalty": kwargs.get("repetition_penalty", self.config.repetition_penalty),
                "do_sample": kwargs.get("do_sample", self.config.do_sample),
                "pad_token_id": self.tokenizer.pad_token_id,
                "eos_token_id": self.tokenizer.eos_token_id
            }

            # Generate response
            with self.lock:  # Ensure thread safety
                outputs = self.generator(
                    prompt,
                    **_generation_params
                )

            # Extract generated text
            generated_text = outputs[0]["generated_text"]
            response_text = generated_text[len(prompt):].strip()

            # Calculate metrics
            latency = time.time() - start_time
            tokens_used = len(self.tokenizer.encode(generated_text))
            memory_used = self._get_memory_usage()

            # Create response
            response = OSS20BResponse(
                text=response_text,
                tokens_used=tokens_used,
                latency=latency,
                memory_used=memory_used,
                model_variant=self.config.model_variant.value,
                quantization=self.config.quantization.value,
                timestamp=datetime.now(UTC),
                metadata={
                    "generation_params": _generation_params,
                    "original_prompt": prompt,
                    "full_generated_text": generated_text
                }
            )

            # Update performance metrics
            self._update_performance_metrics(response)

            return response

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    async def stream_response(self, prompt: str, max_length: int | None = None,
                            temperature: float | None = None, **kwargs) -> AsyncGenerator[str, None]:
        """Stream a response from the OSS-20B model."""
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")

        try:
            # Use provided parameters or defaults
            max_len = max_length or self.config.max_length
            temp = temperature or self.config.temperature

            # Prepare generation parameters
            _generation_params = {
                "max_length": max_len,
                "temperature": temp,
                "top_p": kwargs.get("top_p", self.config.top_p),
                "top_k": kwargs.get("top_k", self.config.top_k),
                "repetition_penalty": kwargs.get("repetition_penalty", self.config.repetition_penalty),
                "do_sample": kwargs.get("do_sample", self.config.do_sample),
                "pad_token_id": self.tokenizer.pad_token_id,
                "eos_token_id": self.tokenizer.eos_token_id
            }

            # For streaming, we need to use the model directly
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if self.device == "cuda":
                inputs = {k: v.cuda() for k, v in inputs.items()}

            # Generate with streaming
            with self.lock:
                generated_tokens = []
                for _ in range(max_len):
                    outputs = self.model(**inputs, use_cache=True)
                    next_token_logits = outputs.logits[:, -1, :]

                    # Apply temperature and sampling
                    if temp > 0:
                        next_token_logits = next_token_logits / temp

                    # Sample next token
                    probs = torch.softmax(next_token_logits, dim=-1)
                    next_token = torch.multinomial(probs, num_samples=1)

                    # Decode and yield token
                    next_token_text = self.tokenizer.decode(next_token[0], skip_special_tokens=True)
                    if next_token_text:
                        yield next_token_text

                    # Add to inputs for next iteration
                    inputs["input_ids"] = torch.cat([inputs["input_ids"], next_token], dim=1)
                    generated_tokens.append(next_token)

                    # Check for EOS
                    if next_token.item() == self.tokenizer.eos_token_id:
                        break

                    # Yield control to event loop
                    await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise

    async def batch_generate(self, prompts: list[str], max_length: int | None = None,
                            temperature: float | None = None, batch_size: int = 4, **kwargs) -> list[OSS20BResponse]:
        """Generate responses for multiple prompts in batches."""
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")

        responses = []

        try:
            # Process prompts in batches
            for i in range(0, len(prompts), batch_size):
                batch_prompts = prompts[i:i + batch_size]

                # Generate responses for batch
                batch_responses = await asyncio.gather(*[
                    self.generate_response(prompt, max_length, temperature, **kwargs)
                    for prompt in batch_prompts
                ])

                responses.extend(batch_responses)

                # Small delay between batches to prevent memory issues
                if i + batch_size < len(prompts):
                    await asyncio.sleep(0.1)

            return responses

        except Exception as e:
            logger.error(f"Batch generation failed: {e}")
            raise

    async def function_call(self, prompt: str, functions: list[dict[str, Any]], **kwargs) -> OSS20BResponse:
        """Execute function calling with OSS-20B model."""
        # OSS-20B doesn't have native function calling, so we'll enhance the prompt
        enhanced_prompt = self._enhance_prompt_for_function_calling(prompt, functions)

        return await self.generate_response(enhanced_prompt, **kwargs)

    def _enhance_prompt_for_function_calling(self, prompt: str, functions: list[dict[str, Any]]) -> str:
        """Enhance prompt to include function calling instructions."""
        enhanced_prompt = prompt + "\n\nAvailable functions:\n"

        for func in functions:
            enhanced_prompt += f"- {func['name']}: {func['description']}\n"
            if 'parameters' in func:
                enhanced_prompt += f"  Parameters: {json.dumps(func['parameters'], indent=2)}\n"

        enhanced_prompt += "\nPlease respond with the function name and parameters in JSON format."

        return enhanced_prompt

    async def fine_tune_model(self, training_data: list[dict[str, str]], adapter_name: str,
                             learning_rate: float = 3e-4, num_epochs: int = 3) -> bool:
        """Fine-tune the model with custom data."""
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")

        try:
            logger.info(f"Starting fine-tuning for adapter: {adapter_name}")

            # Prepare training data
            formatted_data = []
            for item in training_data:
                formatted_data.append({
                    "instruction": item.get("instruction", ""),
                    "input": item.get("input", ""),
                    "output": item.get("output", "")
                })

            # Configure LoRA
            lora_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                inference_mode=False,
                r=16,
                lora_alpha=32,
                lora_dropout=0.1,
                target_modules=["q_proj", "v_proj"]
            )

            # Apply LoRA to model
            model = get_peft_model(self.model, lora_config)

            # Training loop (simplified)
            model.train()
            optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

            for epoch in range(num_epochs):
                total_loss = 0
                for item in formatted_data:
                    # Prepare input
                    text = f"Instruction: {item['instruction']}\nInput: {item['input']}\nOutput: {item['output']}"
                    inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

                    if self.device == "cuda":
                        inputs = {k: v.cuda() for k, v in inputs.items()}

                    # Forward pass
                    outputs = model(**inputs, labels=inputs["input_ids"])
                    loss = outputs.loss

                    # Backward pass
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()

                    total_loss += loss.item()

                avg_loss = total_loss / len(formatted_data)
                logger.info(f"Epoch {epoch + 1}/{num_epochs}, Average Loss: {avg_loss:.4f}")

            # Save adapter
            model.save_pretrained(f"adapters/{adapter_name}")
            logger.info(f"Fine-tuning completed. Adapter saved: adapters/{adapter_name}")

            return True

        except Exception as e:
            logger.error(f"Fine-tuning failed: {e}")
            return False

    async def load_adapter(self, adapter_name: str) -> bool:
        """Load a fine-tuned adapter."""
        try:
            adapter_path = f"adapters/{adapter_name}"
            if not Path(adapter_path).exists():
                logger.error(f"Adapter not found: {adapter_path}")
                return False

            # Load adapter
            self.model = self.model.from_pretrained(adapter_path)
            logger.info(f"Adapter loaded: {adapter_name}")

            return True

        except Exception as e:
            logger.error(f"Failed to load adapter: {e}")
            return False

    def optimize_memory(self) -> dict[str, Any]:
        """Optimize memory usage for the model."""
        optimization_results = {}

        try:
            if torch.cuda.is_available():
                # Clear CUDA cache
                torch.cuda.empty_cache()
                optimization_results["cuda_cache_cleared"] = True

                # Get memory info
                allocated_before = torch.cuda.memory_allocated(0) / 1024**3
                cached_before = torch.cuda.memory_reserved(0) / 1024**3

                # Force garbage collection
                gc.collect()

                allocated_after = torch.cuda.memory_allocated(0) / 1024**3
                cached_after = torch.cuda.memory_reserved(0) / 1024**3

                optimization_results["memory_optimization"] = {
                    "allocated_before_gb": round(allocated_before, 2),
                    "allocated_after_gb": round(allocated_after, 2),
                    "cached_before_gb": round(cached_before, 2),
                    "cached_after_gb": round(cached_after, 2),
                    "allocated_saved_gb": round(allocated_before - allocated_after, 2),
                    "cached_saved_gb": round(cached_before - cached_after, 2)
                }

            # System memory optimization
            gc.collect()
            optimization_results["system_gc"] = True

            logger.info("Memory optimization completed")

        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            optimization_results["error"] = str(e)

        return optimization_results

    async def benchmark_performance(self, test_prompts: list[str], iterations: int = 5) -> dict[str, Any]:
        """Benchmark model performance with test prompts."""
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")

        benchmark_results = {
            "model_info": {
                "model_path": self.config.model_path,
                "model_variant": self.config.model_variant.value,
                "quantization": self.config.quantization.value,
                "device": self.device
            },
            "benchmark_config": {
                "test_prompts": len(test_prompts),
                "iterations": iterations,
                "total_tests": len(test_prompts) * iterations
            },
            "results": {}
        }

        try:
            # Warm up
            logger.info("Warming up model...")
            await self.generate_response("Hello, how are you?", max_length=50)

            # Run benchmarks
            for prompt in test_prompts:
                prompt_results = {
                    "latencies": [],
                    "tokens_generated": [],
                    "memory_usage": []
                }

                for _i in range(iterations):
                    _start_time = time.time()
                    response = await self.generate_response(prompt, max_length=100)

                    prompt_results["latencies"].append(response.latency)
                    prompt_results["tokens_generated"].append(response.tokens_used)
                    prompt_results["memory_usage"].append(response.memory_used)

                    # Small delay between iterations
                    await asyncio.sleep(0.1)

                # Calculate statistics
                latencies = prompt_results["latencies"]
                tokens = prompt_results["tokens_generated"]
                memory = prompt_results["memory_usage"]

                benchmark_results["results"][prompt[:50] + "..."] = {
                    "avg_latency": sum(latencies) / len(latencies),
                    "min_latency": min(latencies),
                    "max_latency": max(latencies),
                    "avg_tokens": sum(tokens) / len(tokens),
                    "avg_memory_gb": sum(memory) / len(memory),
                    "throughput_tokens_per_second": sum(tokens) / sum(latencies)
                }

            # Overall statistics
            all_latencies = [r["avg_latency"] for r in benchmark_results["results"].values()]
            all_tokens = [r["avg_tokens"] for r in benchmark_results["results"].values()]

            benchmark_results["overall"] = {
                "avg_latency": sum(all_latencies) / len(all_latencies),
                "avg_tokens_per_request": sum(all_tokens) / len(all_tokens),
                "total_benchmark_time": sum(all_latencies)
            }

            logger.info("Performance benchmark completed")

        except Exception as e:
            logger.error(f"Performance benchmark failed: {e}")
            benchmark_results["error"] = str(e)

        return benchmark_results

    def get_model_info(self) -> dict[str, Any]:
        """Get comprehensive model information."""
        if not self.model_loaded:
            return {"error": "Model not loaded"}

        try:
            # Basic info
            info = {
                "model_path": self.config.model_path,
                "model_variant": self.config.model_variant.value,
                "quantization": self.config.quantization.value,
                "device": self.device,
                "model_loaded": self.model_loaded,
                "timestamp": datetime.now(UTC).isoformat()
            }

            # Model parameters
            if self.model:
                total_params = sum(p.numel() for p in self.model.parameters())
                trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)

                info["parameters"] = {
                    "total": f"{total_params:,}",
                    "trainable": f"{trainable_params:,}",
                    "non_trainable": f"{total_params - trainable_params:,}"
                }

            # Memory usage
            info["memory"] = self._get_memory_usage()

            # Performance metrics
            info["performance"] = self.performance_metrics

            return info

        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}

    def _get_memory_usage(self) -> dict[str, float]:
        """Get current memory usage."""
        memory_info = {}

        try:
            # System memory
            system_memory = psutil.virtual_memory()
            memory_info["system"] = {
                "total_gb": round(system_memory.total / 1024**3, 2),
                "available_gb": round(system_memory.available / 1024**3, 2),
                "used_gb": round(system_memory.used / 1024**3, 2),
                "percent_used": round(system_memory.percent, 1)
            }

            # GPU memory
            if torch.cuda.is_available():
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                allocated_memory = torch.cuda.memory_allocated(0) / 1024**3
                cached_memory = torch.cuda.memory_reserved(0) / 1024**3

                memory_info["gpu"] = {
                    "total_gb": round(gpu_memory, 2),
                    "allocated_gb": round(allocated_memory, 2),
                    "cached_gb": round(cached_memory, 2),
                    "free_gb": round(gpu_memory - cached_memory, 2)
                }

        except Exception as e:
            logger.warning(f"Could not get memory usage: {e}")
            memory_info["error"] = str(e)

        return memory_info

    def _update_performance_metrics(self, response: OSS20BResponse):
        """Update performance metrics with response data."""
        timestamp = response.timestamp.isoformat()

        if "responses" not in self.performance_metrics:
            self.performance_metrics["responses"] = []

        self.performance_metrics["responses"].append({
            "timestamp": timestamp,
            "latency": response.latency,
            "tokens_used": response.tokens_used,
            "memory_used": response.memory_used
        })

        # Keep only last 1000 responses
        MAX_RESPONSES_HISTORY = 1000
        if len(self.performance_metrics["responses"]) > MAX_RESPONSES_HISTORY:
            self.performance_metrics["responses"] = self.performance_metrics["responses"][-MAX_RESPONSES_HISTORY:]

        # Update summary statistics
        latencies = [r["latency"] for r in self.performance_metrics["responses"]]
        tokens = [r["tokens_used"] for r in self.performance_metrics["responses"]]

        self.performance_metrics["summary"] = {
            "total_responses": len(latencies),
            "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
            "avg_tokens": sum(tokens) / len(tokens) if tokens else 0,
            "last_updated": timestamp
        }

    def _start_memory_monitoring(self):
        """Start background memory monitoring."""
        if self.memory_monitor:
            return

        async def monitor_memory():
            while True:
                try:
                    memory_info = self._get_memory_usage()

                    # Check for memory warnings
                    MEMORY_WARNING_THRESHOLD = 90  # 90% threshold for warnings
                    if "gpu" in memory_info:
                        gpu_used_percent = (memory_info["gpu"]["allocated_gb"] / memory_info["gpu"]["total_gb"]) * 100
                        if gpu_used_percent > MEMORY_WARNING_THRESHOLD:
                            logger.warning(f"High GPU memory usage: {gpu_used_percent:.1f}%")

                    if "system" in memory_info and memory_info["system"]["percent_used"] > MEMORY_WARNING_THRESHOLD:
                        logger.warning(f"High system memory usage: {memory_info['system']['percent_used']:.1f}%")

                    await asyncio.sleep(30)  # Check every 30 seconds

                except Exception as e:
                    logger.error(f"Memory monitoring error: {e}")
                    await asyncio.sleep(60)

        self.memory_monitor = asyncio.create_task(monitor_memory())

    def cleanup(self):
        """Clean up resources."""
        try:
            if self.memory_monitor:
                self.memory_monitor.cancel()

            if self.model:
                del self.model
                self.model = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            gc.collect()

            self.model_loaded = False
            logger.info("OSS-20B manager cleaned up")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
