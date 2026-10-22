import asyncio
from typing import List, Optional
import httpx

from app.providers.protocols import (
    EmbeddingProvider,
    EmbeddingResult,
    EmbeddingMetadata,
    ProviderError,
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderConfigurationError,
    ProviderResponseError,
)


class CohereEmbeddingProvider:
    """Cohere embedding provider adapter.

    Note: Cohere only provides embedding models, not chat generation.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "embed-english-v3.0",
        dimension: int = 1024,
        timeout: float = 60.0,
        max_retries: int = 3,
        base_url: str = "https://api.cohere.ai/v1",
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
        return f"cohere:{self.model}"

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
            return ProviderTimeoutError("cohere", self.timeout)
        elif isinstance(error, httpx.HTTPStatusError):
            if error.response.status_code == 429:
                retry_after = error.response.headers.get("Retry-After")
                return ProviderRateLimitError(
                    "cohere", float(retry_after) if retry_after else None
                )
            elif error.response.status_code == 401:
                return ProviderConfigurationError("cohere", "Invalid API key")
            return ProviderResponseError(
                "cohere", str(error), error.response.status_code
            )
        elif isinstance(error, httpx.ConnectError):
            return ProviderConfigurationError("cohere", "Cannot connect to Cohere API")
        return ProviderError(
            f"Cohere {operation} failed: {error}",
            provider="cohere",
            original_error=error,
        )

    async def embed(self, texts: List[str]) -> "EmbeddingResult":
        if not texts:
            from app.providers.protocols import EmbeddingResult, EmbeddingMetadata
            return EmbeddingResult(
                vectors=[],
                metadata=EmbeddingMetadata(
                    provider="cohere",
                    model=self.model,
                    version="latest",
                    dimension=self._dimension,
                )
            )

        client = await self._get_client()
        vectors = []
        batch_size = 96  # Cohere max batch size

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            payload = {
                "model": self.model,
                "texts": batch,
                "input_type": "search_document",
            }

            last_error = None
            for attempt in range(self.max_retries):
                try:
                    response = await self._client.post("/embed", json=payload)
                    response.raise_for_status()
                    data = response.json()

                    batch_embeddings = data["embeddings"]
                    for embedding in batch_embeddings:
                        if len(embedding) != self._dimension:
                            raise ProviderResponseError(
                                "cohere",
                                f"Dimension mismatch: expected {self._dimension}, got {len(embedding)}",
                                500,
                            )
                    vectors.extend(batch_embeddings)
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
                provider="cohere",
                model=self.model,
                version="latest",
                dimension=self._dimension,
                usage={"total_tokens": len(texts) * 100},  # Approximate
            )
        )