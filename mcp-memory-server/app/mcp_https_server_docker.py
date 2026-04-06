#!/usr/bin/env python3
"""
MCP-Compatible HTTPS Memory Server - Docker Version
Handles all JSON-RPC requests at the root endpoint for Claude integration
Enhanced with Docker environment variable support and connection retry logic
"""

import json
import logging
import uuid
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="MCP Memory Server", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Global components
client: Optional[QdrantClient] = None
model: Optional[SentenceTransformer] = None
collections: Dict[str, str] = {}

# Configuration from environment variables
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

def create_jsonrpc_response(request_id: Optional[str], result: Any = None, error: Any = None) -> Dict[str, Any]:
    """Create a JSON-RPC 2.0 response"""
    response = {
        "jsonrpc": "2.0",
        "id": request_id
    }
    
    if error:
        response["error"] = error
    else:
        response["result"] = result
    
    return response

def create_jsonrpc_error(code: int, message: str, data: Any = None) -> Dict[str, Any]:
    """Create a JSON-RPC 2.0 error"""
    error = {
        "code": code,
        "message": message
    }
    if data:
        error["data"] = data
    return error

def get_collection_name(agent_id: str) -> str:
    """Generate collection name for agent"""
    if agent_id not in collections:
        import hashlib
        hash_obj = hashlib.md5(agent_id.encode())
        hash_hex = hash_obj.hexdigest()[:8]
        safe_name = f"agent_{hash_hex}_{agent_id}".replace("-", "_").replace(" ", "_")
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')[:63]
        collections[agent_id] = safe_name.lower()
    return collections[agent_id]

async def ensure_collection(agent_id: str) -> str:
    """Ensure agent collection exists"""
    collection_name = get_collection_name(agent_id)
    
    try:
        collections_list = client.get_collections().collections
        collection_names = [col.name for col in collections_list]
        
        if collection_name not in collection_names:
            logger.info(f"Creating collection for agent {agent_id}: {collection_name}")
            vector_size = 384  # all-MiniLM-L6-v2 dimension
            
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            
            # Add metadata point
            metadata_point = PointStruct(
                id=0,
                vector=[0.0] * vector_size,
                payload={
                    "type": "agent_metadata",
                    "agent_id": agent_id,
                    "created_at": datetime.now().isoformat()
                }
            )
            client.upsert(collection_name=collection_name, points=[metadata_point])
        
        return collection_name
    except Exception as e:
        logger.error(f"Error creating collection: {e}")
        raise

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log ALL incoming requests for debugging"""
    if log_level == "DEBUG":
        logger.debug(f"🔍 Incoming request: {request.method} {request.url}")
        logger.debug(f"🔍 Headers: {dict(request.headers)}")
        logger.debug(f"🔍 Client: {request.client}")
    
    response = await call_next(request)
    
    if log_level == "DEBUG":
        logger.debug(f"🔍 Response status: {response.status_code}")
    
    return response

@app.on_event("startup")
async def startup():
    """Initialize server components"""
    global client, model
    
    logger.info("🚀 MCP Memory Server starting up...")
    logger.info(f"🌐 Server will be available at: http://{SERVER_HOST}:{SERVER_PORT}")
    logger.info(f"🔗 Connecting to Qdrant at: {QDRANT_HOST}:{QDRANT_PORT}")
    
    try:
        # Initialize Qdrant with retry logic
        max_retries = 5
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to Qdrant... (attempt {attempt + 1}/{max_retries})")
                client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, check_compatibility=False)
                # Test connection
                client.get_collections()
                logger.info("✅ Connected to Qdrant successfully")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Qdrant connection failed (attempt {attempt + 1}): {e}")
                import time
                time.sleep(2)
        
        # Initialize embedding model
        logger.info("Loading embedding model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        logger.info("✅ MCP Memory Server startup complete")
        logger.info("📡 Waiting for Claude to connect...")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

# Main JSON-RPC endpoint - handles ALL MCP requests
@app.post("/")
async def handle_jsonrpc(request: Request):
    """Handle all JSON-RPC requests at the root endpoint"""
    try:
        # Log ALL incoming requests for debugging
        raw_body = await request.body()
        if log_level == "DEBUG":
            logger.debug(f"Raw request body: {raw_body}")
            logger.debug(f"Request headers: {dict(request.headers)}")
        
        body = await request.json()
        logger.info(f"Received JSON-RPC request: {body.get('method', 'unknown')}")
        
        # Validate JSON-RPC structure
        if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
            return create_jsonrpc_response(
                body.get("id"),
                error=create_jsonrpc_error(-32600, "Invalid Request")
            )
        
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        # Route to appropriate handler
        if method == "initialize":
            result = await handle_initialize(params)
        elif method == "tools/list":
            result = await handle_tools_list(params)
        elif method == "tools/call":
            result = await handle_tools_call(params)
        elif method == "notifications/initialized":
            # Claude sends this after successful initialization
            result = {}
        else:
            logger.warning(f"Unknown method: {method}")
            return create_jsonrpc_response(
                request_id,
                error=create_jsonrpc_error(-32601, f"Method not found: {method}")
            )
        
        return create_jsonrpc_response(request_id, result)
        
    except json.JSONDecodeError:
        return create_jsonrpc_response(
            None,
            error=create_jsonrpc_error(-32700, "Parse error")
        )
    except Exception as e:
        logger.error(f"JSON-RPC handler error: {e}")
        return create_jsonrpc_response(
            body.get("id") if 'body' in locals() else None,
            error=create_jsonrpc_error(-32603, f"Internal error: {str(e)}")
        )

# MCP Method Handlers

async def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP initialize request"""
    logger.info("Handling initialize request")
    
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "qdrant-memory-server",
            "version": "1.0.0"
        }
    }

async def handle_tools_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/list request"""
    logger.info("Handling tools/list request")
    
    tools = [
        {
            "name": "get_summary",
            "description": "Get agent's summary information",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Agent identifier"}
                },
                "required": ["agent_id"]
            }
        },
        {
            "name": "update_summary",
            "description": "Update agent's summary",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Agent identifier"},
                    "summary": {"type": "string", "description": "Summary content"},
                    "tags": {"type": "array", "items": {"type": "string"}, "default": []}
                },
                "required": ["agent_id", "summary"]
            }
        },
        {
            "name": "add_memory",
            "description": "Add a new memory",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Agent identifier"},
                    "content": {"type": "string", "description": "Memory content"},
                    "tags": {"type": "array", "items": {"type": "string"}, "default": []}
                },
                "required": ["agent_id", "content"]
            }
        },
        {
            "name": "search_memories",
            "description": "Search memories by content similarity",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Agent identifier"},
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "default": 10, "description": "Max results"}
                },
                "required": ["agent_id", "query"]
            }
        }
    ]
    
    return {"tools": tools}

async def handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/call request"""
    logger.info(f"Handling tools/call request: {params.get('name', 'unknown')}")
    
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    try:
        if tool_name == "get_summary":
            result = await tool_get_summary(arguments)
        elif tool_name == "update_summary":
            result = await tool_update_summary(arguments)
        elif tool_name == "add_memory":
            result = await tool_add_memory(arguments)
        elif tool_name == "search_memories":
            result = await tool_search_memories(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2, default=str)
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Tool call error: {e}")
        raise

# Tool Implementations

async def tool_get_summary(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get agent summary"""
    agent_id = args.get("agent_id", "default")
    collection_name = await ensure_collection(agent_id)
    
    filter_condition = models.Filter(
        must=[models.FieldCondition(key="memory_type", match=models.MatchValue(value="summary"))]
    )
    
    results = client.scroll(
        collection_name=collection_name,
        scroll_filter=filter_condition,
        limit=1,
        with_payload=True
    )[0]
    
    if results:
        payload = results[0].payload
        return {
            "agent_id": agent_id,
            "summary": payload.get("content"),
            "timestamp": payload.get("timestamp"),
            "tags": payload.get("tags", [])
        }
    else:
        return {
            "agent_id": agent_id,
            "summary": None,
            "message": "No summary found"
        }

async def tool_update_summary(args: Dict[str, Any]) -> Dict[str, Any]:
    """Update agent summary"""
    agent_id = args.get("agent_id", "default")
    summary = args["summary"]
    tags = args.get("tags", [])
    
    collection_name = await ensure_collection(agent_id)
    timestamp = datetime.now()
    
    # Generate embedding
    summary_vector = model.encode(summary).tolist()
    
    point = PointStruct(
        id=1,  # Reserved ID for summary
        vector=summary_vector,
        payload={
            "memory_type": "summary",
            "content": summary,
            "timestamp": timestamp.isoformat(),
            "tags": tags,
            "metadata": {
                "last_updated": timestamp.isoformat(),
                "agent_id": agent_id
            }
        }
    )
    
    client.upsert(collection_name=collection_name, points=[point])
    
    return {
        "success": True,
        "agent_id": agent_id,
        "summary": summary,
        "timestamp": timestamp.isoformat(),
        "tags": tags
    }

async def tool_add_memory(args: Dict[str, Any]) -> Dict[str, Any]:
    """Add new memory"""
    agent_id = args.get("agent_id", "default")
    content = args["content"]
    tags = args.get("tags", [])
    
    collection_name = await ensure_collection(agent_id)
    memory_id = str(uuid.uuid4())
    timestamp = datetime.now()
    
    # Generate embedding
    content_vector = model.encode(content).tolist()
    
    point = PointStruct(
        id=memory_id,
        vector=content_vector,
        payload={
            "memory_type": "long_term",
            "content": content,
            "timestamp": timestamp.isoformat(),
            "tags": tags,
            "metadata": {
                "created_at": timestamp.isoformat(),
                "agent_id": agent_id
            }
        }
    )
    
    client.upsert(collection_name=collection_name, points=[point])
    
    return {
        "success": True,
        "agent_id": agent_id,
        "memory_id": memory_id,
        "content": content,
        "timestamp": timestamp.isoformat(),
        "tags": tags
    }

async def tool_search_memories(args: Dict[str, Any]) -> Dict[str, Any]:
    """Search memories"""
    agent_id = args.get("agent_id", "default")
    query = args["query"]
    limit = args.get("limit", 10)
    
    collection_name = await ensure_collection(agent_id)
    
    # Generate query vector
    query_vector = model.encode(query).tolist()
    
    # Search with exclusion of metadata
    filter_condition = models.Filter(
        must_not=[models.FieldCondition(key="type", match=models.MatchValue(value="agent_metadata"))]
    )
    
    results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        query_filter=filter_condition,
        limit=limit,
        with_payload=True
    ).points
    
    memories = []
    for result in results:
        payload = result.payload
        memories.append({
            "memory_id": result.id,
            "content": payload.get("content"),
            "memory_type": payload.get("memory_type"),
            "timestamp": payload.get("timestamp"),
            "tags": payload.get("tags", []),
            "score": result.score
        })
    
    return {
        "agent_id": agent_id,
        "query": query,
        "results": memories,
        "total_found": len(memories)
    }

# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Check Qdrant connection
        client.get_collections()
        return {
            "status": "healthy", 
            "timestamp": datetime.now().isoformat(),
            "qdrant_host": QDRANT_HOST,
            "qdrant_port": QDRANT_PORT
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Catch-all route for debugging
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def catch_all_debug(path: str, request: Request):
    """Catch any requests Claude might be making to unexpected endpoints"""
    body = await request.body()
    if log_level == "DEBUG":
        logger.debug(f"🔍 CATCH-ALL: {request.method} /{path}")
        logger.debug(f"🔍 Body: {body}")
    
    # If it's a JSON-RPC request, try to handle it
    if request.method == "POST" and body:
        try:
            json_body = json.loads(body)
            if json_body.get("jsonrpc") == "2.0":
                logger.info(f"🔍 Found JSON-RPC request at /{path}: {json_body.get('method', 'unknown')}")
                # Redirect to main handler
                return await handle_jsonrpc(request)
        except:
            pass
    
    return {"message": f"Caught {request.method} request to /{path}", "body": body.decode() if body else None}

if __name__ == "__main__":
    # Enable debug mode with more verbose logging
    uvicorn.run(
        app, 
        host=SERVER_HOST, 
        port=SERVER_PORT, 
        log_level=log_level.lower(),
        access_log=True if log_level == "DEBUG" else False
    )
