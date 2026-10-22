from typing import Optional
from app.config import Settings, EmbeddingConfig, GenerationConfig
from app.providers.protocols import (
    EmbeddingProvider,
    ChatGenerationProvider,
    EvaluationJudgeProvider,
    ProviderConfigurationError,
)
from app.providers.mock import MockEmbeddingProvider, MockGenerationProvider
from app.providers.ollama import OllamaEmbeddingProvider, OllamaGenerationProvider
from app.providers.openai import OpenAIEmbeddingProvider, OpenAIGenerationProvider
from app.providers.anthropic import AnthropicGenerationProvider
from app.providers.cohere import CohereEmbeddingProvider


class ProviderFactory:
    """Factory for creating provider instances based on configuration."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._embedding_cache: dict = {}
        self._generation_cache: dict = {}

    def get_embedding_provider(self, config: Optional[EmbeddingConfig] = None) -> "EmbeddingProvider":
        """Get or create an embedding provider instance."""
        if config is None:
            config = EmbeddingConfig(
                provider=self.settings.EMBEDDING_PROVIDER,
                model=self.settings.EMBEDDING_MODEL,
                dimension=self.settings.EMBEDDING_DIMENSION,
            )

        # Force mock mode if enabled
        if self.settings.MOCK_MODE:
            config.provider = "mock"

        cache_key = f"{config.provider}:{config.model}:{config.dimension}"
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        provider = self._create_embedding_provider(config)
        self._embedding_cache[cache_key] = provider
        return provider

    def get_generation_provider(self, config: Optional[GenerationConfig] = None) -> "ChatGenerationProvider":
        """Get or create a generation provider instance."""
        if config is None:
            config = GenerationConfig(
                provider=self.settings.GENERATION_PROVIDER,
                model=self.settings.GENERATION_MODEL,
            )

        # Force mock mode if enabled
        if self.settings.MOCK_MODE:
            config.provider = "mock"

        cache_key = f"{config.provider}:{config.model}:{config.temperature}:{config.max_tokens}"
        if cache_key in self._generation_cache:
            return self._generation_cache[cache_key]

        provider = self._create_generation_provider(config)
        self._generation_cache[cache_key] = provider
        return provider

    def get_judge_provider(self) -> Optional["EvaluationJudgeProvider"]:
        """Get judge provider if enabled."""
        if not self.settings.RAGAS_API_KEY and self.settings.EVAL_JUDGE_PROVIDER != "mock":
            return None

        if self.settings.MOCK_MODE:
            from app.providers.mock import get_mock_generation_provider
            return get_mock_generation_provider()

        # Would implement Ragas or other judge here
        return None

    def _create_embedding_provider(self, config: "EmbeddingConfig") -> "EmbeddingProvider":
        provider_type = config.provider.lower()

        if provider_type == "mock":
            return MockEmbeddingProvider(dimension=config.dimension)

        elif provider_type == "ollama":
            if not config.base_url:
                raise ProviderConfigurationError(
                    "ollama", "OLLAMA_EMBEDDING_URL not configured"
                )
            return OllamaEmbeddingProvider(
                base_url=config.base_url,
                model=config.model,
                dimension=config.dimension,
                timeout=config.timeout_seconds,
            )

        elif provider_type == "openai":
            if not config.api_key and not self.settings.OPENAI_API_KEY:
                raise ProviderConfigurationError("openai", "OPENAI_API_KEY not configured")
            return OpenAIEmbeddingProvider(
                api_key=config.api_key or self.settings.OPENAI_API_KEY,
                model=config.model,
                dimension=config.dimension,
                timeout=config.timeout_seconds,
            )

        elif provider_type == "cohere":
            if not config.api_key and not self.settings.COHERE_API_KEY:
                raise ProviderConfigurationError("cohere", "COHERE_API_KEY not configured")
            return CohereEmbeddingProvider(
                api_key=config.api_key or self.settings.COHERE_API_KEY,
                model=config.model,
                dimension=config.dimension,
                timeout=config.timeout_seconds,
            )

        else:
            raise ProviderConfigurationError(
                "embedding", f"Unknown provider: {provider_type}"
            )

    def _create_generation_provider(self, config: "GenerationConfig") -> "ChatGenerationProvider":
        provider_type = config.provider.lower()

        if provider_type == "mock":
            return MockGenerationProvider()

        elif provider_type == "ollama":
            if not config.base_url and not self.settings.OLLAMA_GENERATION_URL:
                raise ProviderConfigurationError(
                    "ollama", "OLLAMA_GENERATION_URL not configured"
                )
            return OllamaGenerationProvider(
                base_url=config.base_url or self.settings.OLLAMA_GENERATION_URL,
                model=config.model,
                timeout=config.timeout_seconds,
            )

        elif provider_type == "openai":
            if not config.api_key and not self.settings.OPENAI_API_KEY:
                raise ProviderConfigurationError("openai", "OPENAI_API_KEY not configured")
            return OpenAIGenerationProvider(
                api_key=config.api_key or self.settings.OPENAI_API_KEY,
                model=config.model,
                timeout=config.timeout_seconds,
            )

        elif provider_type == "anthropic":
            if not config.api_key and not self.settings.ANTHROPIC_API_KEY:
                raise ProviderConfigurationError("anthropic", "ANTHROPIC_API_KEY not configured")
            return AnthropicGenerationProvider(
                api_key=config.api_key or self.settings.ANTHROPIC_API_KEY,
                model=config.model,
                timeout=config.timeout_seconds,
            )

        else:
            raise ProviderConfigurationError(
                "generation", f"Unknown provider: {provider_type}"
            )

    async def close_all(self):
        """Close all cached provider connections."""
        for provider in self._embedding_cache.values():
            if hasattr(provider, "close"):
                await provider.close()
        for provider in self._generation_cache.values():
            if hasattr(provider, "close"):
                await provider.close()
        self._embedding_cache.clear()
        self._generation_cache.clear()


# Global factory instance (initialized in main.py lifespan)
_factory: Optional["ProviderFactory"] = None


def get_provider_factory(settings: Settings) -> "ProviderFactory":
    global _factory
    if _factory is None:
        _factory = ProviderFactory(settings)
    return _factory


def get_embedding_provider(settings: Settings, config: Optional["EmbeddingConfig"] = None) -> "EmbeddingProvider":
    factory = get_provider_factory(settings)
    return factory.get_embedding_provider(config)


def get_generation_provider(settings: Settings, config: Optional["GenerationConfig"] = None) -> "ChatGenerationProvider":
    factory = get_provider_factory(settings)
    return factory.get_generation_provider(config)


async def close_providers():
    global _factory
    if _factory:
        await _factory.close_all()
        _factory = None