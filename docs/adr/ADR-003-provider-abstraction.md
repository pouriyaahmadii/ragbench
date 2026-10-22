# ADR-003: Provider Abstraction for Embeddings and Generation

**Status:** Accepted  
**Date:** 2026-10-22  
**Deciders:** Architecture Team  
**Technical Story:** RAGBench initialization

## Context

RAGBench must support multiple embedding and generation providers:
- **Deterministic Mock** (required for CI, demo, development)
- **Local models** via Ollama (optional, no API costs)
- **External APIs** (OpenAI, Anthropic, Cohere, etc.)

The pipeline must not depend on any specific provider's SDK types, error formats, or quirks.

## Decision

### Provider Protocols (Interfaces)

Define minimal, stable protocols in `services/backend/app/providers/protocols.py`:

```python
from typing import Protocol, runtime_checkable
from pydantic import BaseModel

# --- Embeddings ---

class EmbeddingResult(BaseModel):
    vectors: list[list[float]]
    metadata: "EmbeddingMetadata"

class EmbeddingMetadata(BaseModel):
    provider: str
    model: str
    version: str
    dimension: int
    usage: dict | None = None  # tokens, cost if available

@runtime_checkable
class EmbeddingProvider(Protocol):
    async def embed(self, texts: list[str]) -> EmbeddingResult: ...
    
    @property
    def dimension(self) -> int: ...
    
    @property
    def model_identifier(self) -> str: ...  # e.g., "mock:v1", "ollama:nomic-embed-text"

# --- Generation ---

class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class GenerationConfig(BaseModel):
    model: str
    temperature: float = 0.0
    max_tokens: int = 1024
    prompt_version: str = "1.0"
    extra: dict = {}

class GenerationResult(BaseModel):
    text: str
    usage: dict | None = None  # prompt_tokens, completion_tokens, total_tokens
    metadata: dict = {}  # provider-specific (finish_reason, etc.)

@runtime_checkable
class ChatGenerationProvider(Protocol):
    async def generate(
        self, 
        messages: list[Message], 
        config: GenerationConfig
    ) -> GenerationResult: ...
    
    @property
    def model_identifier(self) -> str: ...
```

### Provider Implementations

| Provider | Embedding | Generation | Use Case |
|----------|-----------|------------|----------|
| `MockEmbeddingProvider` | ✅ | - | CI, demo, unit tests |
| `MockGenerationProvider` | - | ✅ | CI, demo, unit tests |
| `OllamaEmbeddingProvider` | ✅ | - | Local embeddings (optional) |
| `OllamaGenerationProvider` | - | ✅ | Local generation (optional) |
| `OpenAIEmbeddingProvider` | ✅ | - | Production (optional) |
| `OpenAIGenerationProvider` | - | ✅ | Production (optional) |
| `AnthropicGenerationProvider` | - | ✅ | Production (optional) |
| `CohereEmbeddingProvider` | ✅ | - | Production (optional) |

### Provider Factory

```python
# services/backend/app/providers/factory.py
def get_embedding_provider(config: EmbeddingConfig) -> EmbeddingProvider:
    if config.provider == "mock" or settings.MOCK_MODE:
        return MockEmbeddingProvider(dimension=config.dimension)
    elif config.provider == "ollama":
        return OllamaEmbeddingProvider(base_url=config.base_url, model=config.model)
    elif config.provider == "openai":
        return OpenAIEmbeddingProvider(api_key=config.api_key, model=config.model)
    else:
        raise ConfigurationError(f"Unknown embedding provider: {config.provider}")

def get_generation_provider(config: GenerationConfig) -> ChatGenerationProvider:
    if config.provider == "mock" or settings.MOCK_MODE:
        return MockGenerationProvider(fixtures=config.fixtures)
    elif config.provider == "ollama":
        return OllamaGenerationProvider(base_url=config.base_url, model=config.model)
    elif config.provider == "openai":
        return OpenAIGenerationProvider(api_key=config.api_key, model=config.model)
    elif config.provider == "anthropic":
        return AnthropicGenerationProvider(api_key=config.api_key, model=config.model)
    else:
        raise ConfigurationError(f"Unknown generation provider: {config.provider}")
```

### Configuration

Provider selection via validated Pydantic Settings:

```python
class EmbeddingConfig(BaseModel):
    provider: Literal["mock", "ollama", "openai", "cohere"] = "mock"
    model: str = "mock"
    version: str = "1.0"
    dimension: int = 384
    batch_size: int = 100
    timeout_seconds: int = 60
    base_url: str | None = None  # For Ollama
    api_key: str | None = None   # For external (loaded from env)

class GenerationConfig(BaseModel):
    provider: Literal["mock", "ollama", "openai", "anthropic"] = "mock"
    model: str = "mock"
    version: str = "1.0"
    temperature: float = 0.0
    max_tokens: int = 1024
    prompt_version: str = "1.0"
    base_url: str | None = None
    api_key: str | None = None
```

### Mock Provider Behavior

**MockEmbeddingProvider:**
- Deterministic: same input text → same vector (hash-based)
- Configurable dimension (default 384)
- Returns `EmbeddingMetadata(provider="mock", model="mock", version="1.0", dimension=N)`
- Zero latency (or configurable simulated latency)

**MockGenerationProvider:**
- Fixture-based: returns pre-defined answers for known questions
- Falls back to "The provided documents do not contain sufficient evidence..." for unknown
- Includes citations in format `[chunk-uuid]` for known answers
- Returns `GenerationMetadata(provider="mock", model="mock", version="1.0")`

### Validation at Boundaries

Before using provider results:
1. **Embeddings:** `len(vectors) == len(texts)`, `all(len(v) == expected_dim)`, `all(isfinite(x))`
2. **Generation:** Parse response into `GenerationResult`; validate citations format
3. **Errors:** Normalize provider exceptions → `ProviderError(provider, original_error, retryable)`

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Direct SDK usage in pipeline | Couples pipeline to provider; hard to test; no Mock without mocking SDK |
| Adapter pattern with base class | Protocol is lighter; no inheritance; structural typing |
| LangChain/LlamaIndex wrappers | Framework lock-in; adds dependency; obscures provider details |
| Single `ModelProvider` for both | Embeddings and generation have different contracts, configs, lifecycles |
| Config-driven dynamic imports | Explicit factory clearer; easier to test; no import-time side effects |

## Consequences

### Positive
- **Zero-cost Mock mode:** CI and demo work without any API keys or model downloads
- **Provider parity:** Same pipeline code works with Mock, Ollama, OpenAI, etc.
- **Testability:** Unit tests use Mock providers; contract tests verify all implementations
- **Experiment integrity:** Provider identity recorded with every embedding/generation
- **Security:** API keys never in frontend; only in server-side Settings

### Negative
- **Abstraction maintenance:** New provider features require protocol updates
- **Feature parity:** Not all provider features exposed (e.g., logprobs, streaming)
- **Mock limitations:** Mock embeddings not semantic; Mock generation not intelligent

### Risks
| Risk | Mitigation |
|------|------------|
| Protocol drift | Contract tests for every provider; CI runs against all configured |
| Mock too simple | Design Mock to exercise full pipeline contracts; document limitations |
| External API changes | Pin SDK versions; integration tests with real providers (optional) |
| Credential leakage | Settings validation; secret scan; frontend never receives keys |

## Implementation Notes

1. **Protocol Location:** `services/backend/app/providers/protocols.py` (no external deps)
2. **Implementations:** `services/backend/app/providers/implementations/`
3. **Factory:** `services/backend/app/providers/factory.py`
4. **Config:** `services/backend/app/config/providers.py` (Pydantic Settings)
5. **Contract Tests:** `services/backend/tests/contract/test_embedding_provider.py`, `test_generation_provider.py`
6. **Mock Fixtures:** `services/backend/tests/fixtures/mock_generation.json` (question → answer mapping)

## Related ADRs
- ADR-001: Initial Technology Stack
- ADR-002: RAG Pipeline Boundaries
- ADR-004: Evaluation Metrics Strategy