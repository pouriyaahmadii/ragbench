import pytest
import asyncio
import math
from typing import List

from app.providers.protocols import (
    EmbeddingProvider,
    EmbeddingResult,
    ProviderError,
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderConfigurationError,
    ProviderResponseError,
)
from app.providers.mock import MockEmbeddingProvider
from app.providers.factory import ProviderFactory
from app.config import Settings, EmbeddingConfig


class TestEmbeddingProviderContract:
    """Contract tests for EmbeddingProvider implementations.

    These tests verify that all embedding providers conform to the expected interface
    and behavior. Run with pytest -m contract.
    """

    @pytest.fixture
    def mock_config(self) -> EmbeddingConfig:
        return EmbeddingConfig(
            provider="mock",
            model="mock",
            dimension=384,
            batch_size=100,
        )

    @pytest.fixture
    def mock_provider(self, mock_config) -> MockEmbeddingProvider:
        return MockEmbeddingProvider(dimension=mock_config.dimension)

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_embed_returns_correct_length(self, mock_provider: MockEmbeddingProvider):
        """Provider must return same number of vectors as input texts."""
        texts = ["text one", "text two", "text three"]
        result = await mock_provider.embed(texts)
        assert isinstance(result, EmbeddingResult)
        assert len(result.vectors) == len(texts)

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_embed_dimension_matches(self, mock_provider: MockEmbeddingProvider):
        """All returned vectors must have the configured dimension."""
        texts = ["test"]
        result = await mock_provider.embed(texts)
        assert all(len(v) == mock_provider.dimension for v in result.vectors)
        assert result.metadata.dimension == mock_provider.dimension

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_embed_finite_values(self, mock_provider: MockEmbeddingProvider):
        """All embedding values must be finite (no NaN or Inf)."""
        import math
        texts = ["test"]
        result = await mock_provider.embed(texts)
        for vector in result.vectors:
            for val in vector:
                assert math.isfinite(val), f"Non-finite value found: {val}"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_embed_deterministic(self, mock_provider: MockEmbeddingProvider):
        """Same input must produce same output (deterministic)."""
        texts = ["deterministic test"]
        result1 = await mock_provider.embed(texts)
        result2 = await mock_provider.embed(texts)
        assert result1.vectors == result2.vectors

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_embed_different_inputs_different_outputs(self, mock_provider: MockEmbeddingProvider):
        """Different inputs should produce different embeddings."""
        texts = ["different text one", "different text two"]
        result = await mock_provider.embed(texts)
        assert result.vectors[0] != result.vectors[1]

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_embed_empty_list(self, mock_provider: MockEmbeddingProvider):
        """Empty input must return empty result, not error."""
        result = await mock_provider.embed([])
        assert isinstance(result, EmbeddingResult)
        assert result.vectors == []
        assert result.metadata.dimension == mock_provider.dimension

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_embed_batch_size_respected(self, mock_provider: MockEmbeddingProvider):
        """Large batches should work (test with more than batch_size)."""
        # Create more texts than default batch size (100)
        texts = [f"text {i}" for i in range(150)]
        result = await mock_provider.embed(texts)
        assert len(result.vectors) == 150

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_metadata_fields_present(self, mock_provider: MockEmbeddingProvider):
        """Metadata must contain required fields."""
        texts = ["test"]
        result = await mock_provider.embed(texts)
        meta = result.metadata
        assert meta.provider == "mock"
        assert meta.model == "mock"
        assert meta.version == "1.0"
        assert meta.dimension == mock_provider.dimension

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_model_identifier_property(self, mock_provider: MockEmbeddingProvider):
        """model_identifier property must return non-empty string."""
        identifier = mock_provider.model_identifier
        assert isinstance(identifier, str)
        assert len(identifier) > 0
        assert "mock" in identifier

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_dimension_property(self, mock_provider: MockEmbeddingProvider):
        """dimension property must return positive integer."""
        assert isinstance(mock_provider.dimension, int)
        assert mock_provider.dimension > 0

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_special_characters_handled(self, mock_provider: MockEmbeddingProvider):
        """Special characters and Unicode must be handled."""
        texts = ["Hello 世界", "🚀🌟", "path/to/file.txt", "C:\\Windows\\path"]
        result = await mock_provider.embed(texts)
        assert len(result.vectors) == 4
        assert all(len(v) == mock_provider.dimension for v in result.vectors)

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_very_long_text(self, mock_provider: MockEmbeddingProvider):
        """Very long text must be handled without error."""
        long_text = "x" * 10000
        result = await mock_provider.embed([long_text])
        assert len(result.vectors) == 1
        assert len(result.vectors[0]) == mock_provider.dimension


class TestMockEmbeddingProviderSpecific:
    """Tests specific to MockEmbeddingProvider behavior."""

    @pytest.fixture
    def provider(self) -> MockEmbeddingProvider:
        return MockEmbeddingProvider(dimension=128)

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_same_seed_same_output(self):
        """Same seed must produce identical embeddings."""
        p1 = MockEmbeddingProvider(dimension=64, seed=123)
        p2 = MockEmbeddingProvider(dimension=64, seed=123)
        r1 = await p1.embed(["test"])
        r2 = await p2.embed(["test"])
        assert r1.vectors == r2.vectors

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_different_seeds_different_output(self):
        """Different seeds must produce different embeddings."""
        p1 = MockEmbeddingProvider(dimension=64, seed=123)
        p2 = MockEmbeddingProvider(dimension=64, seed=456)
        r1 = await p1.embed(["test"])
        r2 = await p2.embed(["test"])
        assert r1.vectors != r2.vectors


class TestProviderFactory:
    """Tests for provider factory configuration."""

    @pytest.fixture
    def settings(self) -> Settings:
        return Settings(
            MOCK_MODE=True,
            EMBEDDING_PROVIDER="mock",
            EMBEDDING_MODEL="mock",
            EMBEDDING_DIMENSION=384,
        )

    @pytest.mark.contract
    def test_factory_creates_mock_provider(self, settings: Settings):
        factory = ProviderFactory(settings)
        provider = factory.get_embedding_provider()
        assert isinstance(provider, MockEmbeddingProvider)
        assert provider.dimension == 384

    @pytest.mark.contract
    def test_factory_caches_providers(self, settings: Settings):
        factory = ProviderFactory(settings)
        p1 = factory.get_embedding_provider()
        p2 = factory.get_embedding_provider()
        assert p1 is p2  # Same instance (cached)

    @pytest.mark.contract
    def test_factory_different_configs_different_instances(self, settings: Settings):
        factory = ProviderFactory(settings)
        p1 = factory.get_embedding_provider(EmbeddingConfig(dimension=384))
        p2 = factory.get_embedding_provider(EmbeddingConfig(dimension=768))
        assert p1 is not p2
        assert p1.dimension == 384
        assert p2.dimension == 768


class TestProviderErrors:
    """Tests for provider error handling."""

    @pytest.mark.contract
    def test_provider_error_attributes(self):
        error = ProviderError(
            "test message",
            provider="test",
            retryable=True,
            error_code="TEST_CODE"
        )
        assert error.provider == "test"
        assert error.retryable is True
        assert error.error_code == "TEST_CODE"

    @pytest.mark.contract
    def test_timeout_error(self):
        error = ProviderTimeoutError("test", 30.0)
        assert error.provider == "test"
        assert error.retryable is True
        assert error.error_code == "TIMEOUT"
        assert "30" in str(error)

    @pytest.mark.contract
    def test_rate_limit_error(self):
        error = ProviderRateLimitError("test", retry_after=60.0)
        assert error.provider == "test"
        assert error.retryable is True
        assert error.error_code == "RATE_LIMIT"
        assert error.retry_after == 60.0

    @pytest.mark.contract
    def test_config_error(self):
        error = ProviderConfigurationError("test", "missing API key")
        assert error.provider == "test"
        assert error.retryable is False
        assert error.error_code == "CONFIG_ERROR"

    @pytest.mark.contract
    def test_response_error(self):
        error = ProviderResponseError("test", "server error", 500)
        assert error.provider == "test"
        assert error.retryable is True  # 5xx errors are retryable
        assert error.error_code == "RESPONSE_ERROR"
        assert error.status_code == 500


class TestEmbeddingConfig:
    """Tests for EmbeddingConfig validation."""

    @pytest.mark.contract
    def test_valid_config(self):
        config = EmbeddingConfig(
            provider="mock",
            model="mock",
            dimension=384,
            batch_size=100,
        )
        assert config.provider == "mock"
        assert config.dimension == 384

    @pytest.mark.contract
    def test_config_hash_consistency(self):
        config1 = EmbeddingConfig(provider="mock", model="a", dimension=384)
        config2 = EmbeddingConfig(provider="mock", model="a", dimension=384)
        config3 = EmbeddingConfig(provider="mock", model="b", dimension=384)
        assert config1.config_hash() == config2.config_hash()
        assert config1.config_hash() != config3.config_hash()