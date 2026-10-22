from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any


class EmbeddingConfig(BaseModel):
    provider: Literal["mock", "ollama", "openai", "cohere"] = "mock"
    model: str = "mock"
    version: str = "1.0"
    dimension: int = 384
    batch_size: int = 100
    timeout_seconds: int = 60
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)

    def config_hash(self) -> str:
        import hashlib
        import json
        # Pydantic v2: use model_dump with json.dumps for sorted keys
        data = self.model_dump(exclude={"api_key"})
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


class GenerationConfig(BaseModel):
    provider: Literal["mock", "ollama", "openai", "anthropic"] = "mock"
    model: str = "mock"
    version: str = "1.0"
    temperature: float = 0.0
    max_tokens: int = 1024
    timeout_seconds: int = 60
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    prompt_version: str = "1.0"
    extra: Dict[str, Any] = Field(default_factory=dict)

    def config_hash(self) -> str:
        import hashlib
        import json
        # Pydantic v2: use model_dump with json.dumps for sorted keys
        data = self.model_dump(exclude={"api_key"})
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


class ChunkingConfig(BaseModel):
    strategy: Literal["fixed", "structure_aware"] = "fixed"
    size_chars: int = Field(default=1200, gt=0)
    overlap_chars: int = Field(default=150, ge=0)

    def config_hash(self) -> str:
        import hashlib
        import json
        canonical = self.model_dump_json(sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def validate_overlap(self):
        if self.overlap_chars >= self.size_chars:
            raise ValueError("overlap_chars must be less than size_chars")


class RetrievalConfig(BaseModel):
    method: Literal["dense"] = "dense"
    top_k: int = Field(default=5, ge=1, le=20)
    filters: Dict[str, Any] = Field(default_factory=dict)

    def config_hash(self) -> str:
        import hashlib
        import json
        canonical = self.model_dump_json(sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


class JudgeConfig(BaseModel):
    enabled: bool = False
    provider: Literal["ragas", "custom"] = "ragas"
    model: str = "gpt-4"
    prompt_version: str = "1.0"
    api_key: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)

    def config_hash(self) -> str:
        import hashlib
        import json
        # Pydantic v2: use model_dump with json.dumps for sorted keys
        data = self.model_dump(exclude={"api_key"})
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]