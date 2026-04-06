#!/usr/bin/env python3
"""
Qdrant Memory MCP Server - Agent-Based Collections (No User ID)
A Model Context Protocol server for managing memories using Qdrant vector database.
Each agent gets its own collection, eliminating the need for user_id.
"""

import argparse
import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings from text content."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service with specified model.

        Popular models and their dimensions:
        - all-MiniLM-L6-v2: 384 dimensions (fast, good for most use cases)
        - all-mpnet-base-v2: 768 dimensions (better quality, slower)
        - all-MiniLM-L12-v2: 384 dimensions (balanced)
        - paraphrase-multilingual-MiniLM-L12-v2: 384 dimensions (multilingual)
        """
        self.model_name = model_name
        self.model = None
        self.vector_size = None

    def _lazy_load_model(self):
        """Load the model only when first needed."""
        if self.model is None:
            import os
            # Check if model is already cached locally
            cache_dir = os.path.expanduser("~/.cache/torch/sentence_transformers")
            model_cache_path = os.path.join(cache_dir, self.model_name.replace("/", "_"))
            
            if os.path.exists(model_cache_path):
                logger.info(f"Loading cached model from: {model_cache_path}")
            else:
                logger.info(f"Downloading model: {self.model_name} (this may take a moment on first run)")
            
            # Load with optimizations
            self.model = SentenceTransformer(
                self.model_name,
                device='cpu',  # Force CPU for consistency
                cache_folder=cache_dir
            )
            
            # Set model to evaluation mode for faster inference
            self.model.eval()
            
            # Get the actual vector dimension from the model
            test_embedding = self.model.encode(["test"], show_progress_bar=False)
            self.vector_size = test_embedding.shape[1]
            logger.info(f"Model loaded successfully. Vector dimension: {self.vector_size}")

    def get_vector_size(self) -> int:
        """Get the vector dimension for this model."""
        self._lazy_load_model()
        return self.vector_size

    def encode(self, text: str) -> List[float]:
        """Generate embedding vector for given text."""
        self._lazy_load_model()

        # Clean and prepare text
        cleaned_text = text.strip()
        if not cleaned_text:
            # Return zero vector for empty text
            return [0.0] * self.vector_size

        # Generate embedding with optimizations
        embedding = self.model.encode(
            cleaned_text,
            show_progress_bar=False,
            convert_to_tensor=False,
            normalize_embeddings=False
        )

        # Convert to list of floats
        return embedding.tolist()

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently."""
        self._lazy_load_model()

        # Clean texts
        cleaned_texts = [text.strip() if text.strip() else "empty" for text in texts]

        # Generate embeddings in batch (more efficient)
        embeddings = self.model.encode(
            cleaned_texts,
            show_progress_bar=False,
            convert_to_tensor=False,
            normalize_embeddings=False,
            batch_size=32  # Process in batches for efficiency
        )

        # Convert to list of lists
        return [emb.tolist() for emb in embeddings]


class MemoryType(Enum):
    SUMMARY = "summary"
    LONG_TERM = "long_term"


@dataclass
class Memory:
    id: str
    memory_type: MemoryType
    content: str
    timestamp: datetime
    tags: List[str]
    metadata: Dict[str, Any]
    vector: Optional[List[float]] = None


class QdrantMemoryServer:
    def __init__(self,
                 agent_id: str,
                 server_name: str = "qdrant-memory-server",
                 qdrant_host: str = "localhost",
                 qdrant_port: int = 6333,
                 embedding_model: str = "all-MiniLM-L6-v2"):
        self.agent_id = agent_id
        self.server_name = server_name
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port

        # Initialize embedding service
        self.embedding_service = EmbeddingService(embedding_model)

        # Create collection name based on agent ID
        self.collection_name = self._get_collection_name(agent_id)
        self.client: Optional[QdrantClient] = None
        self.server = Server(server_name)
        self._setup_handlers()

    def _get_collection_name(self, agent_id: str) -> str:
        """Generate a safe collection name from agent ID."""
        # Hash the agent ID to create a consistent, safe collection name
        hash_obj = hashlib.md5(agent_id.encode())
        hash_hex = hash_obj.hexdigest()[:8]
        # Ensure collection name starts with letter and contains only valid chars
        safe_name = f"agent_{hash_hex}_{agent_id}".replace("-", "_").replace(" ", "_")
        # Limit length and ensure valid characters
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')[:63]
        return safe_name.lower()

    async def initialize_qdrant(self):
        """Initialize Qdrant client and ensure agent's collection exists."""
        try:
            logger.info(f"Connecting to Qdrant at {self.qdrant_host}:{self.qdrant_port}")
            
            self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port, check_compatibility=False)

            vector_size = self.embedding_service.get_vector_size()

            # Check if agent's collection exists, create if not
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating collection for agent {self.agent_id}: {self.collection_name}")
                logger.info(f"Vector size: {vector_size}")

                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )

                # Add agent metadata to the collection
                self._initialize_agent_metadata()
            else:
                logger.info(f"Collection {self.collection_name} for agent {self.agent_id} already exists")

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant for agent {self.agent_id}: {e}")
            logger.error(f"Please ensure Qdrant is running at {self.qdrant_host}:{self.qdrant_port}")
            raise

    def _initialize_agent_metadata(self):
        """Initialize agent metadata in the collection."""
        # Fix: Use integer 0 as a reserved ID for metadata (consistent across restarts)
        vector_size = self.embedding_service.get_vector_size()
        metadata_point = PointStruct(
            id=0,  # Use integer ID
            vector=[0.0] * vector_size,
            payload={
                "type": "agent_metadata",
                "agent_id": self.agent_id,
                "created_at": datetime.now().isoformat(),
                "collection_name": self.collection_name,
                "server_name": self.server_name,
                "vector_size": vector_size
            }
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[metadata_point]
        )

    def _setup_handlers(self):
        """Setup MCP server handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available memory management tools."""
            return [
                types.Tool(
                    name="get_summary",
                    description="Get the agent's summary information (role, work description, etc.)",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="update_summary",
                    description="Update or create the agent's summary information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "Summary of user's role, work, or context"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional tags for categorization",
                                "default": []
                            }
                        },
                        "required": ["summary"]
                    }
                ),
                types.Tool(
                    name="add_memory",
                    description="Add a new long-term memory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Memory content"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tags for categorization",
                                "default": []
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata",
                                "default": {}
                            }
                        },
                        "required": ["content"]
                    }
                ),
                types.Tool(
                    name="search_memories",
                    description="Search memories by content similarity or tags",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for semantic search"
                            },
                            "memory_type": {
                                "type": "string",
                                "enum": ["summary", "long_term", "all"],
                                "description": "Type of memories to search",
                                "default": "all"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Filter by tags",
                                "default": []
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10
                            }
                        }
                    }
                ),
                types.Tool(
                    name="update_memory",
                    description="Update an existing memory by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "memory_id": {
                                "type": "string",
                                "description": "Memory ID to update"
                            },
                            "content": {
                                "type": "string",
                                "description": "New content"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Updated tags"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Updated metadata"
                            }
                        },
                        "required": ["memory_id"]
                    }
                ),
                types.Tool(
                    name="delete_memory",
                    description="Delete a memory by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "memory_id": {
                                "type": "string",
                                "description": "Memory ID to delete"
                            }
                        },
                        "required": ["memory_id"]
                    }
                ),
                types.Tool(
                    name="list_memories",
                    description="List all memories with pagination",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "memory_type": {
                                "type": "string",
                                "enum": ["summary", "long_term", "all"],
                                "description": "Type of memories to list",
                                "default": "all"
                            },
                            "offset": {
                                "type": "integer",
                                "description": "Pagination offset",
                                "default": 0
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 20
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_memory_stats",
                    description="Get memory usage statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_agent_info",
                    description="Get information about this agent's memory collection",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="cleanup_old_memories",
                    description="Clean up old memories based on retention policy",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days_old": {
                                "type": "integer",
                                "description": "Remove memories older than this many days",
                                "default": 365
                            },
                            "dry_run": {
                                "type": "boolean",
                                "description": "If true, only return what would be deleted",
                                "default": True
                            }
                        }
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls."""
            try:
                if name == "get_summary":
                    result = await self._get_summary()
                elif name == "update_summary":
                    result = await self._update_summary(
                        arguments["summary"],
                        arguments.get("tags", [])
                    )
                elif name == "add_memory":
                    result = await self._add_memory(
                        arguments["content"],
                        arguments.get("tags", []),
                        arguments.get("metadata", {})
                    )
                elif name == "search_memories":
                    result = await self._search_memories(
                        arguments.get("query"),
                        arguments.get("memory_type", "all"),
                        arguments.get("tags", []),
                        arguments.get("limit", 10)
                    )
                elif name == "update_memory":
                    result = await self._update_memory(
                        arguments["memory_id"],
                        arguments.get("content"),
                        arguments.get("tags"),
                        arguments.get("metadata")
                    )
                elif name == "delete_memory":
                    result = await self._delete_memory(arguments["memory_id"])
                elif name == "list_memories":
                    result = await self._list_memories(
                        arguments.get("memory_type", "all"),
                        arguments.get("offset", 0),
                        arguments.get("limit", 20)
                    )
                elif name == "get_memory_stats":
                    result = await self._get_memory_stats()
                elif name == "get_agent_info":
                    result = await self._get_agent_info()
                elif name == "cleanup_old_memories":
                    result = await self._cleanup_old_memories(
                        arguments.get("days_old", 365),
                        arguments.get("dry_run", True)
                    )
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

            except Exception as e:
                error_msg = f"Error executing {name}: {str(e)}"
                logger.error(error_msg)
                return [types.TextContent(type="text", text=json.dumps({"error": error_msg}))]

    async def _get_summary(self) -> Dict[str, Any]:
        """Get the agent's summary information."""
        filter_condition = models.Filter(
            must=[
                models.FieldCondition(key="memory_type", match=models.MatchValue(value="summary"))
            ]
        )

        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=filter_condition,
            limit=1,
            with_payload=True
        )[0]

        if results:
            payload = results[0].payload
            return {
                "agent_id": self.agent_id,
                "summary": payload.get("content"),
                "timestamp": payload.get("timestamp"),
                "tags": payload.get("tags", []),
                "metadata": payload.get("metadata", {})
            }
        else:
            return {
                "agent_id": self.agent_id,
                "summary": None,
                "message": "No summary found"
            }

    async def _update_summary(self, summary: str, tags: List[str]) -> Dict[str, Any]:
        """Update or create the agent's summary."""
        # Fix: Use integer 1 instead of string "agent_summary"
        memory_id = 1  # Changed from "agent_summary"
        timestamp = datetime.now()
        summary_vector = self.embedding_service.encode(summary)
        point = PointStruct(
            id=memory_id,
            vector=summary_vector,
            payload={
                "memory_type": "summary",
                "content": summary,
                "timestamp": timestamp.isoformat(),
                "tags": tags,
                "metadata": {
                    "last_updated": timestamp.isoformat(),
                    "agent_id": self.agent_id
                }
            }
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

        return {
            "success": True,
            "agent_id": self.agent_id,
            "memory_id": memory_id,
            "summary": summary,
            "timestamp": timestamp.isoformat(),
            "tags": tags,
            "vector_dimension": len(summary_vector)
        }

    async def _add_memory(self, content: str, tags: List[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new long-term memory."""
        import uuid
        memory_id = f"{uuid.uuid4()}"
        timestamp = datetime.now()

        # Generate embedding for the content
        content_vector = self.embedding_service.encode(content)

        # Add agent info to metadata
        enriched_metadata = {
            **metadata,
            "created_at": timestamp.isoformat(),
            "agent_id": self.agent_id,
            "content_length": len(content)
        }

        point = PointStruct(
            id=memory_id,
            vector=content_vector,  # Use actual embedding
            payload={
                "memory_type": "long_term",
                "content": content,
                "timestamp": timestamp.isoformat(),
                "tags": tags,
                "metadata": enriched_metadata
            }
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

        return {
            "success": True,
            "agent_id": self.agent_id,
            "memory_id": memory_id,
            "content": content,
            "timestamp": timestamp.isoformat(),
            "tags": tags,
            "metadata": enriched_metadata,
            "vector_dimension": len(content_vector)
        }

    async def _search_memories(self, query: Optional[str], memory_type: str, tags: List[str], limit: int) -> Dict[
        str, Any]:
        """Search memories by content similarity or tags."""
        must_conditions = []

        # Filter by memory type if specified
        if memory_type != "all":
            must_conditions.append(
                models.FieldCondition(key="memory_type", match=models.MatchValue(value=memory_type))
            )

        # Filter by tags if specified
        if tags:
            for tag in tags:
                must_conditions.append(
                    models.FieldCondition(key="tags", match=models.MatchAny(any=[tag]))
                )

        # Build filter condition - exclude agent metadata from search results
        filter_condition = models.Filter(
            must=must_conditions,
            must_not=[
                models.FieldCondition(key="type", match=models.MatchValue(value="agent_metadata"))
            ]
        )

        if query:
            # Generate embedding for the search query
            query_vector = self.embedding_service.encode(query)

            # Use query_points method for semantic search (search is deprecated)
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=filter_condition,
                limit=limit,
                with_payload=True
            ).points
        else:
            # Just filter without semantic search using scroll
            results, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_condition,
                limit=limit,
                with_payload=True
            )

        memories = []
        for result in results:
            payload = result.payload
            memories.append({
                "memory_id": result.id,
                "content": payload.get("content"),
                "memory_type": payload.get("memory_type"),
                "timestamp": payload.get("timestamp"),
                "tags": payload.get("tags", []),
                "metadata": payload.get("metadata", {}),
                "score": getattr(result, 'score', None)
            })

        return {
            "agent_id": self.agent_id,
            "query": query,
            "memory_type": memory_type,
            "filter_tags": tags,
            "results": memories,
            "total_found": len(memories),
            "semantic_search": query is not None
        }

    async def _update_memory(self, memory_id: str, content: Optional[str], tags: Optional[List[str]],
                             metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Update an existing memory."""
        try:
            existing = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id],
                with_payload=True
            )[0]

            payload = existing.payload.copy()
            timestamp = datetime.now()

            # Determine if we need to regenerate the vector
            regenerate_vector = content is not None
            current_vector = None

            if content is not None:
                payload["content"] = content
                payload["metadata"]["content_length"] = len(content)
                # Generate new embedding for updated content
                current_vector = self.embedding_service.encode(content)

            if tags is not None:
                payload["tags"] = tags
            if metadata is not None:
                payload["metadata"].update(metadata)

            payload["metadata"]["last_updated"] = timestamp.isoformat()
            payload["metadata"]["agent_id"] = self.agent_id

            # If content wasn't updated, use a placeholder vector (Qdrant requires a vector)
            if current_vector is None:
                current_vector = [0.0] * self.embedding_service.get_vector_size()

            point = PointStruct(
                id=memory_id,
                vector=current_vector,
                payload=payload
            )

            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

            return {
                "success": True,
                "agent_id": self.agent_id,
                "memory_id": memory_id,
                "updated_at": timestamp.isoformat(),
                "updated_fields": {
                    "content": content is not None,
                    "tags": tags is not None,
                    "metadata": metadata is not None
                },
                "vector_regenerated": regenerate_vector
            }

        except Exception as e:
            return {
                "success": False,
                "agent_id": self.agent_id,
                "error": f"Memory not found or update failed: {str(e)}"
            }

    async def _delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """Delete a memory by ID."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[memory_id])
            )

            return {
                "success": True,
                "agent_id": self.agent_id,
                "memory_id": memory_id,
                "deleted_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "agent_id": self.agent_id,
                "error": f"Failed to delete memory: {str(e)}"
            }

    async def _list_memories(self, memory_type: str, offset: int, limit: int) -> Dict[str, Any]:
        """List all memories with pagination."""
        must_conditions = []

        if memory_type != "all":
            must_conditions.append(
                models.FieldCondition(key="memory_type", match=models.MatchValue(value=memory_type))
            )

        # Exclude agent metadata from list results
        must_conditions.append(
            models.FieldCondition(
                key="type",
                match=models.MatchValue(value="agent_metadata"),
            )
        )

        filter_condition = models.Filter(must=must_conditions) if must_conditions else models.Filter(
            must_not=[
                models.FieldCondition(key="type", match=models.MatchValue(value="agent_metadata"))
            ]
        )

        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=filter_condition,
            offset=offset,
            limit=limit,
            with_payload=True
        )[0]

        memories = []
        for result in results:
            payload = result.payload
            memories.append({
                "memory_id": result.id,
                "content": payload.get("content"),
                "memory_type": payload.get("memory_type"),
                "timestamp": payload.get("timestamp"),
                "tags": payload.get("tags", []),
                "metadata": payload.get("metadata", {})
            })

        return {
            "agent_id": self.agent_id,
            "memory_type": memory_type,
            "offset": offset,
            "limit": limit,
            "memories": memories,
            "count": len(memories)
        }

    async def _get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        # Get summary count
        summary_filter = models.Filter(
            must=[
                models.FieldCondition(key="memory_type", match=models.MatchValue(value="summary"))
            ]
        )

        # Get long-term memory count
        ltm_filter = models.Filter(
            must=[
                models.FieldCondition(key="memory_type", match=models.MatchValue(value="long_term"))
            ]
        )

        summary_count = self.client.count(
            collection_name=self.collection_name,
            count_filter=summary_filter
        ).count

        ltm_count = self.client.count(
            collection_name=self.collection_name,
            count_filter=ltm_filter
        ).count

        return {
            "agent_id": self.agent_id,
            "summary_memories": summary_count,
            "long_term_memories": ltm_count,
            "total_memories": summary_count + ltm_count,
            "generated_at": datetime.now().isoformat()
        }

    async def _get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent's memory collection."""
        try:
            # Get collection info
            collection_info = self.client.get_collection(self.collection_name)

            # Get total points count (excluding metadata)
            total_filter = models.Filter(
                must_not=[
                    models.FieldCondition(key="type", match=models.MatchValue(value="agent_metadata"))
                ]
            )
            total_count = self.client.count(
                collection_name=self.collection_name,
                count_filter=total_filter
            ).count

            return {
                "agent_id": self.agent_id,
                "collection_name": self.collection_name,
                "server_name": self.server_name,
                "total_memories": total_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.value,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "agent_id": self.agent_id,
                "error": f"Failed to get agent info: {str(e)}"
            }

    async def _cleanup_old_memories(self, days_old: int, dry_run: bool) -> Dict[str, Any]:
        """Clean up old memories based on retention policy."""
        try:
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)

            # Exclude agent metadata from cleanup
            filter_condition = models.Filter(
                must_not=[
                    models.FieldCondition(key="type", match=models.MatchValue(value="agent_metadata"))
                ]
            )

            # Get all memories
            all_memories = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_condition,
                limit=10000,  # Adjust based on your needs
                with_payload=True
            )[0]

            # Find old memories
            old_memories = []
            for memory in all_memories:
                timestamp_str = memory.payload.get("timestamp")
                if timestamp_str:
                    try:
                        memory_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).timestamp()
                        if memory_time < cutoff_date:
                            old_memories.append({
                                "memory_id": memory.id,
                                "content": memory.payload.get("content", "")[:100] + "...",
                                "timestamp": timestamp_str,
                                "memory_type": memory.payload.get("memory_type")
                            })
                    except:
                        continue

            if not dry_run and old_memories:
                # Delete the old memories
                memory_ids = [mem["memory_id"] for mem in old_memories]
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.PointIdsList(points=memory_ids)
                )

            return {
                "agent_id": self.agent_id,
                "days_old": days_old,
                "dry_run": dry_run,
                "memories_found": len(old_memories),
                "memories_deleted": len(old_memories) if not dry_run else 0,
                "old_memories": old_memories[:10],  # Return first 10 for preview
                "executed_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "agent_id": self.agent_id,
                "error": f"Failed to cleanup memories: {str(e)}"
            }

    async def run(self):
        """Run the MCP server."""
        from mcp.server.stdio import stdio_server
        from mcp.server.lowlevel import NotificationOptions

        await self.initialize_qdrant()
        logger.info(f"Qdrant Memory MCP Server for agent '{self.agent_id}' starting...")
        logger.info(f"Using collection: {self.collection_name}")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=self.server_name,
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(
                            tools_changed=False,
                            prompts_changed=False,
                            resources_changed=False
                        ),
                        experimental_capabilities={},
                    ),
                ),
            )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Qdrant Memory MCP Server - Agent-Based Collections")
    parser.add_argument("--agent-id", required=True, help="Unique identifier for this agent")
    parser.add_argument("--name", help="Server name (defaults to qdrant-memory-{agent-id})")
    parser.add_argument("--host", default="localhost", help="Qdrant host")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port")

    args = parser.parse_args()

    # Generate server name if not provided
    server_name = args.name or f"qdrant-memory-{args.agent_id}"

    server = QdrantMemoryServer(
        agent_id=args.agent_id,
        server_name=server_name,
        qdrant_host=args.host,
        qdrant_port=args.port
    )

    asyncio.run(server.run())


if __name__ == "__main__":
    main()
