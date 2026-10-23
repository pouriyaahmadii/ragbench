import pytest
import uuid
from typing import List
from unittest.mock import Mock, AsyncMock, patch

from app.retrieval.schemas import (
    RetrievalResult,
    RetrievalConfig,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalError,
    DimensionMismatchError,
    CollectionNotFoundError,
    InvalidFilterError,
)
from app.retrieval.service import RetrievalService
from app.config import Settings


class TestRetrievalSchemas:
    """Tests for retrieval schemas."""

    def test_retrieval_result_creation(self):
        """Test creating a RetrievalResult with all fields."""
        chunk_id = uuid.uuid4()
        doc_id = uuid.uuid4()
        doc_ver_id = uuid.uuid4()
        corpus_id = uuid.uuid4()
        
        result = RetrievalResult(
            rank=1,
            score=0.95,
            chunk_id=chunk_id,
            document_id=doc_id,
            document_version_id=doc_ver_id,
            corpus_id=corpus_id,
            page_number=5,
            source_title="Test Document",
            text="This is a test chunk.",
            metadata={"key": "value"},
        )
        
        assert result.rank == 1
        assert result.score == 0.95
        assert result.chunk_id == chunk_id
        assert result.document_id == doc_id
        assert result.document_version_id == doc_ver_id
        assert result.corpus_id == corpus_id
        assert result.page_number == 5
        assert result.source_title == "Test Document"
        assert result.text == "This is a test chunk."
        assert result.metadata == {"key": "value"}

    def test_retrieval_config_defaults(self):
        """Test RetrievalConfig default values."""
        config = RetrievalConfig()
        
        assert config.method == "dense"
        assert config.top_k == 5
        assert config.filters == {}
        assert config.score_threshold is None

    def test_retrieval_config_custom(self):
        """Test RetrievalConfig with custom values."""
        config = RetrievalConfig(
            method="hybrid",
            top_k=10,
            filters={"document_id": "uuid"},
            score_threshold=0.7,
        )
        
        assert config.method == "hybrid"
        assert config.top_k == 10
        assert config.filters == {"document_id": "uuid"}
        assert config.score_threshold == 0.7

    def test_retrieval_request(self):
        """Test RetrievalRequest creation."""
        query_vector = [0.1, 0.2, 0.3]
        corpus_id = uuid.uuid4()
        
        request = RetrievalRequest(
            query_vector=query_vector,
            corpus_id=corpus_id,
        )
        
        assert request.query_vector == query_vector
        assert request.corpus_id == corpus_id
        assert isinstance(request.config, RetrievalConfig)

    def test_retrieval_response(self):
        """Test RetrievalResponse creation."""
        chunk_id = uuid.uuid4()
        doc_id = uuid.uuid4()
        
        result = RetrievalResult(
            rank=1,
            score=0.95,
            chunk_id=uuid.uuid4(),
            document_id=doc_id,
            document_version_id=uuid.uuid4(),
            corpus_id=uuid.uuid4(),
            source_title="Test",
            text="Test chunk",
        )
        
        response = RetrievalResponse(
            results=[result],
            query_time_ms=100,
            total_candidates=1,
            config=RetrievalConfig(),
        )
        
        assert len(response.results) == 1
        assert response.query_time_ms == 100
        assert response.total_candidates == 1


class TestRetrievalExceptions:
    """Tests for retrieval exceptions."""

    def test_retrieval_error(self):
        error = RetrievalError("Test error", "TEST_CODE")
        assert str(error) == "Test error"
        assert error.error_code == "TEST_CODE"

    def test_dimension_mismatch_error(self):
        error = DimensionMismatchError(expected=384, actual=768)
        assert "384" in str(error)
        assert "768" in str(error)
        assert error.expected == 384
        assert error.actual == 768
        assert error.error_code == "DIMENSION_MISMATCH"

    def test_collection_not_found_error(self):
        error = CollectionNotFoundError("test_collection")
        assert "test_collection" in str(error)
        assert error.collection_name == "test_collection"
        assert error.error_code == "COLLECTION_NOT_FOUND"

    def test_invalid_filter_error(self):
        error = InvalidFilterError("Invalid filter")
        assert str(error) == "Invalid filter"
        assert error.error_code == "INVALID_FILTER"


class TestRetrievalService:
    """Tests for RetrievalService (mocked)."""

    @pytest.fixture
    def mock_settings(self) -> Settings:
        return Settings(
            MOCK_MODE=True,
            EMBEDDING_DIMENSION=384,
            EMBEDDING_PROVIDER="mock",
            EMBEDDING_MODEL="mock",
        )

    @pytest.fixture
    def mock_client(self):
        client = Mock()
        # Use side_effect to allow per-test configuration
        client.get_collections = Mock()
        client.get_collection = Mock()
        client.search = Mock()
        client.retrieve = Mock()
        return client

    @pytest.fixture
    def retrieval_service(self, mock_settings: Settings, mock_client):
        with patch('app.retrieval.service.get_qdrant_client', return_value=mock_client):
            service = RetrievalService(mock_settings)
            service._client = mock_client
            return service

    @pytest.mark.asyncio
    async def test_validate_collection_success(self, retrieval_service, mock_client):
        """Test successful collection validation."""
        corpus_id = uuid.uuid4()
        collection_name = f"corpus_{corpus_id}"
        
        # Configure mock for this test
        collections_response = Mock()
        collections_response.collections = [Mock()]
        collections_response.collections[0].name = collection_name
        mock_client.get_collections.return_value = collections_response
        mock_client.get_collection.return_value = Mock(
            config=Mock(params=Mock(vectors=Mock(size=384)))
        )
        
        result = await retrieval_service._validate_collection(corpus_id, 384)
        
        assert result == collection_name

    @pytest.mark.asyncio
    async def test_validate_collection_not_found(self, retrieval_service, mock_client):
        """Test collection not found error."""
        corpus_id = uuid.uuid4()
        
        collections_response = Mock()
        collections_response.collections = []
        mock_client.get_collections.return_value = collections_response
        
        with pytest.raises(CollectionNotFoundError):
            await retrieval_service._validate_collection(corpus_id, 384)

    @pytest.mark.asyncio
    async def test_validate_collection_dimension_mismatch(self, retrieval_service, mock_client):
        """Test dimension mismatch error."""
        corpus_id = uuid.uuid4()
        collection_name = f"corpus_{corpus_id}"
        
        collections_response = Mock()
        collections_response.collections = [Mock()]
        collections_response.collections[0].name = collection_name
        mock_client.get_collections.return_value = collections_response
        mock_client.get_collection.return_value = Mock(
            config=Mock(params=Mock(vectors=Mock(size=768)))
        )
        
        with pytest.raises(DimensionMismatchError) as exc_info:
            await retrieval_service._validate_collection(corpus_id, 384)
        
        assert exc_info.value.expected == 384
        assert exc_info.value.actual == 768

    def test_build_filter_empty(self, retrieval_service):
        """Test filter building with empty filters."""
        filter_result = retrieval_service._build_filter({})
        assert filter_result is None

    def test_build_filter_single_value(self, retrieval_service):
        """Test filter building with single value."""
        filters = {"document_id": "uuid123"}
        filter_obj = retrieval_service._build_filter(filters)
        
        assert filter_obj is not None

    def test_build_filter_list_value(self, retrieval_service):
        """Test filter building with list values."""
        filters = {"document_id": ["uuid1", "uuid2"]}
        filter_obj = retrieval_service._build_filter(filters)
        
        assert filter_obj is not None

    def test_build_filter_multiple_fields(self, retrieval_service):
        """Test filter building with multiple fields."""
        filters = {
            "document_id": "uuid1",
            "page_number": 5,
        }
        filter_obj = retrieval_service._build_filter(filters)
        
        assert filter_obj is not None

    @pytest.mark.asyncio
    async def test_retrieve_success(self, retrieval_service, mock_client):
        """Test successful retrieval."""
        corpus_id = uuid.uuid4()
        chunk_id = uuid.uuid4()
        doc_id = uuid.uuid4()
        doc_ver_id = uuid.uuid4()
        
        # Setup mock client
        collections_response = Mock()
        collections_response.collections = [Mock()]
        collections_response.collections[0].name = f"corpus_{corpus_id}"
        mock_client.get_collections.return_value = collections_response
        mock_client.get_collection.return_value = Mock(
            config=Mock(params=Mock(vectors=Mock(size=384)))
        )
        mock_client.search.return_value = [
            Mock(
                id=str(uuid.uuid4()),
                score=0.95,
                payload={
                    "chunk_id": str(chunk_id),
                    "document_id": str(doc_id),
                    "document_version_id": str(doc_ver_id),
                    "corpus_id": str(corpus_id),
                    "page_number": 5,
                    "source_title": "Test Document",
                    "text_excerpt": "This is a test chunk.",
                }
            )
        ]
        
        request = RetrievalRequest(
            query_vector=[0.1, 0.2, 0.3],
            corpus_id=corpus_id,
        )
        
        response = await retrieval_service.retrieve(request)
        
        assert isinstance(response, RetrievalResponse)
        assert len(response.results) == 1
        assert response.results[0].score == 0.95
        assert response.query_time_ms >= 0

    @pytest.mark.asyncio
    async def test_retrieve_empty_results(self, retrieval_service, mock_client):
        """Test retrieval with empty results."""
        corpus_id = uuid.uuid4()
        
        collections_response = Mock()
        collections_response.collections = [Mock()]
        collections_response.collections[0].name = f"corpus_{corpus_id}"
        mock_client.get_collections.return_value = collections_response
        mock_client.get_collection.return_value = Mock(
            config=Mock(params=Mock(vectors=Mock(size=384)))
        )
        mock_client.search.return_value = []
        
        request = RetrievalRequest(
            query_vector=[0.1, 0.2, 0.3],
            corpus_id=corpus_id,
        )
        
        response = await retrieval_service.retrieve(request)
        
        assert isinstance(response, RetrievalResponse)
        assert len(response.results) == 0

    @pytest.mark.asyncio
    async def test_retrieve_dimension_mismatch(self, retrieval_service, mock_client):
        """Test retrieval with dimension mismatch."""
        corpus_id = uuid.uuid4()
        
        collections_response = Mock()
        collections_response.collections = [Mock()]
        collections_response.collections[0].name = f"corpus_{corpus_id}"
        mock_client.get_collections.return_value = collections_response
        mock_client.get_collection.return_value = Mock(
            config=Mock(params=Mock(vectors=Mock(size=768)))  # Different dimension
        )
        
        request = RetrievalRequest(
            query_vector=[0.1, 0.2, 0.3],  # 3 dimensions
            corpus_id=corpus_id,
        )
        
        with pytest.raises(DimensionMismatchError):
            await retrieval_service.retrieve(request)

    @pytest.mark.asyncio
    async def test_retrieve_collection_not_found(self, retrieval_service, mock_client):
        """Test retrieval with non-existent collection."""
        corpus_id = uuid.uuid4()
        
        collections_response = Mock()
        collections_response.collections = []
        mock_client.get_collections.return_value = collections_response
        
        request = RetrievalRequest(
            query_vector=[0.1, 0.2, 0.3],
            corpus_id=corpus_id,
        )
        
        with pytest.raises(CollectionNotFoundError):
            await retrieval_service.retrieve(request)

    @pytest.mark.asyncio
    async def test_retrieve_with_filters(self, retrieval_service, mock_client):
        """Test retrieval with metadata filters."""
        corpus_id = uuid.uuid4()
        
        collections_response = Mock()
        collections_response.collections = [Mock()]
        collections_response.collections[0].name = f"corpus_{corpus_id}"
        mock_client.get_collections.return_value = collections_response
        mock_client.get_collection.return_value = Mock(
            config=Mock(params=Mock(vectors=Mock(size=384)))
        )
        mock_client.search.return_value = [
            Mock(
                id=str(uuid.uuid4()),
                score=0.95,
                payload={
                    "chunk_id": str(uuid.uuid4()),
                    "document_id": str(uuid.uuid4()),
                    "document_version_id": str(uuid.uuid4()),
                    "corpus_id": str(uuid.uuid4()),
                    "page_number": 1,
                    "source_title": "Test",
                    "text_excerpt": "Filtered result",
                }
            )
        ]
        
        request = RetrievalRequest(
            query_vector=[0.1, 0.2, 0.3],
            corpus_id=corpus_id,
            config=RetrievalConfig(filters={"document_id": "doc1"}),
        )
        
        response = await retrieval_service.retrieve(request)
        
        assert len(response.results) == 1
        # Verify search was called with filter
        mock_client.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_citation(self, retrieval_service, mock_client):
        """Test citation validation."""
        corpus_id = uuid.uuid4()
        chunk_id = uuid.uuid4()
        
        collections_response = Mock()
        collections_response.collections = [Mock()]
        collections_response.collections[0].name = f"corpus_{corpus_id}"
        mock_client.get_collections.return_value = collections_response
        mock_client.get_collection.return_value = Mock(
            config=Mock(params=Mock(vectors=Mock(size=384)))
        )
        mock_client.retrieve.return_value = [
            Mock(id=str(uuid.uuid4()), payload={"chunk_id": str(chunk_id)})
        ]
        
        result = await retrieval_service.validate_citation(chunk_id, corpus_id)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_citation_not_found(self, retrieval_service, mock_client):
        """Test citation validation when chunk not found."""
        corpus_id = uuid.uuid4()
        
        collections_response = Mock()
        collections_response.collections = [Mock()]
        collections_response.collections[0].name = f"corpus_{corpus_id}"
        mock_client.get_collections.return_value = collections_response
        mock_client.get_collection.return_value = Mock(
            config=Mock(params=Mock(vectors=Mock(size=384)))
        )
        mock_client.retrieve.return_value = []
        
        result = await retrieval_service.validate_citation(uuid.uuid4(), corpus_id)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_get_chunk_metadata(self, retrieval_service, mock_client):
        """Test getting chunk metadata."""
        chunk_id = uuid.uuid4()
        corpus_id = uuid.uuid4()
        
        collections_response = Mock()
        collections_response.collections = [Mock()]
        collections_response.collections[0].name = f"corpus_{corpus_id}"
        mock_client.get_collections.return_value = collections_response
        mock_client.get_collection.return_value = Mock(
            config=Mock(params=Mock(vectors=Mock(size=384)))
        )
        mock_client.retrieve.return_value = [
            Mock(
                id=str(chunk_id),
                payload={"chunk_id": str(chunk_id), "test": "data"},
            )
        ]
        
        result = await retrieval_service.get_chunk_metadata(chunk_id, corpus_id)
        
        assert result is not None
        assert result["id"] == str(chunk_id)
        assert "payload" in result


class TestRetrievalResponseSerialization:
    """Tests for RetrievalResponse serialization."""

    def test_response_json_serialization(self):
        """Test that RetrievalResponse can be serialized to JSON."""
        result = RetrievalResult(
            rank=1,
            score=0.95,
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            document_version_id=uuid.uuid4(),
            corpus_id=uuid.uuid4(),
            source_title="Test",
            text="Test chunk",
        )
        
        response = RetrievalResponse(
            results=[result],
            query_time_ms=100,
            total_candidates=1,
            config=RetrievalConfig(),
        )
        
        json_str = response.model_dump_json()
        assert "results" in json_str
        assert "query_time_ms" in json_str

    def test_response_deserialization(self):
        """Test that RetrievalResponse can be deserialized from JSON."""
        result = RetrievalResult(
            rank=1,
            score=0.95,
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            document_version_id=uuid.uuid4(),
            corpus_id=uuid.uuid4(),
            source_title="Test",
            text="Test chunk",
        )
        
        response = RetrievalResponse(
            results=[result],
            query_time_ms=100,
            total_candidates=1,
            config=RetrievalConfig(),
        )
        
        json_str = response.model_dump_json()
        restored = RetrievalResponse.model_validate_json(json_str)
        
        assert len(restored.results) == 1
        assert restored.results[0].score == 0.95