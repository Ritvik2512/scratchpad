# MCP Memory Server for Claude

A semantic memory system built specifically for Claude using the Model Context Protocol (MCP).  
This project enables persistent, searchable memory for Claude Desktop by integrating vector embeddings with a custom MCP server.

---

## Features

- MCP-compatible memory server for Claude (JSON-RPC based)
- Semantic memory using transformer embeddings
- Vector database integration with Qdrant
- Agent-based memory isolation
- FastAPI backend for handling MCP requests
- HTTP ↔ MCP bridge for Claude Desktop integration
- Dockerized setup for easy deployment
- Includes infrastructure setup (e.g., load balancer support)

---

## Tech Stack

- **Backend:** Python, FastAPI  
- **ML / Embeddings:** Sentence Transformers  
- **Vector DB:** Qdrant  
- **Protocol:** Model Context Protocol (MCP)  
- **Infrastructure:** Docker, Docker Compose, AWS (ALB setup)

---

## How It Works

1. Claude sends requests via MCP (JSON-RPC)  
2. The memory server processes and stores data as vector embeddings  
3. Data is stored in Qdrant for efficient similarity search  
4. Relevant memories are retrieved and returned to Claude  

---

## Project Structure
mcp-memory-server/
│
├── app/ # Core MCP server + bridge
├── scripts/ # Setup and deployment scripts
├── docker/ # Docker configuration
├── config/ # Claude MCP config
│
├── .env.example # Environment variables template
├── requirements.txt
├── README.md
├── .gitignore

---

## Environment Setup

```bash
cp .env.example .env
```

# Modify values if needed

---

## Running the Project

### 1. Start Qdrant (Vector Database)

Run Qdrant using Docker:
```bash
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### 2. Install Dependencies

Install required Python packages:
```bash
pip install -r requirements.txt
```
### 3. Run MCP Memory Server

Start the MCP memory server:
```bash
python memory.py --agent-id your-agent --host localhost --port 6333
```
### 4. (Optional) Using Docker Compose

If using Docker setup:
```bash
docker-compose up --build
```
---

