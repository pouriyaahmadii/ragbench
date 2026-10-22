from typing import Protocol, List, Optional, Dict, Any
from pydantic import BaseModel, Field
from abc import abstractmethod


class EmbeddingResult(BaseModel):
    vectors: List[List[float]] = Field(description="List of embedding vectors")
    metadata: "EmbeddingMetadata" = Field(description="Provider metadata")


class EmbeddingMetadata(BaseModel):
    provider: str = Field(description="Provider name (mock, ollama, openai, cohere)")
    model: str = Field(description="Model identifier")
    version: str = Field(description="Model version")
    dimension: int = Field(description="Embedding dimension")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="Token usage if available")


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers. All implementations must be async."""

    @property
    def dimension(self) -> int:
        """Expected embedding dimension for this provider."""
        ...

    @property
    def model_identifier(self) -> str:
        """Unique identifier for this provider/model combination."""
        ...

    @abstractmethod
    async def embed(self, texts: List[str]) -> EmbeddingResult:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            EmbeddingResult with vectors and metadata

        Raises:
            ProviderError: On provider-specific failures
            ValueError: On invalid input
        """
        ...


class Message(BaseModel):
    role: str = Field(description="Message role: system, user, assistant")
    content: str = Field(description="Message content")


class GenerationConfig(BaseModel):
    model: str = Field(description="Model identifier")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, gt=0)
    prompt_version: str = Field(default="1.0")
    extra: Dict[str, Any] = Field(default_factory=dict)


class GenerationResult(BaseModel):
    text: str = Field(description="Generated text content")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="Token usage if available")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific metadata")


class ChatGenerationProvider(Protocol):
    """Protocol for chat generation providers. All implementations must be async."""

    @property
    def model_identifier(self) -> str:
        """Unique identifier for this provider/model combination."""
        ...

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        config: GenerationConfig
    ) -> GenerationResult:
        """Generate a response from messages.

        Args:
            messages: List of conversation messages
            config: Generation configuration

        Returns:
            GenerationResult with text and metadata

        Raises:
            ProviderError: On provider-specific failures
            ValueError: On invalid input
        """
        ...


class EvaluationJudgeProvider(Protocol):
    """Protocol for evaluation judge providers (optional)."""

    @property
    def model_identifier(self) -> str:
        """Unique identifier for this judge provider/model."""
        ...

    @abstractmethod
    async def evaluate(
        self,
        question: str,
        answer: str,
        context: List[str],
        reference_answer: Optional[str] = None,
        criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Evaluate answer quality.

        Args:
            question: The original question
            answer: Generated answer to evaluate
            context: Retrieved context passages
            reference_answer: Optional reference answer
            criteria: Optional evaluation criteria

        Returns:
            Dictionary with evaluation scores and metadata

        Raises:
            ProviderError: On provider-specific failures
        """
        ...


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(
        self,
        message: str,
        provider: str,
        original_error: Optional[Exception] = None,
        retryable: bool = False,
        error_code: Optional[str] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error
        self.retryable = retryable
        self.error_code = error_code


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request times out."""

    def __init__(self, provider: str, timeout_seconds: float):
        super().__init__(
            f"Provider {provider} timed out after {timeout_seconds}s",
            provider=provider,
            retryable=True,
            error_code="TIMEOUT"
        )


class ProviderRateLimitError(ProviderError):
    """Raised when provider returns rate limit error."""

    def __init__(self, provider: str, retry_after: Optional[float] = None):
        super().__init__(
            f"Provider {provider} rate limited",
            provider=provider,
            retryable=True,
            error_code="RATE_LIMIT"
        )
        self.retry_after = retry_after


class ProviderConfigurationError(ProviderError):
    """Raised when provider is misconfigured (missing credentials, etc.)."""

    def __init__(self, provider: str, message: str):
        super().__init__(
            f"Provider {provider} configuration error: {message}",
            provider=provider,
            retryable=False,
            error_code="CONFIG_ERROR"
        )


class ProviderResponseError(ProviderError):
    """Raised when provider returns an error response."""

    def __init__(self, provider: str, message: str, status_code: Optional[int] = None):
        super().__init__(
            f"Provider {provider} error: {message}",
            provider=provider,
            retryable=status_code is not None and status_code >= 500,
            error_code="RESPONSE_ERROR"
        )
        self.status_code = status_code