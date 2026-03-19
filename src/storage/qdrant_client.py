import logging
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    Distance, VectorParams, SparseVectorParams, PointStruct, 
    SparseVector, PayloadSchemaType
)
from src.core.config import get_settings
from src.core.exceptions import (
    VectorStoreInitializationError, 
    VectorStoreOperationError
)

logger = logging.getLogger(__name__)
settings = get_settings()

class QdrantManager:
    """
    Production-grade Qdrant manager (v2).
    Handles lifecycle, configuration validation, and indexing.
    """

    def __init__(self):
        self.client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=settings.QDRANT_API_KEY,
            grpc_port=settings.QDRANT_GRPC_PORT,
            prefer_grpc=False
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.dense_vector_name = "dense-text"
        self.sparse_vector_name = "sparse-text"

    async def init_collection(self):
        """
        Bootstrap the collection: create if missing, or validate if exists.
        Then ensures payload indexes are up to date.
        """
        try:
            exists = await self.client.collection_exists(self.collection_name)
            
            if not exists:
                logger.info(f"Creating collection '{self.collection_name}' with Hybrid Search config...")
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        self.dense_vector_name: VectorParams(
                            size=settings.QDRANT_VECTOR_SIZE,
                            distance=Distance.COSINE,
                        )
                    },
                    sparse_vectors_config={
                        self.sparse_vector_name: SparseVectorParams()
                    }
                )
                logger.info(f"Collection '{self.collection_name}' created.")
            else:
                logger.info(f"Validating existing collection '{self.collection_name}'...")
                info = await self.client.get_collection(self.collection_name)
                params = info.config.params
                
                # Validation Logic
                if not params.vectors or self.dense_vector_name not in params.vectors:
                    raise ValueError(f"Missing dense vector config for '{self.dense_vector_name}'")
                
                dense_cfg = params.vectors[self.dense_vector_name]
                if dense_cfg.size != settings.QDRANT_VECTOR_SIZE:
                    raise ValueError(f"Vector size mismatch: expected {settings.QDRANT_VECTOR_SIZE}, got {dense_cfg.size}")

                if not params.sparse_vectors or self.sparse_vector_name not in params.sparse_vectors:
                    raise ValueError(f"Missing sparse vector config for '{self.sparse_vector_name}'")
                
                logger.info(f"Collection '{self.collection_name}' validated.")

            # Always ensure payload indexes for performance
            await self._ensure_payload_indexes()
                
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {str(e)}")
            raise VectorStoreInitializationError(details={"error": str(e)})

    async def _ensure_payload_indexes(self):
        """
        Proactively creates indexes on frequently filtered fields.
        """
        indexed_fields = {
            "tenant_id": PayloadSchemaType.KEYWORD,
            "document_id": PayloadSchemaType.KEYWORD,
            "created_at": PayloadSchemaType.DATETIME,
        }
        
        for field, schema_type in indexed_fields.items():
            try:
                await self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field,
                    field_schema=schema_type
                )
            except Exception as e:
                # Often occurs if index already exists, which is fine
                logger.debug(f"Payload index for '{field}' skip/fail: {str(e)}")

    async def upsert_document(self, doc_id: str, dense_vector: list[float], sparse_indices: list[int], sparse_values: list[float], payload: dict):
        """
        Standardized document insertion for Hybrid Search.
        """
        try:
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=doc_id,
                        vector={
                            self.dense_vector_name: dense_vector,
                            self.sparse_vector_name: SparseVector(
                                indices=sparse_indices,
                                values=sparse_values
                            )
                        },
                        payload=payload
                    )
                ]
            )
        except Exception as e:
            raise VectorStoreOperationError(operation="upsert", details={"error": str(e)})

    async def health_check(self) -> dict:
        """
        Checks connection and collection health.
        """
        try:
            # Check basic connection
            # We use a simple lightweight check
            collections = await self.client.get_collections()
            
            # Check target collection
            exists = await self.client.collection_exists(self.collection_name)
            
            return {
                "status": "healthy" if exists else "degraded",
                "connection": "ok",
                "collection_found": exists,
                "collection_name": self.collection_name,
                "total_collections": len(collections.collections)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def close(self):
        """Closes the client connection."""
        await self.client.close()

# Singleton instance for easy access across the app
qdrant_manager = QdrantManager()
