"""Model registry.

Loads role→model assignments from registry.yaml and environment variables, then
builds ModelInfo objects and exposes their availability against the provider.
The registry is purely local and configuration-driven; no models are downloaded.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from config.settings import settings
from models.providers.base import ModelProvider
from models.providers.ollama import OllamaProvider
from models.schemas import ModelAvailability, ModelInfo

_REGISTRY_PATH = Path(__file__).resolve().parent / "registry.yaml"

# Environment override keys in order: role -> env var
_ENV_ROLE_MAP = {
    "general": "OLLAMA_GENERAL_MODEL",
    "reasoning": "OLLAMA_REASONING_MODEL",
    "coding": "OLLAMA_CODING_MODEL",
    "vision": "OLLAMA_VISION_MODEL",
    "embedding": "OLLAMA_EMBEDDING_MODEL",
}

# capabilities per known role
_ROLE_CAPS: dict[str, dict] = {
    "general": {
        "capabilities": ["text", "reasoning", "tool_calling"],
        "vision_support": False,
        "tool_support": True,
        "embedding_support": False,
    },
    "reasoning": {
        "capabilities": ["text", "reasoning"],
        "vision_support": False,
        "tool_support": False,
        "embedding_support": False,
    },
    "coding": {
        "capabilities": ["text", "coding", "tool_calling"],
        "vision_support": False,
        "tool_support": True,
        "embedding_support": False,
    },
    "vision": {
        "capabilities": ["text", "image", "vision"],
        "vision_support": True,
        "tool_support": False,
        "embedding_support": False,
    },
    "embedding": {
        "capabilities": ["embedding"],
        "vision_support": False,
        "tool_support": False,
        "embedding_support": True,
    },
}


def _role_model_name(role: str, yaml_roles: dict) -> str:
    env_name = getattr(settings, f"ollama_{role}_model", "")
    if env_name:
        return env_name
    return str(yaml_roles.get(role) or "")


class ModelRegistry:
    def __init__(self, provider: ModelProvider | None = None) -> None:
        self.provider: ModelProvider = provider or OllamaProvider()
        self._raw: dict = self._load_raw()
        self._models: dict[str, ModelInfo] = self._build()

    @staticmethod
    def _load_raw() -> dict:
        with open(_REGISTRY_PATH, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return data.get("roles", {})

    def _build(self) -> dict[str, ModelInfo]:
        models: dict[str, ModelInfo] = {}
        for role, raw in _ROLE_CAPS.items():
            model_name = _role_model_name(role, self._raw)
            if not model_name:
                continue
            info = ModelInfo(
                id=role,
                provider=self.provider.name,
                model_name=model_name,
                capabilities=list(raw["capabilities"]),
                vision_support=raw["vision_support"],
                tool_support=raw["tool_support"],
                embedding_support=raw["embedding_support"],
                enabled=True,
            )
            models[role] = info
        return models

    def all(self) -> list[ModelInfo]:
        return list(self._models.values())

    def get(self, role: str) -> ModelInfo | None:
        return self._models.get(role)

    def configured_roles(self) -> list[str]:
        return list(self._models.keys())

    async def availability(self) -> list[ModelAvailability]:
        """Check which configured models are actually available at the provider."""
        available_on_provider = await self._provider_model_names()
        result: list[ModelAvailability] = []
        for info in self.all():
            err: str | None = None
            name = info.model_name.split(":")[0]  # compare prefix w/o tag
            found = any(
                m.split(":")[0] == name or m == info.model_name
                for m in available_on_provider
            )
            if not found:
                err = (
                    f"Model '{info.model_name}' not found. "
                    f"Pull it with: ollama pull {info.model_name}"
                )
            result.append(ModelAvailability(info=info, available=found, error=err))
        return result

    async def _provider_model_names(self) -> list[str]:
        try:
            return await self.provider.list_models()
        except Exception:
            return []


_registry: ModelRegistry | None = None


def get_registry(provider: ModelProvider | None = None) -> ModelRegistry:
    """Return the (cached) model registry."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry(provider=provider)
    return _registry


def reset_registry() -> None:
    global _registry
    _registry = None
