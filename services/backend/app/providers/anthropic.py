import asyncio
from typing import List, Optional
import httpx

from app.providers.protocols import (
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


class AnthropicGenerationProvider:
    """Anthropic Claude generation provider adapter.

    Note: Anthropic does not provide embedding models, only generation.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-haiku-20240307",
        timeout: float = 120.0,
        max_retries: int = 3,
        base_url: str = "https://api.anthropic.com/v1",
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def model_identifier(self) -> str:
        return f"anthropic:{self.model}"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
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
            return ProviderTimeoutError("anthropic", self.timeout)
        elif isinstance(error, httpx.HTTPStatusError):
            if error.response.status_code == 429:
                retry_after = error.response.headers.get("Retry-After")
                return ProviderRateLimitError(
                    "anthropic", float(retry_after) if retry_after else None
                )
            elif error.response.status_code == 401:
                return ProviderConfigurationError("anthropic", "Invalid API key")
            return ProviderResponseError(
                "anthropic", str(error), error.response.status_code
            )
        elif isinstance(error, httpx.ConnectError):
            return ProviderConfigurationError("anthropic", "Cannot connect to Anthropic API")
        return ProviderError(
            f"Anthropic {operation} failed: {error}",
            provider="anthropic",
            original_error=error,
        )

    def _convert_messages(self, messages: List["Message"]) -> List[dict]:
        """Convert internal messages to Anthropic format."""
        anthropic_messages = []
        system_prompt = None

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        return system_prompt, anthropic_messages

    async def generate(
        self,
        messages: List["Message"],
        config: "GenerationConfig"
    ) -> "GenerationResult":
        client = await self._get_client()

        system_prompt, anthropic_messages = self._convert_messages(messages)

        payload = {
            "model": self.model,
            "messages": anthropic_messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        if system_prompt:
            payload["system"] = system_prompt

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await self._client.post("/messages", json=payload)
                response.raise_for_status()
                data = response.json()

                if not data.get("content"):
                    raise ProviderResponseError("anthropic", "Empty response", 500)

                text = data["content"][0]["text"]
                if not text:
                    raise ProviderResponseError("anthropic", "Empty response text", 500)

                from app.providers.protocols import GenerationResult
                return GenerationResult(
                    text=text.strip(),
                    usage={
                        "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                        "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
                        "total_tokens": data.get("usage", {}).get("input_tokens", 0) +
                                        data.get("usage", {}).get("output_tokens", 0),
                    },
                    metadata={
                        "provider": "anthropic",
                        "model": self.model,
                        "version": "latest",
                        "prompt_version": config.prompt_version,
                        "finish_reason": data.get("stop_reason", "end_turn"),
                    }
                )
            except Exception as e:
                last_error = self._normalize_error(e, "generate")
                if not last_error.retryable or attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise last_error