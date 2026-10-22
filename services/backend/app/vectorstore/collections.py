from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    CollectionStatus, OptimizersConfigDiff,
)
from qdrant_client.http.exceptions import UnexpectedResponse


async def ensure_collection_exists(
    client: QdrantClient,
    collection_name: str,
    vector_dimension: int,
    distance: str = "Cosine",
) -> bool:
    """
    Ensure a collection exists, create if it doesn't.
    
    Returns:
        True if collection was created, False if it already existed
    """
    try:
        collections = client.get_collections()
        existing_names = [c.name for c in collections.collections]
        
        if collection_name in existing_names:
            # Verify dimension matches
            collection_info = client.get_collection(collection_name)
            existing_dim = collection_info.config.params.vectors.size
            if existing_dim != vector_dimension:
                raise ValueError(
                    f"Collection {collection_name} exists with different dimension: "
                    f"expected {vector_dimension}, got {existing_dim}"
                )
            return False
        
        # Create collection
        distance_enum = Distance.COSINE
        if distance.lower() == "dot":
            distance_enum = Distance.DOT
        elif distance.lower() == "euclid":
            distance_enum = Distance.EUCLID
        
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_dimension,
                distance=distance_enum,
            ),
            optimizers_config=OptimizersConfigDiff(
                indexing_threshold=20000,
            ),
        )
        return True
        
    except Exception as e:
        raise RuntimeError(f"Failed to ensure collection {collection_name}: {e}")


def upsert_vectors(
    client: QdrantClient,
    collection_name: str,
    vectors: List[Dict[str, Any]],
    batch_size: int = 100,
) -> int:
    """
    Upsert vectors to a collection in batches.
    
    Returns:
        Number of vectors upserted
    """
    if not vectors:
        return 0
    
    total_upserted = 0
    
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + 100]
        points = [
            PointStruct(
                id=v["id"],
                vector=v["vector"],
                payload=v.get("payload", {}),
            )
            for v in batch
        ]
        
        client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True,
        )
        total_upserted += len(batch)
    
    return total_upserted


async def upsert_vectors_async(
    client,
    collection_name: str,
    vectors: List[Dict[str, Any]],
    batch_size: int = 100,
) -> int:
    """
    Upsert vectors to a collection asynchronously.
    """
    if not vectors:
        return 0
    
    total_upserted = 0
    
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + 100]
        points = [
            PointStruct(
                id=v["id"],
                vector=v["vector"],
                payload=v.get("payload", {}),
            )
            for v in batch
        ]
        
        await client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True,
        )
        total_upserted += len(batch)
    
    return total_upserted


def delete_vectors(
    client: QdrantClient,
    collection_name: str,
    point_ids: List[str],
) -> bool:
    """
    Delete vectors by their IDs.
    """
    if not point_ids:
        return True
    
    try:
        client.delete(
            collection_name=collection_name,
            points_selector=point_ids,
            wait=True,
        )
        return True
    except Exception as e:
        raise RuntimeError(f"Failed to delete vectors from {collection_name}: {e}")


def search_vectors(
    client: QdrantClient,
    collection_name: str,
    query_vector: List[float],
    top_k: int = 5,
    filter_conditions: Optional[Dict] = None,
) -> List[Dict]:
    """
    Search for similar vectors.
    """
    query_filter = None
    if filter_conditions:
        # Build Qdrant filter from conditions
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        must_conditions = []
        for key, value in filter_conditions.items():
            must_conditions.append(
                FieldCondition(key=key, match=MatchValue(value=value))
            )
        query_filter = Filter(must=must_conditions) if must_conditions else None
    
    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
        with_vectors=False,
    )
    
    return [
        {
            "id": str(hit.id),
            "score": hit.score,
            "payload": hit.payload,
        }
        for hit in results
    ]


def get_collection_info(client: QdrantClient, collection_name: str) -> Optional[Dict]:
    """Get collection information."""
    try:
        info = client.get_collection(collection_name)
        return {
            "name": collection_name,
            "vectors_count": info.vectors_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "points_count": info.points_count,
            "status": info.status,
            "config": {
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance.value,
            },
        }
    except UnexpectedResponse:
        return None