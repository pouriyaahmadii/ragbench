import hashlib
import re
from typing import List
from app.providers.protocols import (
    EmbeddingProvider,
    EmbeddingResult,
    EmbeddingMetadata,
    ChatGenerationProvider,
    GenerationConfig,
    GenerationResult,
    Message,
)
import random


class MockEmbeddingProvider:
    """Deterministic mock embedding provider for testing and CI.

    Generates embeddings based on text hash for reproducibility.
    Not semantically meaningful - only for testing pipeline contracts.
    """

    def __init__(self, dimension: int = 384, seed: int = 42):
        self._dimension = dimension
        self._seed = seed

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_identifier(self) -> str:
        return f"mock:embedding:v1:dim{self._dimension}"

    def _text_to_vector(self, text: str) -> List[float]:
        """Generate deterministic vector from text using hash, incorporating seed."""
        # Incorporate seed into the hash for different seeds producing different outputs
        hash_input = f"{text}:{self._seed}".encode()
        hash_obj = hashlib.sha256(hash_input)
        hash_bytes = hash_obj.digest()

        vector = []
        for i in range(self._dimension):
            byte_idx = (i * 4) % len(hash_bytes)
            chunk = hash_bytes[byte_idx:byte_idx + 4]
            if len(chunk) < 4:
                chunk = chunk + hash_bytes[:4 - len(chunk)]
            val = int.from_bytes(chunk, 'little', signed=True) / (2**31)
            vector.append(val)
        return vector

    async def embed(self, texts: List[str]) -> "EmbeddingResult":
        """Generate deterministic embeddings based on text hash."""
        from app.providers.protocols import EmbeddingResult, EmbeddingMetadata
        if not texts:
            return EmbeddingResult(
                vectors=[],
                metadata=EmbeddingMetadata(
                    provider="mock",
                    model="mock",
                    version="1.0",
                    dimension=self._dimension,
                )
            )

        vectors = [self._text_to_vector(text) for text in texts]

        return EmbeddingResult(
            vectors=vectors,
            metadata=EmbeddingMetadata(
                provider="mock",
                model="mock",
                version="1.0",
                dimension=self._dimension,
            )
        )


class MockGenerationProvider:
    """Deterministic mock generation provider for testing and CI.

    Returns predefined responses based on question keywords.
    Not semantically meaningful - only for testing pipeline contracts.
    """

    def __init__(self, seed: int = 42):
        self._fixtures = {
            "retention": "The stated retention period is 30 days. [chunk-policy-001-003]",
            "exception": "The exception must be approved by an authorized policy owner. [chunk-access-001-002]",
            "office": "The company has offices in San Francisco and New York. [chunk-office-001-001]",
        }
        self._default_response = "The provided documents do not contain sufficient evidence to answer this question."

    @property
    def model_identifier(self) -> str:
        return "mock:generation:v1"

    async def generate(
        self,
        messages: List["Message"],
        config: "GenerationConfig"
    ) -> "GenerationResult":
        """Generate a deterministic response based on question content."""
        question = ""
        for msg in reversed(messages):
            if msg.role == "user":
                question = msg.content
                break

        answer_text = self._default_response
        for keyword, fixture in self._fixtures.items():
            if keyword.lower() in question.lower():
                answer_text = fixture
                break

        citations = []
        import re
        for match in re.finditer(r'\[([a-zA-Z0-9\-_]+)\]', answer_text):
            citations.append(match.group(1))

        clean_answer = re.sub(r'\s*\[[a-zA-Z0-9\-_]+\]', '', answer_text).strip()

        from app.providers.protocols import GenerationResult
        return GenerationResult(
            text=clean_answer,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            metadata={
                "provider": "mock",
                "model": "mock",
                "version": "1.0",
                "prompt_version": config.prompt_version,
                "citations": citations,
                "finish_reason": "stop",
            }
        )


def get_mock_embedding_provider(dimension: int = 384, seed: int = 42) -> MockEmbeddingProvider:
    return MockEmbeddingProvider(dimension=dimension, seed=seed)


def get_mock_generation_provider(seed: int = 42) -> MockGenerationProvider:
    return MockGenerationProvider(seed=seed)