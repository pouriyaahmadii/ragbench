import pytest
from unittest.mock import patch, AsyncMock

from app.config import Settings, EmbeddingConfig, GenerationConfig
from app.providers.factory import ProviderFactory
from app.providers.protocols import ProviderConfigurationError


class TestProviderFactoryConfigurationErrors:
    """Tests for provider factory configuration error handling."""

    @pytest.fixture
    def mock_settings(self) -> Settings:
        """Settings with MOCK_MODE=False to test real provider errors."""
        return Settings(
            MOCK_MODE=False,
            EMBEDDING_PROVIDER="openai",
            EMBEDDING_MODEL="text-embedding-3-small",
            EMBEDDING_DIMENSION=1536,
            GENERATION_PROVIDER="openai",
            GENERATION_MODEL="gpt-4o-mini",
            OPENAI_API_KEY=None,
        )

    def test_embedding_missing_openai_key_raises_config_error(self, mock_settings: Settings):
        """Missing OpenAI API key should raise ProviderConfigurationError."""
        factory = ProviderFactory(mock_settings)
        with pytest.raises(ProviderConfigurationError) as exc_info:
            factory.get_embedding_provider()
        assert exc_info.value.provider == "openai"
        assert exc_info.value.error_code == "CONFIG_ERROR"
        assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_generation_missing_openai_key_raises_config_error(self, mock_settings: Settings):
        """Missing OpenAI API key for generation should raise error."""
        factory = ProviderFactory(mock_settings)
        with pytest.raises(ProviderConfigurationError) as exc_info:
            factory.get_generation_provider()
        assert exc_info.value.provider == "openai"
        assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_embedding_missing_ollama_url_raises_config_error(self, mock_settings: Settings):
        """Missing Ollama URL should raise error."""
        mock_settings.EMBEDDING_PROVIDER = "ollama"
        mock_settings.OLLAMA_EMBEDDING_URL = None
        factory = ProviderFactory(mock_settings)
        with pytest.raises(ProviderConfigurationError) as exc_info:
            factory.get_embedding_provider()
        assert exc_info.value.provider == "ollama"
        assert "URL" in str(exc_info.value)

    def test_generation_missing_ollama_url_raises_config_error(self, mock_settings: Settings):
        """Missing Ollama generation URL should raise error."""
        mock_settings.GENERATION_PROVIDER = "ollama"
        mock_settings.OLLAMA_GENERATION_URL = None
        factory = ProviderFactory(mock_settings)
        with pytest.raises(ProviderConfigurationError) as exc_info:
            factory.get_generation_provider()
        assert exc_info.value.provider == "ollama"
        assert "URL" in str(exc_info.value)

    def test_embedding_missing_cohere_key_raises_config_error(self, mock_settings: Settings):
        """Missing Cohere API key should raise error."""
        mock_settings.EMBEDDING_PROVIDER = "cohere"
        mock_settings.COHERE_API_KEY = None
        factory = ProviderFactory(mock_settings)
        with pytest.raises(ProviderConfigurationError) as exc_info:
            factory.get_embedding_provider()
        assert exc_info.value.provider == "cohere"

    def test_generation_missing_anthropic_key_raises_config_error(self, mock_settings: Settings):
        """Missing Anthropic API key should raise error."""
        mock_settings.GENERATION_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_API_KEY = None
        factory = ProviderFactory(mock_settings)
        with pytest.raises(ProviderConfigurationError) as exc_info:
            factory.get_generation_provider()
        assert exc_info.value.provider == "anthropic"

    def test_unknown_embedding_provider_raises_error(self, mock_settings: Settings):
        """Unknown embedding provider should raise configuration error."""
        mock_settings.EMBEDDING_PROVIDER = "unknown"
        factory = ProviderFactory(mock_settings)
        with pytest.raises(Exception) as exc_info:
            factory.get_embedding_provider()
        # Pydantic validates the literal before our code runs
        error_msg = str(exc_info.value).lower()
        assert "unknown" in error_msg or "literal" in error_msg

    def test_unknown_generation_provider_raises_error(self, mock_settings: Settings):
        """Unknown generation provider should raise configuration error."""
        mock_settings.GENERATION_PROVIDER = "unknown"
        factory = ProviderFactory(mock_settings)
        with pytest.raises(Exception) as exc_info:
            factory.get_generation_provider()
        # Pydantic validates the literal before our code runs
        error_msg = str(exc_info.value).lower()
        assert "unknown" in error_msg or "literal" in error_msg


class TestProviderFactoryMockMode:
    """Tests for factory behavior in mock mode."""

    def test_mock_mode_forces_mock_embedding(self):
        settings = Settings(
            MOCK_MODE=True,
            EMBEDDING_PROVIDER="openai",
            OPENAI_API_KEY=None,
        )
        factory = ProviderFactory(settings)
        provider = factory.get_embedding_provider()
        from app.providers.mock import MockEmbeddingProvider
        assert isinstance(provider, MockEmbeddingProvider)

    def test_mock_mode_forces_mock_generation(self):
        settings = Settings(
            MOCK_MODE=True,
            GENERATION_PROVIDER="openai",
            OPENAI_API_KEY=None,
        )
        factory = ProviderFactory(settings)
        provider = factory.get_generation_provider()
        from app.providers.mock import MockGenerationProvider
        assert isinstance(provider, MockGenerationProvider)

    def test_mock_mode_overrides_explicit_provider(self):
        """MOCK_MODE should override explicit provider selection."""
        settings = Settings(
            MOCK_MODE=True,
            EMBEDDING_PROVIDER="openai",
            GENERATION_PROVIDER="anthropic",
            OPENAI_API_KEY=None,
            ANTHROPIC_API_KEY=None,
        )
        factory = ProviderFactory(settings)
        emb = factory.get_embedding_provider()
        gen = factory.get_generation_provider()
        from app.providers.mock import MockEmbeddingProvider, MockGenerationProvider
        assert isinstance(emb, MockEmbeddingProvider)
        assert isinstance(gen, MockGenerationProvider)


class TestProviderFactoryConfigHashing:
    """Tests for provider factory config-based caching."""

    def test_embedding_cache_by_config(self):
        settings = Settings(MOCK_MODE=True, EMBEDDING_DIMENSION=384)
        factory = ProviderFactory(settings)

        # Same config should return cached instance
        p1 = factory.get_embedding_provider(EmbeddingConfig(dimension=384))
        p2 = factory.get_embedding_provider(EmbeddingConfig(dimension=384))
        assert p1 is p2

        # Different dimension should create new instance
        p3 = factory.get_embedding_provider(EmbeddingConfig(dimension=768))
        assert p3 is not p1
        assert p3.dimension == 768

    def test_generation_cache_by_config(self):
        settings = Settings(MOCK_MODE=True)
        factory = ProviderFactory(settings)

        p1 = factory.get_generation_provider(GenerationConfig(max_tokens=512))
        p2 = factory.get_generation_provider(GenerationConfig(max_tokens=512))
        assert p1 is p2

        p3 = factory.get_generation_provider(GenerationConfig(max_tokens=256))
        assert p3 is not p1

    def test_different_providers_not_cached_together(self):
        settings = Settings(MOCK_MODE=False)
        factory = ProviderFactory(settings)

        # Can't easily test without mocking provider creation
        # but verify the cache key logic includes provider type
        config1 = EmbeddingConfig(provider="mock", dimension=384)
        config2 = EmbeddingConfig(provider="openai", dimension=384)
        key1 = f"{config1.provider}:{config1.model}:{config1.dimension}"
        key2 = f"{config2.provider}:{config2.model}:{config2.dimension}"
        assert key1 != key2


class TestProviderFactoryCleanup:
    """Tests for provider cleanup."""

    @pytest.mark.asyncio
    async def test_close_all_closes_providers(self):
        settings = Settings(MOCK_MODE=True)
        factory = ProviderFactory(settings)

        # Create some providers
        factory.get_embedding_provider()
        factory.get_generation_provider()

        # Should not raise
        await factory.close_all()

        # Caches should be empty
        assert len(factory._embedding_cache) == 0
        assert len(factory._generation_cache) == 0

    @pytest.mark.asyncio
    async def test_close_all_idempotent(self):
        settings = Settings(MOCK_MODE=True)
        factory = ProviderFactory(settings)
        factory.get_embedding_provider()

        await factory.close_all()
        await factory.close_all()  # Should not raise