import time
import asyncio
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


class OpenAIEmbeddingProvider:
    """OpenAI embedding provider adapter."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimension: int = 1536,
        timeout: float = 60.0,
        max_retries: int = 3,
        base_url: str = "https://api.openai.com/v1",
    ):
        self.api_key = api_key
        self.model = model
        self._dimension = dimension
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_identifier(self) -> str:
        return f"openai:{self.model}"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def _normalize_error(self, error: Exception, operation: str) -> ProviderError:
        if isinstance(error, httpx.TimeoutException):
            return ProviderTimeoutError("openai", self.timeout)
        elif isinstance(error, httpx.HTTPStatusError):
            if error.response.status_code == 429:
                retry_after = error.response.headers.get("Retry-After")
                return ProviderRateLimitError(
                    "openai", float(retry_after) if retry_after else None
                )
            elif error.response.status_code == 401:
                return ProviderConfigurationError("openai", "Invalid API key")
            return ProviderResponseError(
                "openai", str(error), error.response.status_code
            )
        elif isinstance(error, httpx.ConnectError):
            return ProviderConfigurationError("openai", "Cannot connect to OpenAI API")
        return ProviderError(
            f"OpenAI {operation} failed: {error}",
            provider="openai",
            original_error=error,
        )

    async def embed(self, texts: List[str]) -> "EmbeddingResult":
        if not texts:
            from app.providers.protocols import EmbeddingResult, EmbeddingMetadata
            return EmbeddingResult(
                vectors=[],
                metadata=EmbeddingMetadata(
                    provider="openai",
                    model=self.model,
                    version="latest",
                    dimension=self._dimension,
                )
            )

        client = await self._get_client()
        vectors = []
        batch_size = 100  # OpenAI max batch size

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            payload = {"model": self.model, "input": batch}

            last_error = None
            for attempt in range(self.max_retries):
                try:
                    response = await client.post("/embeddings", json=payload)
                    response.raise_for_status()
                    data = response.json()

                    batch_vectors = [item["embedding"] for item in data["data"]]
                    for embedding in batch_vectors:
                        if len(embedding) != self._dimension:
                            raise ProviderResponseError(
                                "openai",
                                f"Dimension mismatch: expected {self._dimension}, got {len(embedding)}",
                                500,
                            )
                    vectors.extend(batch_vectors)
                    break
                except Exception as e:
                    last_error = self._normalize_error(e, "embed")
                    if not last_error.retryable or attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
            else:
                raise last_error

        from app.providers.protocols import EmbeddingResult, EmbeddingMetadata
        return EmbeddingResult(
            vectors=vectors,
            metadata=EmbeddingMetadata(
                provider="openai",
                model=self.model,
                version="latest",
                dimension=self._dimension,
                usage={"total_tokens": len(texts) * 100},  # Approximate
            )
        )


class OpenAIGenerationProvider:
    """OpenAI chat generation provider adapter."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout: float = 120.0,
        max_retries: int = 3,
        base_url: str = "https://api.openai.com/v1",
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def model_identifier(self) -> str:
        return f"openai:{self.model}"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def _normalize_error(self, error: Exception, operation: str) -> ProviderError:
        if isinstance(error, httpx.TimeoutException):
            return ProviderTimeoutError("openai", self.timeout)
        elif isinstance(error, httpx.HTTPStatusError):
            if error.response.status_code == 429:
                retry_after = error.response.headers.get("Retry-After")
                return ProviderRateLimitError(
                    "openai", float(retry_after) if retry_after else None
                )
            elif error.response.status_code == 401:
                return ProviderConfigurationError("openai", "Invalid API key")
            return ProviderResponseError(
                "openai", str(error), error.response.status_code
            )
        elif isinstance(error, httpx.ConnectError):
            return ProviderConfigurationError("openai", "Cannot connect to OpenAI API")
        return ProviderError(
            f"OpenAI {operation} failed: {error}",
            provider="openai",
            original_error=error,
        )

    async def generate(
        self,
        messages: List["Message"],
        config: "GenerationConfig"
    ) -> "GenerationResult":
        client = await self._get_client()

        # Convert messages to OpenAI format
        openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        payload = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await client.post("/chat/completions", json=payload)
                response.raise_for_status()
                data = response.json()

                choice = data["choices"][0]
                text = choice["message"]["content"]
                if not text:
                    raise ProviderResponseError("openai", "Empty response", 500)

                from app.providers.protocols import GenerationResult
                return GenerationResult(
                    text=text.strip(),
                    usage={
                        "prompt_tokens": data["usage"]["prompt_tokens"],
                        "completion_tokens": data["usage"]["completion_tokens"],
                        "total_tokens": data["usage"]["total_tokens"],
                    },
                    metadata={
                        "provider": "openai",
                        "model": self.model,
                        "version": "latest",
                        "prompt_version": config.prompt_version,
                        "finish_reason": choice.get("finish_reason", "stop"),
                    }
                )
            except Exception as e:
                last_error = self._normalize_error(e, "generate")
                if not last_error.retryable or attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise last_error