# Technical Documentation: Notebook LLM

## 1. System Architecture & Design Decisions
- **Multimodal RAG**: Designed for research and technical workflows, supporting text, images, tables, code, and diagrams.
- **Backend-Frontend split**: FastAPI for robust, async APIs; Streamlit for rapid prototyping and user interaction.
- **Hybrid retrieval**: Combines vector search (ChromaDB) with keyword filtering for high recall and precision.
- **Gemini API**: Chosen for advanced multimodal (text+vision) capabilities.

## 2. Backend (FastAPI) Structure
- `main.py`: API endpoints for upload, query, structure, summarize, relationships, export.
- `processing/document_processor.py`: Handles file parsing, chunking, metadata extraction.
- `processing/gemini_client.py`: Handles Gemini API calls (text, images, embeddings).
- `db/chroma_client.py`: Manages ChromaDB vector storage and retrieval.
- In-memory `DOCUMENT_STORE` for fast prototyping (can be replaced with persistent DB).

## 3. Document Processing Pipeline
- On upload, files are saved and processed by `process_document`:
  - Uses `unstructured` for parsing (PDF, DOCX, HTML, etc.)
  - Extracts text, images, tables, code blocks
  - Chunks text for vector storage
  - Extracts document structure (sections, hierarchy)
  - For images: skips text extraction, stores path/metadata
- Chunks and metadata are stored in ChromaDB for retrieval.

## 4. ChromaDB Vector Search & Hybrid Retrieval
- Chunks are embedded (via Gemini) and stored in ChromaDB.
- On query, ChromaDB returns top-N relevant chunks (vector search).
- Optionally, keyword search is used for additional recall.
- Retrieved context is sent to Gemini for answer synthesis.

## 5. Gemini API Integration
- `gemini_client.py` provides `query_gemini` (text+images) and embedding endpoints.
- For text/image queries, context and images are sent to Gemini in a single call.
- For image-only docs, the image and question are sent directly (no vector search).

## 6. Frontend (Streamlit) Flow
- Users upload files, ask questions, view structure, summarize, and map relationships.
- Communicates with FastAPI backend via HTTP endpoints.
- Displays answers, document structure, and (optionally) relationship graphs.

## 7. Extensibility
- **Adding file formats**: Extend `SUPPORTED_FORMATS` and add parsing logic in `document_processor.py`.
- **Adding models**: Swap out Gemini for other APIs in `gemini_client.py`.
- **Persistent storage**: Replace in-memory `DOCUMENT_STORE` with a database.
- **Frontend**: Can be replaced with React or other frameworks.

## 8. Error Handling & Limitations
- Graceful error messages for unsupported formats, failed parsing, or API errors.
- Large files may require chunking/tuning for performance.
- In-memory store is not persistent—restart loses state.
- Gemini API rate limits and costs apply.

## 9. Security & Deployment Notes
- Add authentication (JWT, OAuth) for production.
- Use HTTPS and secure API keys.
- Deploy with Uvicorn/Gunicorn behind a reverse proxy (e.g., Nginx).
- For scale, use persistent DB and distributed ChromaDB. 