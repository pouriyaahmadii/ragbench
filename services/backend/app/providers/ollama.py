import json
import time
from typing import List, Optional
import httpx

from app.providers.protocols import (
    EmbeddingProvider,
    EmbeddingResult,
    EmbeddingMetadata,
    ChatGenerationProvider,
    GenerationConfig,
    GenerationResult,
    Message,
    ProviderError,
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderConfigurationError,
    ProviderResponseError,
)
from app.config import Settings


class OllamaEmbeddingProvider:
    """Ollama local embedding provider adapter."""

    def __init__(
        self,
        base_url: str,
        model: str,
        dimension: int,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._dimension = dimension
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_identifier(self) -> str:
        return f"ollama:{self.model}"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def _normalize_error(self, error: Exception, operation: str) -> ProviderError:
        if isinstance(error, httpx.TimeoutException):
            return ProviderTimeoutError("ollama", self.timeout)
        elif isinstance(error, httpx.HTTPStatusError):
            if error.response.status_code == 429:
                retry_after = error.response.headers.get("Retry-After")
                return ProviderRateLimitError(
                    "ollama", float(retry_after) if retry_after else None
                )
            return ProviderResponseError(
                "ollama", str(error), error.response.status_code
            )
        elif isinstance(error, httpx.ConnectError):
            return ProviderConfigurationError(
                "ollama", f"Cannot connect to Ollama at {self.base_url}"
            )
        return ProviderError(
            f"Ollama {operation} failed: {error}",
            provider="ollama",
            original_error=error,
        )

    async def embed(self, texts: List[str]) -> "EmbeddingResult":
        if not texts:
            from app.providers.protocols import EmbeddingResult, EmbeddingMetadata
            return EmbeddingResult(
                vectors=[],
                metadata=EmbeddingMetadata(
                    provider="ollama",
                    model=self.model,
                    version="latest",
                    dimension=self._dimension,
                )
            )

        client = await self._get_client()
        vectors = []

        for text in texts:
            payload = {"model": self.model, "prompt": text}
            last_error = None

            for attempt in range(self.max_retries):
                try:
                    response = await client.post("/api/embeddings", json=payload)
                    response.raise_for_status()
                    data = response.json()
                    embedding = data.get("embedding", [])
                    if not embedding:
                        raise ProviderResponseError(
                            "ollama", "Empty embedding returned", 500
                        )
                    if len(embedding) != self._dimension:
                        raise ProviderResponseError(
                            "ollama",
                            f"Dimension mismatch: expected {self._dimension}, got {len(embedding)}",
                            500,
                        )
                    vectors.append(embedding)
                    break
                except Exception as e:
                    last_error = self._normalize_error(e, "embed")
                    if not last_error.retryable or attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise last_error

        from app.providers.protocols import EmbeddingResult, EmbeddingMetadata
        return EmbeddingResult(
            vectors=vectors,
            metadata=EmbeddingMetadata(
                provider="ollama",
                model=self.model,
                version="latest",
                dimension=self._dimension,
            )
        )


class OllamaGenerationProvider:
    """Ollama local generation provider adapter."""

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float = 120.0,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def model_identifier(self) -> str:
        return f"ollama:{self.model}"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def _normalize_error(self, error: Exception, operation: str) -> ProviderError:
        if isinstance(error, httpx.TimeoutException):
            return ProviderTimeoutError("ollama", self.timeout)
        elif isinstance(error, httpx.HTTPStatusError):
            if error.response.status_code == 429:
                retry_after = error.response.headers.get("Retry-After")
                return ProviderRateLimitError(
                    "ollama", float(retry_after) if retry_after else None
                )
            return ProviderResponseError(
                "ollama", str(error), error.response.status_code
            )
        elif isinstance(error, httpx.ConnectError):
            return ProviderConfigurationError(
                "ollama", f"Cannot connect to Ollama at {self.base_url}"
            )
        return ProviderError(
            f"Ollama {operation} failed: {error}",
            provider="ollama",
            original_error=error,
        )

    async def generate(
        self,
        messages: List["Message"],
        config: "GenerationConfig"
    ) -> "GenerationResult":
        # Convert messages to Ollama chat format
        prompt_parts = []
        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")

        prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"

        client = await self._get_client()
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": config.temperature,
            "num_predict": config.max_tokens,
            "stream": False,
        }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await client.post("/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                text = data.get("response", "")
                if not text:
                    raise ProviderResponseError("ollama", "Empty response", 500)

                from app.providers.protocols import GenerationResult
                return GenerationResult(
                    text=text.strip(),
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                    },
                    metadata={
                        "provider": "ollama",
                        "model": self.model,
                        "version": "latest",
                        "prompt_version": config.prompt_version,
                        "finish_reason": data.get("done_reason", "stop"),
                    }
                )
            except Exception as e:
                last_error = self._normalize_error(e, "generate")
                if not last_error.retryable or attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise last_error