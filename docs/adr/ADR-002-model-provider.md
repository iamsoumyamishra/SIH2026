# ADR-002: Model Provider Abstraction and Rule-Based Router

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

AGENTS.md mandates that the agent must never couple directly to Ollama, and that
the architecture must allow a future `VLLMProvider` without changing the agent.

## Decision

1. **`ModelProvider` (ABC)** in `models/providers/base.py` defines
   `generate`, `stream`, `health_check`, `list_models`, and `embeddings`.
   Only this interface is used by higher layers.

2. **`OllamaProvider`** implements the interface against the local
   `OLLAMA_BASE_URL` (localhost only). All Ollama traffic flows through it.

3. **`ModelRegistry`** reads role→model assignments from `registry.yaml` plus
   `OLLAMA_*` environment overrides. It builds `ModelInfo` objects and can check
   live availability. No model is downloaded automatically.

4. **`ModelRouter`** is a deterministic rule-based router (vision → vision model,
   code keywords → coding model, complex reasoning → reasoning model, default →
   general). A `ModelUnavailableError` is raised when no configured model exists,
   prompting the user to pull one — the system never silently falls back to a
   cloud service.

## Consequences

- Adding `VLLMProvider` only requires a new class and a registry wiring change.
- The MVP uses a simple, explainable router; an ML router can replace it later
  behind the same `route()` interface.
- Model names are configuration, not code.
