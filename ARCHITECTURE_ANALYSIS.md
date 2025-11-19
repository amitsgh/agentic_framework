# Architecture & Flow Analysis

## Architecture Layers

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
│  Redis, Ollama, HuggingFace, etc.                           │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Analysis

### 1. Document Upload Flow
```
1. API Route (documents.py)
   ├─> Validates file
   ├─> Computes file hash
   └─> Saves file temporarily

2. DocumentController.upload()
   ├─> Checks cache via StateManager
   ├─> Calls Pipeline.process()
   │   ├─> Extractor.extract()
   │   ├─> Chunker.chunk()
   │   └─> StateManager.save_chunked_docs()
   └─> DocumentRepository.add_documents()
       └─> BaseDB.add_documents()
```

### 2. Chat with RAG Flow
```
1. API Route (chat.py)
   ├─> Gets LLM instance
   ├─> Gets embeddings
   └─> Creates DocumentRepository from DB

2. ChatController.chat_stream()
   ├─> Builds messages with RAG context
   │   └─> DocumentRepository.similarity_search()
   │       └─> BaseDB.similarity_search()
   └─> LLM.model_stream_response()
```

## Issues Found

### ✅ FIXED: Database Lifecycle Management

**Previous Issue:**
- `_create_document_controller` was using `next(db)` which didn't properly manage lifecycle
- Generator cleanup wasn't guaranteed

**Fix Applied:**
- Changed `_create_document_controller` to return a factory tuple
- Database lifecycle now managed in route handlers using `for db in get_db_sync():`
- Ensures proper connection cleanup via generator's `finally` block

**Current Status:**
```python
# ✅ FIXED: Proper lifecycle management
for db_instance in db:
    document_repository = DocumentRepository(db_instance)
    controller = DocumentControllerClass(pipeline, state_manager, document_repository)
    # ... use controller
    break  # Ensures cleanup
```

**Status:** ✅ Fixed - lifecycle is now properly managed in both endpoints

### ⚠️ MINOR: Logger Import Inconsistency

**Issue:** Multiple files use `from app.logger` instead of `from app.utils.logger`
- `app/dependency.py` line 19
- `app/main.py` line 21
- Multiple service files

**Impact:** Low - might be an alias or different file, but should be consistent

### ⚠️ MINOR: Exception Handling

**Issue:** Several places catch generic `Exception` instead of specific exceptions
- `app/repositories/state_repository.py` (lines 33, 52, 63)
- `app/manager/state_manager.py` (lines 75, 88, 104)
- `app/controllers/chat_controller.py` (line 67)

**Impact:** Low - acceptable for logging/warning scenarios, but could be more specific

## Architecture Strengths

### ✅ Good Separation of Concerns
- Clear layer boundaries
- Controllers don't know about DB implementation
- Repositories abstract database operations
- Services handle implementation details

### ✅ Repository Pattern Properly Implemented
- `DocumentRepository` wraps all DB operations
- `StateRepository` handles cache operations
- Controllers use repositories, not services directly

### ✅ Dependency Injection
- FastAPI's `Depends` used correctly
- Services injected at appropriate levels
- Singleton pattern for expensive resources (embeddings, extractor, cache)

### ✅ Error Handling
- Custom exceptions defined
- Proper error propagation
- HTTP status codes mapped correctly

## Recommendations

### 1. Fix Database Lifecycle (HIGH PRIORITY)
```python
# Option A: Use context manager in route
@router.post("/upload")
async def upload_document(...):
    for db in get_db_sync():
        document_repository = DocumentRepository(db)
        controller = DocumentController(..., document_repository)
        # ... rest of logic
        break  # Exit after first iteration

# Option B: Create repository factory
def _create_document_repository(db: BaseDB) -> DocumentRepository:
    return DocumentRepository(db)

# Then in route:
for db in get_db_sync():
    document_repository = _create_document_repository(db)
    # ...
```

### 2. Standardize Logger Imports (MEDIUM PRIORITY)
- Check if `app/logger.py` exists or is an alias
- If not, update all imports to `app.utils.logger`

### 3. Improve Exception Specificity (LOW PRIORITY)
- Where catching generic Exception, consider more specific exceptions
- Or document why generic catch is acceptable

## Overall Assessment

**Architecture Quality:** ⭐⭐⭐⭐ (4/5)
- Well-structured layers
- Good separation of concerns
- Repository pattern properly implemented
- **Needs fix for database lifecycle management**

**Code Quality:** ⭐⭐⭐⭐ (4/5)
- Clean, readable code
- Good error handling
- Proper logging
- Minor inconsistencies in imports

**Main Concern:** Database connection lifecycle management in document upload endpoint needs to be fixed to prevent connection leaks.

