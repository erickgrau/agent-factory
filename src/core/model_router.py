"""Model Router - Route tasks to appropriate LLM models"""
import os
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for a model provider"""
    name: str
    provider: str
    base_url: str
    api_key_env: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_tokens: int
    supports_reasoning: bool = False
    is_local: bool = False


class ModelRouter:
    """Routes tasks to appropriate models based on requirements"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.models: Dict[str, ModelConfig] = self._load_default_models()
        self.usage_stats: Dict[str, Dict] = {}
    
    def _load_default_models(self) -> Dict[str, ModelConfig]:
        """Load default model configurations"""
        return {
            # Local models (Ollama)
            "ollama/kimi-k2.5:cloud": ModelConfig(
                name="kimi-k2.5",
                provider="ollama",
                base_url="http://localhost:11434",
                api_key_env="",
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                max_tokens=128000,
                supports_reasoning=True,
                is_local=True
            ),
            "ollama/qwen3.5:latest": ModelConfig(
                name="qwen3.5",
                provider="ollama",
                base_url="http://localhost:11434",
                api_key_env="",
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                max_tokens=128000,
                is_local=True
            ),
            "ollama/deepseek-r1:32b": ModelConfig(
                name="deepseek-r1",
                provider="ollama",
                base_url="http://localhost:11434",
                api_key_env="",
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                max_tokens=32000,
                supports_reasoning=True,
                is_local=True
            ),
            
            # Cloud models
            "anthropic/claude-sonnet-4-6": ModelConfig(
                name="claude-sonnet-4-6",
                provider="anthropic",
                base_url="https://api.anthropic.com",
                api_key_env="ANTHROPIC_API_KEY",
                cost_per_1k_input=3.00,
                cost_per_1k_output=15.00,
                max_tokens=200000,
                supports_reasoning=True
            ),
            "anthropic/claude-opus-4-7": ModelConfig(
                name="claude-opus-4-7",
                provider="anthropic",
                base_url="https://api.anthropic.com",
                api_key_env="ANTHROPIC_API_KEY",
                cost_per_1k_input=15.00,
                cost_per_1k_output=75.00,
                max_tokens=200000,
                supports_reasoning=True
            ),
            "openai-codex/gpt-4o": ModelConfig(
                name="gpt-4o",
                provider="openai",
                base_url="https://api.openai.com",
                api_key_env="OPENAI_API_KEY",
                cost_per_1k_input=5.00,
                cost_per_1k_output=15.00,
                max_tokens=128000
            ),
            "google/gemini-3.1-pro-preview": ModelConfig(
                name="gemini-3.1-pro",
                provider="google",
                base_url="https://generativelanguage.googleapis.com",
                api_key_env="GOOGLE_API_KEY",
                cost_per_1k_input=3.50,
                cost_per_1k_output=10.50,
                max_tokens=2000000
            ),
        }
    
    def select_model(
        self,
        task_type: str = "general",
        complexity: int = 3,
        priority: str = "normal",
        budget_remaining: float = None,
        required_capabilities: List[str] = None
    ) -> Optional[str]:
        """Select best model for task"""
        
        # Tier-based selection
        if complexity >= 4 or task_type in ["security-review", "architecture"]:
            tier = "premium"
        elif complexity >= 2:
            tier = "standard"
        else:
            tier = "cheap"
        
        # Filter available models
        available = []
        for model_id, config in self.models.items():
            # Check API key exists for cloud models
            if not config.is_local:
                if config.api_key_env and not os.getenv(config.api_key_env):
                    continue
            
            # Check capabilities
            if required_capabilities:
                if "reasoning" in required_capabilities and not config.supports_reasoning:
                    continue
            
            available.append((model_id, config))
        
        if not available:
            return None
        
        # Sort by cost (prefer cheaper for non-premium)
        if tier == "cheap":
            available.sort(key=lambda x: x[1].cost_per_1k_input)
        
        # Return first available
        return available[0][0]
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """Get configuration for model"""
        return self.models.get(model_id)
    
    def estimate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for token usage"""
        config = self.models.get(model_id)
        if not config:
            return 0.0
        
        input_cost = (input_tokens / 1000) * config.cost_per_1k_input
        output_cost = (output_tokens / 1000) * config.cost_per_1k_output
        return input_cost + output_cost
    
    def record_usage(self, model_id: str, input_tokens: int, output_tokens: int):
        """Record actual usage for stats"""
        if model_id not in self.usage_stats:
            self.usage_stats[model_id] = {
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0.0
            }
        
        cost = self.estimate_cost(model_id, input_tokens, output_tokens)
        self.usage_stats[model_id]["calls"] += 1
        self.usage_stats[model_id]["input_tokens"] += input_tokens
        self.usage_stats[model_id]["output_tokens"] += output_tokens
        self.usage_stats[model_id]["total_cost"] += cost
    
    def get_stats(self) -> Dict:
        """Get usage statistics"""
        total_cost = sum(s["total_cost"] for s in self.usage_stats.values())
        total_calls = sum(s["calls"] for s in self.usage_stats.values())
        
        return {
            "total_cost": round(total_cost, 2),
            "total_calls": total_calls,
            "by_model": self.usage_stats
        }


class ProviderAdapter:
    """Base adapter for LLM providers"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
    
    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate response from model"""
        raise NotImplementedError
    
    async def stream(self, prompt: str):
        """Stream response"""
        raise NotImplementedError


class OllamaAdapter(ProviderAdapter):
    """Adapter for local Ollama models"""
    
    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate using Ollama"""
        # Implementation would use httpx or requests
        # For now, return placeholder
        return f"[Ollama: {self.config.name}] Generated response"


class AnthropicAdapter(ProviderAdapter):
    """Adapter for Anthropic models"""
    
    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate using Anthropic API"""
        return f"[Anthropic: {self.config.name}] Generated response"
