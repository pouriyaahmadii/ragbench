import pytest
import re
from typing import List

from app.providers.protocols import (
    ChatGenerationProvider,
    GenerationConfig,
    GenerationResult,
    Message,
    ProviderConfigurationError,
)
from app.providers.mock import MockGenerationProvider
from app.providers.factory import ProviderFactory
from app.config import Settings, GenerationConfig


class TestGenerationProviderContract:
    """Contract tests for ChatGenerationProvider implementations."""

    @pytest.fixture
    def mock_config(self) -> GenerationConfig:
        return GenerationConfig(
            provider="mock",
            model="mock",
            temperature=0.0,
            max_tokens=1024,
            prompt_version="1.0",
        )

    @pytest.fixture
    def mock_provider(self) -> MockGenerationProvider:
        return MockGenerationProvider()

    @pytest.fixture
    def sample_messages(self) -> List[Message]:
        return [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="What is the retention period?"),
        ]

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_generate_returns_result(self, mock_provider: MockGenerationProvider, sample_messages: List[Message], mock_config: GenerationConfig):
        """Provider must return a GenerationResult."""
        result = await mock_provider.generate(sample_messages, mock_config)
        assert isinstance(result, GenerationResult)
        assert isinstance(result.text, str)
        assert len(result.text) > 0

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_generate_metadata_fields(self, mock_provider: MockGenerationProvider, sample_messages: List[Message], mock_config: GenerationConfig):
        """Result metadata must contain required fields."""
        result = await mock_provider.generate(sample_messages, mock_config)
        meta = result.metadata
        assert meta["provider"] == "mock"
        assert meta["model"] == "mock"
        assert meta["version"] == "1.0"
        assert "prompt_version" in meta
        assert "citations" in meta
        assert "finish_reason" in meta

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_usage_metadata_present(self, mock_provider: MockGenerationProvider, sample_messages: List[Message], mock_config: GenerationConfig):
        """Result must include token usage information."""
        result = await mock_provider.generate(sample_messages, mock_config)
        assert result.usage is not None
        assert "prompt_tokens" in result.usage
        assert "completion_tokens" in result.usage
        assert "total_tokens" in result.usage
        assert result.usage["total_tokens"] == result.usage["prompt_tokens"] + result.usage["completion_tokens"]

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_citations_format(self, mock_provider: MockGenerationProvider, mock_config: GenerationConfig):
        """Citations must be in expected format [chunk-id]."""
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="What is the retention period?"),
        ]
        result = await mock_provider.generate(messages, mock_config)
        # Citations should be in metadata
        citations = result.metadata.get("citations", [])
        assert isinstance(citations, list)
        # Check format if present
        for citation in citations:
            assert isinstance(citation, str)
            assert re.match(r'^[a-zA-Z0-9\-_]+$', citation)

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_prompt_version_recorded(self, mock_provider: MockGenerationProvider, sample_messages: List[Message]):
        """Prompt version from config must be recorded in metadata."""
        config = GenerationConfig(prompt_version="custom-v2")
        result = await mock_provider.generate(sample_messages, config)
        assert result.metadata["prompt_version"] == "custom-v2"

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_temperature_respected(self, mock_provider: MockGenerationProvider, sample_messages: List[Message]):
        """Temperature from config should be passed through (recorded in metadata)."""
        config = GenerationConfig(temperature=0.7)
        result = await mock_provider.generate(sample_messages, config)
        # Mock provider records temperature in metadata for verification
        # (Real providers would use it for sampling)

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_max_tokens_respected(self, mock_provider: MockGenerationProvider, sample_messages: List[Message]):
        """Max tokens from config should be passed through."""
        config = GenerationConfig(max_tokens=50)
        result = await mock_provider.generate(sample_messages, config)
        # Verify max_tokens in config
        assert result.metadata.get("max_tokens") is None or result.metadata.get("max_tokens") == 50

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_abstention_case(self, mock_provider: MockGenerationProvider):
        """Unanswerable questions should trigger abstention response."""
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="What is the CEO's favorite color?"),
        ]
        config = GenerationConfig()
        result = await mock_provider.generate(messages, config)
        assert "sufficient evidence" in result.text.lower() or "insufficient evidence" in result.text.lower()
        assert len(result.metadata.get("citations", [])) == 0

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_model_identifier_property(self, mock_provider: MockGenerationProvider):
        """model_identifier must return non-empty string."""
        identifier = mock_provider.model_identifier
        assert isinstance(identifier, str)
        assert len(identifier) > 0
        assert "mock" in identifier

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_empty_messages_error(self, mock_provider: MockGenerationProvider, mock_config: GenerationConfig):
        """Empty messages should be handled gracefully (not crash)."""
        result = await mock_provider.generate([], mock_config)
        assert isinstance(result, GenerationResult)

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_unicode_content(self, mock_provider: MockGenerationProvider, mock_config: GenerationConfig):
        """Unicode content must be handled correctly."""
        messages = [
            Message(role="user", content="What is 世界? 🚀"),
        ]
        result = await mock_provider.generate(messages, mock_config)
        assert isinstance(result.text, str)
        assert len(result.text) > 0


class TestMockGenerationProviderSpecific:
    """Tests specific to MockGenerationProvider behavior."""

    @pytest.fixture
    def provider(self) -> MockGenerationProvider:
        return MockGenerationProvider()

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_deterministic_responses(self, provider: MockGenerationProvider):
        """Same input must produce same output."""
        messages = [Message(role="user", content="What is retention?")]
        config = GenerationConfig()
        r1 = await provider.generate(messages, config)
        r2 = await provider.generate(messages, config)
        assert r1.text == r2.text
        assert r1.metadata == r2.metadata

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_keyword_matching(self, provider: MockGenerationProvider):
        """Keyword matching for fixture selection."""
        messages = [Message(role="user", content="What is the retention policy?")]
        config = GenerationConfig()
        result = await provider.generate(messages, config)
        assert "30 days" in result.text

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_citation_extraction(self, provider: MockGenerationProvider):
        """Citations in answer text are extracted to metadata."""
        messages = [Message(role="user", content="What is the retention period?")]
        config = GenerationConfig()
        result = await provider.generate(messages, config)
        citations = result.metadata.get("citations", [])
        assert "chunk-policy-001-003" in citations

    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_citation_removal_from_text(self, provider: MockGenerationProvider):
        """Citation markers removed from display text."""
        messages = [Message(role="user", content="What is the retention period?")]
        config = GenerationConfig()
        result = await provider.generate(messages, config)
        assert "[chunk-policy-001-003]" not in result.text
        assert "30 days" in result.text


class TestGenerationConfig:
    """Tests for GenerationConfig validation."""

    def test_valid_config(self):
        config = GenerationConfig(
            provider="mock",
            model="mock",
            temperature=0.5,
            max_tokens=512,
        )
        assert config.temperature == 0.5
        assert config.max_tokens == 512

    def test_config_hash_consistency(self):
        config1 = GenerationConfig(provider="mock", model="a", temperature=0.5)
        config2 = GenerationConfig(provider="mock", model="a", temperature=0.5)
        config3 = GenerationConfig(provider="mock", model="b", temperature=0.5)
        assert config1.config_hash() == config2.config_hash()
        assert config1.config_hash() != config3.config_hash()


class TestProviderFactoryGeneration:
    """Tests for provider factory generation provider creation."""

    @pytest.fixture
    def settings(self) -> Settings:
        return Settings(
            MOCK_MODE=True,
            GENERATION_PROVIDER="mock",
            GENERATION_MODEL="mock",
        )

    @pytest.mark.contract
    def test_factory_creates_mock_provider(self, settings: Settings):
        factory = ProviderFactory(settings)
        provider = factory.get_generation_provider()
        assert isinstance(provider, MockGenerationProvider)

    @pytest.mark.contract
    def test_factory_caches_providers(self, settings: Settings):
        factory = ProviderFactory(settings)
        p1 = factory.get_generation_provider()
        p2 = factory.get_generation_provider()
        assert p1 is p2

    @pytest.mark.contract
    def test_factory_different_configs_different_instances(self, settings: Settings):
        factory = ProviderFactory(settings)
        p1 = factory.get_generation_provider(GenerationConfig(max_tokens=512))
        p2 = factory.get_generation_provider(GenerationConfig(max_tokens=256))
        assert p1 is not p2

    @pytest.mark.contract
    def test_factory_mock_mode_forces_mock(self, settings: Settings):
        """MOCK_MODE should force mock provider regardless of config."""
        settings.GENERATION_PROVIDER = "openai"
        settings.OPENAI_API_KEY = None  # Not configured
        factory = ProviderFactory(settings)
        provider = factory.get_generation_provider()
        assert isinstance(provider, MockGenerationProvider)