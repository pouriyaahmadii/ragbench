from typing import Optional
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams
from app.config import Settings


# Global client instances
_qdrant_client: Optional[QdrantClient] = None
_async_qdrant_client: Optional[AsyncQdrantClient] = None


def get_qdrant_client(settings: Optional[Settings] = None) -> QdrantClient:
    """Get or create synchronous Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        if settings:
            url = settings.QDRANT_URL
            api_key = settings.QDRANT_API_KEY
        else:
            from app.config import settings as default_settings
            url = default_settings.QDRANT_URL
            api_key = default_settings.QDRANT_API_KEY
        
        _qdrant_client = QdrantClient(
            url=url,
            api_key=api_key,
            timeout=60.0,
        )
    return _qdrant_client


async def get_async_qdrant_client(settings: Optional[Settings] = None) -> AsyncQdrantClient:
    """Get or create asynchronous Qdrant client."""
    global _async_qdrant_client
    if _async_qdrant_client is None:
        if settings:
            url = settings.QDRANT_URL
            api_key = settings.QDRANT_API_KEY
        else:
            from app.config import settings as default_settings
            url = default_settings.QDRANT_URL
            api_key = default_settings.QDRANT_API_KEY
        
        _async_qdrant_client = AsyncQdrantClient(
            url=url,
            api_key=api_key,
            timeout=60.0,
        )
    return _async_qdrant_client


def close_qdrant_clients():
    """Close Qdrant client connections."""
    global _qdrant_client, _async_qdrant_client
    if _qdrant_client:
        _qdrant_client.close()
        _qdrant_client = None
    
    # Async client closure would need async context
    # Handled in async context