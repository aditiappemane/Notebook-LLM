# Notebook LLM - Complete Multimodal Research Assistant

## Overview
A production-ready multimodal RAG system that ingests, processes, and reasons over complex documents (text, images, tables, charts, code) using Gemini API and advanced document processing.

## Features
- Ingest 10+ file formats (PDF, DOCX, HTML, CSV, Excel, PowerPoint, Jupyter, images)
- Multimodal understanding (text, images, tables, charts, code)
- Document hierarchy and relationship mapping
- Advanced queries and smart summarization
- User authentication, document management, query history, collaboration
- Custom embeddings and vector search
- Export and integration options

## Tech Stack
- **Backend:** FastAPI (Python)
- **Frontend:** Streamlit (Python)
- **AI:** Gemini API (multimodal)
- **Vector DB:** (to be selected)

## Setup
1. Clone the repo
2. Install Python 3.10+
3. `pip install -r requirements.txt`
4. Run backend: `uvicorn backend.main:app --reload`
5. Run frontend: `streamlit run frontend/app.py`

## Directory Structure
- `backend/` - FastAPI backend, document processing, AI integration
- `frontend/` - Streamlit frontend
- `data/` - Uploaded and processed documents 