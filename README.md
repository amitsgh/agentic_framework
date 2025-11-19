# Agentic Framework - LLM Application with RAG Capabilities

## 📋 Project Overview

This is a production-ready **Agentic Framework** built with FastAPI that provides a complete RAG (Retrieval-Augmented Generation) system for document processing and intelligent chat interactions. The framework implements a clean, layered architecture with factory patterns, dependency injection, and comprehensive state management.

### Key Features

- **Document Processing Pipeline**: Extract, chunk, embed, and store documents in a vector database
- **RAG-Enabled Chat**: Intelligent chat interface with context retrieval from uploaded documents
- **State Management**: Comprehensive caching and state tracking for document processing stages
- **Modular Architecture**: Factory pattern-based service layer for easy extensibility
- **Multiple Extractor Support**: Docling-based document extraction with support for multiple formats
- **Vector Search**: Semantic similarity search using embeddings
- **Streaming Responses**: Real-time streaming chat responses
- **Production-Ready**: Proper error handling, logging, and lifecycle management

---

## 🏗️ Architecture Overview

The framework follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (Routes)                        │
│  app/api/v1/chat.py, app/api/v1/documents.py               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Controller Layer                            │
│  ChatController, DocumentController                         │
│  - Orchestrates business logic                              │
│  - Coordinates between repositories, pipelines, managers     │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Repositories │ │  Pipeline    │ │   Manager    │
│              │ │              │ │              │
│ DocumentRepo │ │ DocumentPipe │ │ StateManager│
│ StateRepo    │ │              │ │              │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       │                │                │
       ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                  Services Layer                              │
│  BaseDB, BaseLLM, BaseEmbeddings, BaseExtractor, etc.      │
│  - Implementation details                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Infrastructure Layer                            │
│  Redis, Ollama, HuggingFace, etc.                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 System Flow

### 1. Document Upload & Processing Flow

```
1. API Route (POST /api/v1/upload)
   ├─> Validates file (type, size, extension)
   ├─> Computes SHA256 file hash
   └─> Saves file temporarily

2. DocumentController.upload()
   ├─> Checks cache via StateManager
   │   └─> If already processed (STORED stage), returns cached chunks
   │
   ├─> Calls Pipeline.process()
   │   ├─> Stage 1: Extract (BaseExtractor.extract())
   │   │   └─> Converts PDF/DOCX to structured documents
   │   │
   │   ├─> Stage 2: Chunk (BaseChunker.chunk())
   │   │   └─> Splits documents into semantic chunks
   │   │   └─> Caches chunked documents in Redis
   │   │
   │   └─> Updates ProcessingState (UPLOADED → EXTRACTED → CHUNKED)
   │
   └─> DocumentRepository.add_documents()
       ├─> Generates embeddings for each chunk (BaseEmbeddings)
       └─> Stores in vector database (Redis with embeddings)
       └─> Updates ProcessingState to STORED
```

**Processing Stages:**
- `UPLOADED`: File received and validated
- `EXTRACTED`: Text extracted from document
- `CHUNKED`: Documents split into chunks
- `EMBEDDED`: Chunks embedded (implicit during storage)
- `STORED`: Chunks stored in vector database
- `FAILED`: Processing failed with error message

### 2. Chat with RAG Flow

```
1. API Route (GET /api/v1/chat/chat)
   ├─> Gets LLM instance (Ollama)
   ├─> Gets embeddings instance (HuggingFace)
   └─> Creates DocumentRepository from DB

2. ChatController.chat_stream()
   ├─> Builds messages with RAG context
   │   ├─> DocumentRepository.similarity_search()
   │   │   ├─> Embeds user query
   │   │   ├─> Searches vector DB for top-k similar chunks
   │   │   └─> Returns relevant document chunks
   │   │
   │   └─> Constructs prompt with context:
   │       "Answer based on context: [retrieved chunks]
   │        Question: [user query]"
   │
   └─> LLM.model_stream_response()
       └─> Streams response token by token
```

---

## 🧩 Key Components

### 1. **Controllers** (`app/controllers/`)

**DocumentController**
- Orchestrates document upload and processing
- Manages pipeline execution
- Handles state transitions
- Coordinates between pipeline, state manager, and repository

**ChatController**
- Orchestrates chat interactions
- Builds RAG-enhanced prompts
- Manages streaming responses
- Handles optional RAG context retrieval

### 2. **Pipeline** (`app/pipeline/`)

**DocumentPipeline**
- Orchestrates the document processing pipeline
- Manages stage transitions (UPLOADED → EXTRACTED → CHUNKED)
- Implements caching strategy (checks cache before processing)
- Handles errors and state updates

### 3. **Repositories** (`app/repositories/`)

**DocumentRepository**
- Abstracts vector database operations
- Handles document storage with embeddings
- Implements similarity search
- Manages document deletion

**StateRepository**
- Manages processing state in cache
- Handles state persistence and retrieval
- Tracks processing stages and errors

### 4. **Managers** (`app/manager/`)

**StateManager**
- High-level state management
- Caches chunked documents
- Manages processing state lifecycle
- Handles cache invalidation

### 5. **Services** (`app/services/`)

All services follow a **Factory Pattern** with base classes:

- **Extractor** (`extractor/`): Document extraction (Docling)
- **Chunker** (`chunker/`): Document chunking (Hybrid chunker)
- **Embeddings** (`embedder/`): Text embeddings (HuggingFace)
- **LLM** (`llm/`): Language model (Ollama)
- **Database** (`db/`): Vector database (Redis)
- **Cache** (`cache/`): Caching layer (Redis)

Each service has:
- `base.py`: Abstract base class defining interface
- `factory.py`: Factory function with registry pattern
- Implementation files (e.g., `redis_db.py`, `ollama_llm.py`)

### 6. **Dependency Injection** (`app/dependency.py`)

- Singleton pattern for expensive resources (embeddings, extractor, cache)
- Lifecycle management for database connections
- Factory functions for service instantiation
- Proper cleanup and resource management

---

## 🛠️ Technology Stack

### Core Framework
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **Python 3.10+**: Modern Python features

### LLM & AI
- **Ollama**: Local LLM inference (supports Llama2, etc.)
- **HuggingFace Transformers**: Embedding models (sentence-transformers)
- **Docling**: Advanced document extraction and parsing

### Data Storage
- **Redis**: Vector database and caching layer
- **Sentence Transformers**: Embedding generation

### Document Processing
- **Docling**: Multi-format document extraction (PDF, DOCX, etc.)
- **Hybrid Chunking**: Semantic and structural chunking

### Development Tools
- **Colorlog**: Colored logging
- **Pydantic Settings**: Environment-based configuration

---

## 📁 Project Structure

```
agentic_framework/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── chat.py              # Chat API routes
│   │       └── documents.py         # Document API routes
│   ├── controllers/
│   │   ├── chat_controller.py       # Chat orchestration
│   │   └── document_controller.py   # Document orchestration
│   ├── pipeline/
│   │   └── pipeline.py              # Document processing pipeline
│   ├── repositories/
│   │   ├── document_repository.py   # Document DB operations
│   │   └── state_repository.py      # State cache operations
│   ├── manager/
│   │   └── state_manager.py         # State management
│   ├── services/
│   │   ├── extractor/               # Document extraction services
│   │   ├── chunker/                 # Chunking services
│   │   ├── embedder/                # Embedding services
│   │   ├── llm/                     # LLM services
│   │   ├── db/                      # Database services
│   │   └── cache/                   # Caching services
│   ├── models/
│   │   ├── document_model.py        # Document data models
│   │   └── processing_state.py      # Processing state models
│   ├── config.py                    # Configuration management
│   ├── dependency.py                # Dependency injection
│   ├── exceptions.py               # Custom exceptions
│   ├── main.py                     # FastAPI application
│   └── router.py                   # Route registration
├── ui/                              # Streamlit UI (optional)
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

---

## 🚀 Setup & Installation

### Prerequisites

- Python 3.10+
- Redis server running (for vector DB and caching)
- Ollama installed and running (for LLM inference)

### Installation Steps

1. **Clone the repository**
   ```bash
   cd agentic_framework
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file (optional, defaults are provided):
   ```env
   # LLM Configuration
   LLM_TYPE=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama2

   # Database Configuration
   DATABASE_TYPE=redis
   REDIS_URL=redis://localhost:6379
   COLLECTION_NAME=default

   # Embeddings Configuration
   EMBEDDINGS_TYPE=huggingface
   MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

   # Extractor Configuration
   EXTRACTOR_TYPE=docling
   CHUNKER_TYPE=docling-hybrid

   # RAG Configuration
   RAG_ENABLED=true
   RAG_TOP_K=5
   RAG_MIN_SCORE=0.7

   # Cache Configuration
   ENABLE_CACHING=true
   CACHE_TYPE=redis-cache
   ```

4. **Start Redis**
   ```bash
   redis-server
   ```

5. **Start Ollama** (if not already running)
   ```bash
   ollama serve
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

---

## 📡 API Endpoints

### Document Endpoints

#### `POST /api/v1/upload`
Upload and process a document.

**Parameters:**
- `file`: File upload (PDF, DOCX, TXT, MD)
- `forced_reprocess`: Boolean (optional, default: false)

**Response:**
```json
{
  "status": "success",
  "file_name": "document.pdf",
  "message": "Document processed and stored successfully. Created 15 chunks. (Hash: abc123...)"
}
```

#### `DELETE /api/v1/delete-all`
Delete all documents from the database.

**Response:**
```json
{
  "status": "success",
  "file_name": "",
  "message": "Successfully deleted 50 documents from database."
}
```

### Chat Endpoints

#### `GET /api/v1/chat/chat`
Chat with the LLM (with optional RAG).

**Parameters:**
- `query`: User query (required)
- `model_name`: LLM model name (optional, default: "ollama/llama2")
- `use_rag`: Enable RAG (optional, overrides config)

**Response:**
Streaming text response (text/plain)

### Health Check

#### `GET /health`
Application health check.

**Response:**
```json
{
  "message": "LLM Application",
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## 🎯 Design Patterns & Best Practices

### 1. **Factory Pattern**
All services use factory functions with registry patterns:
```python
# Example: Database Factory
DATABASE_REGISTRY = {
    "redis": RedisDB,
    # Easy to add more: "pinecone": PineconeDB
}

def get_db_instance() -> BaseDB:
    db_class = DATABASE_REGISTRY.get(config.DATABASE_TYPE)
    return db_class()
```

### 2. **Repository Pattern**
Data access is abstracted through repositories:
- Controllers use repositories, not services directly
- Easy to swap database implementations
- Clear separation of concerns

### 3. **Dependency Injection**
FastAPI's `Depends()` used throughout:
- Singleton pattern for expensive resources
- Proper lifecycle management
- Testable components

### 4. **State Management**
Comprehensive state tracking:
- Processing stages tracked in cache
- Chunked documents cached for performance
- Error states preserved for debugging

### 5. **Error Handling**
Custom exception hierarchy:
- `FrameworkException`: Base exception
- `DocumentProcessingError`: Document processing failures
- `DatabaseError`: Database operation failures
- `LLMError`: LLM operation failures
- `ValidationError`: Input validation failures

### 6. **Logging**
Structured logging throughout:
- Color-coded log levels
- Contextual information
- Error stack traces

---

## 🔍 Key Features Explained

### 1. **Intelligent Caching**
- File hash-based deduplication
- Chunked documents cached to avoid re-processing
- Processing state persisted across requests
- Configurable TTL for cache entries

### 2. **Flexible Service Layer**
- Easy to swap implementations (e.g., switch from Ollama to OpenAI)
- Factory pattern allows runtime configuration
- Base classes ensure interface consistency

### 3. **RAG Implementation**
- Semantic search using embeddings
- Top-k retrieval with similarity scoring
- Context injection into LLM prompts
- Configurable RAG parameters

### 4. **Streaming Responses**
- Real-time token streaming for chat
- Better user experience
- Lower latency

### 5. **Production-Ready Features**
- Comprehensive error handling
- Health check endpoint
- CORS configuration
- Request validation
- Lifecycle management

---

## 📊 Processing State Flow

```
UPLOADED
   │
   ▼
EXTRACTED (if not cached)
   │
   ▼
CHUNKED (if not cached)
   │
   ▼
STORED (after embedding & DB insertion)
   │
   └─> FAILED (if any error occurs)
```

Each stage is cached and can be resumed from any point.

---

## 🔧 Configuration Options

Key configuration options (see `app/config.py` for full list):

- **LLM_TYPE**: LLM provider (default: "ollama")
- **DATABASE_TYPE**: Vector database (default: "redis")
- **EXTRACTOR_TYPE**: Document extractor (default: "docling")
- **CHUNKER_TYPE**: Chunking strategy (default: "docling-hybrid")
- **EMBEDDINGS_TYPE**: Embedding provider (default: "huggingface")
- **RAG_ENABLED**: Enable/disable RAG (default: true)
- **RAG_TOP_K**: Number of chunks to retrieve (default: 5)
- **CHUNK_SIZE**: Chunk size in characters (default: 1000)
- **CHUNK_OVERLAP**: Overlap between chunks (default: 200)
- **ENABLE_CACHING**: Enable caching (default: true)

---

## 🧪 Testing the System

### 1. Upload a Document
```bash
curl -X POST "http://localhost:8000/api/v1/upload?forced_reprocess=false" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### 2. Chat with RAG
```bash
curl "http://localhost:8000/api/v1/chat/chat?query=What%20is%20the%20main%20topic%20of%20the%20document?&use_rag=true"
```

### 3. Chat without RAG
```bash
curl "http://localhost:8000/api/v1/chat/chat?query=Hello%20world&use_rag=false"
```

---

## 📝 Architecture Strengths

✅ **Clean Separation of Concerns**: Each layer has a clear responsibility  
✅ **Extensibility**: Easy to add new extractors, chunkers, or databases  
✅ **Testability**: Dependency injection makes components easily testable  
✅ **Performance**: Caching reduces redundant processing  
✅ **Maintainability**: Clear structure and consistent patterns  
✅ **Production-Ready**: Proper error handling, logging, and lifecycle management  

---

## 🚧 Future Enhancements

Potential improvements:
- [ ] Add more LLM providers (OpenAI, Anthropic, etc.)
- [ ] Support for more document formats
- [ ] Advanced chunking strategies
- [ ] Multi-tenant support
- [ ] Authentication and authorization
- [ ] Rate limiting
- [ ] Metrics and monitoring
- [ ] Batch document processing
- [ ] Document versioning

---

## 📄 License

This project is part of a personal/portfolio project demonstrating advanced Python architecture patterns and LLM application development.

---

## 👤 Author

Developed as a demonstration of:
- Clean architecture principles
- Factory and repository patterns
- RAG system implementation
- Production-ready FastAPI applications
- LLM integration best practices

---

**Version**: 1.0.0  
**Last Updated**: 2024
