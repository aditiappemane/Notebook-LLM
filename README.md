# Notebook LLM

A production-ready multimodal RAG (Retrieval-Augmented Generation) system inspired by NotebookLM, with advanced capabilities for research, technical, and collaborative workflows.

## Features
- **Multimodal support:** Text, images, tables, charts, code, diagrams
- **10+ file formats:** PDF, DOCX, HTML, CSV, Excel, PowerPoint, Jupyter, Markdown, LaTeX, PNG, JPG, TXT
- **Document structure extraction:** Sections, hierarchy, metadata
- **Hybrid search:** Vector (ChromaDB) + keyword
- **Advanced query:** Query decomposition, Gemini integration (text & images)
- **Summarization & relationship mapping**
- **Streamlit frontend**
- **FastAPI backend**

## Architecture
```mermaid
graph TD
  A[User/Researcher] -->|Upload/Query| B[Streamlit Frontend]
  B -->|API| C[FastAPI Backend]
  C -->|Process| D[Document Processor (unstructured, PIL, etc.)]
  C -->|Store| E[ChromaDB (Vectors)]
  C -->|Store| F[Document Store (in-memory)]
  C -->|Query| G[Gemini API (Text+Vision)]
  D -->|Extract| F
  E -->|Retrieve| C
  F -->|Context| C
```

## Setup Instructions

### Prerequisites
- Python 3.9+
- NodeJS (optional, for React frontend)
- [Google Gemini API key](https://ai.google.dev/)

### Installation
```bash
git clone <your-repo-url>
cd Notebook\ LLM
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file in `backend/` with:
```
GEMINI_API_KEY=your_gemini_api_key
```

### Running the Backend
```bash
cd backend
uvicorn main:app --reload
```

### Running the Frontend
```bash
cd frontend
streamlit run app.py
```

## Usage
1. **Upload documents** (PDF, DOCX, PNG, etc.) via the Streamlit UI.
2. **Ask questions** about your documents (text or images).
3. **View document structure** and extracted sections.
4. **Summarize** documents or map relationships.
5. **Export** answers or structure (optional).

## API Endpoints (FastAPI)
- `POST /upload` — Upload a document
- `POST /query` — Ask a question about a document
- `GET /structure` — Get document structure/sections
- `POST /summarize` — Summarize a document
- `GET /relationships` — Extract entity/concept relationships
- `POST /export/answer` — Export answer (JSON/PDF)
- `GET /export/structure` — Export structure (JSON/PDF)

## Contribution Guidelines
- Fork the repo, create a feature branch, submit a PR
- Write clear commit messages
- Add/maintain docstrings and comments
- Run tests before submitting

## License
[Add your license here]

## Contact
[Your name/contact info] 