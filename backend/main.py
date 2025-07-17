from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
import uuid
from backend.processing.document_processor import process_document
from backend.processing.gemini_client import query_gemini, decompose_query
from backend.db.chroma_client import add_chunks_to_chroma, query_chroma
from typing import Dict
import base64
import json
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

app = FastAPI()

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

DOCUMENT_STORE: Dict[str, dict] = {}

@app.get("/")
def read_root():
    return {"message": "Notebook LLM backend is running."}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    print("[UPLOAD] Received upload request")
    file_location = os.path.join(DATA_DIR, file.filename)
    print(f"[UPLOAD] Saving file to {file_location}")
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    print("[UPLOAD] File saved, starting document processing...")
    processing_summary = process_document(file_location)
    print("[UPLOAD] Document processing complete")
    doc_id = str(uuid.uuid4())
    DOCUMENT_STORE[doc_id] = {
        "filename": file.filename,
        "file_path": file_location,
        "processing": processing_summary
    }
    print("[UPLOAD] Storing chunks in ChromaDB...")
    chunks = processing_summary.get("chunks", [])
    chunk_texts = [c["text"] for c in chunks]
    metadatas = [{"document_id": doc_id, "filename": file.filename, "type": c["type"]} for c in chunks]
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    if chunk_texts:
        add_chunks_to_chroma(chunk_texts, metadatas, ids)
    print("[UPLOAD] ChromaDB storage complete, returning response.")
    return JSONResponse({
        "filename": file.filename,
        "status": "uploaded",
        "processing": processing_summary,
        "document_id": doc_id
    })

@app.post("/query")
async def query_document(document_id: str, question: str):
    doc = DOCUMENT_STORE.get(document_id)
    if not doc:
        print("[QUERY] Document not found for ID:", document_id)
        raise HTTPException(status_code=404, detail="Document not found")
    processing = doc["processing"]
    # If this is an image-only document, send the image directly to Gemini
    if processing.get("status") == "image_uploaded":
        print("[QUERY] Image-only document detected. Sending image to Gemini.")
        image_paths = processing.get("image_paths", [])
        images_b64 = []
        for img_path in image_paths:
            try:
                with open(img_path, "rb") as img_file:
                    img_bytes = img_file.read()
                    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                    images_b64.append(img_b64)
            except Exception as e:
                print(f"[QUERY] Failed to read image {img_path}: {e}")
                continue
        print("[QUERY] Calling Gemini for image query...")
        gemini_response = query_gemini(question, images=images_b64)
        print("[QUERY] Gemini response received.")
        answer = gemini_response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No answer from Gemini.")
        return {"answer": answer}
    # For text documents, log and handle each step
    try:
        print("[QUERY] Performing ChromaDB vector search...")
        chroma_results = query_chroma(question, n_results=3, metadata_filter={"document_id": document_id})
        print("[QUERY] ChromaDB search complete.")
        context_chunks = chroma_results.get("documents", [[]])[0]
        context_text = "\n".join(context_chunks)
    except Exception as e:
        print(f"[QUERY] ChromaDB error: {e}")
        return {"error": f"ChromaDB error: {e}"}
    # Gather images as base64
    image_paths = processing.get("image_paths", [])
    images_b64 = []
    for img_path in image_paths:
        try:
            with open(img_path, "rb") as img_file:
                img_bytes = img_file.read()
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                images_b64.append(img_b64)
        except Exception as e:
            print(f"[QUERY] Failed to read image {img_path}: {e}")
            continue
    try:
        print("[QUERY] Calling Gemini for text+image query...")
        gemini_response = query_gemini(f"Context: {context_text}\n\nQuestion: {question}", images=images_b64)
        print("[QUERY] Gemini response received.")
        answer = gemini_response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No answer from Gemini.")
        return {"answer": answer}
    except Exception as e:
        print(f"[QUERY] Gemini API error: {e}")
        return {"error": f"Gemini API error: {e}"}

@app.get("/structure")
def get_document_structure(document_id: str):
    doc = DOCUMENT_STORE.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    processing = doc["processing"]
    sections = processing.get("sections", [])
    return {"sections": sections}

@app.post("/export/answer")
async def export_answer(document_id: str, question: str, format: str = "json"):
    doc = DOCUMENT_STORE.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    processing = doc["processing"]
    sub_questions = decompose_query(question)
    answers = []
    for sub_q in sub_questions:
        chroma_results = query_chroma(sub_q, n_results=3, metadata_filter={"document_id": document_id})
        vector_chunks = chroma_results.get("documents", [[]])[0]
        all_chunks = processing.get("text_preview", [])
        keyword_chunks = [chunk for chunk in all_chunks if sub_q.lower() in chunk.lower()]
        merged_chunks = list(dict.fromkeys(keyword_chunks + vector_chunks))
        context_text = "\n".join(merged_chunks)
        image_paths = processing.get("image_paths", [])
        images_b64 = []
        for img_path in image_paths:
            try:
                with open(img_path, "rb") as img_file:
                    img_bytes = img_file.read()
                    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                    images_b64.append(img_b64)
            except Exception as e:
                continue
        gemini_response = query_gemini(f"Context: {context_text}\n\nQuestion: {sub_q}", images=images_b64)
        answer = gemini_response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No answer from Gemini.")
        answers.append((sub_q, answer))
    synthesis_prompt = """Given the following sub-questions and their answers, synthesize a comprehensive answer to the original question.\n\n"""
    for sq, ans in answers:
        synthesis_prompt += f"Sub-question: {sq}\nAnswer: {ans}\n\n"
    synthesis_prompt += f"Original question: {question}\n\nFinal answer:"
    synthesis_response = query_gemini(synthesis_prompt)
    final_answer = synthesis_response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No answer from Gemini.")
    export_data = {
        "document_id": document_id,
        "question": question,
        "final_answer": final_answer,
        "sub_answers": answers
    }
    if format == "json":
        filename = f"answer_{document_id}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        return FileResponse(filename, media_type="application/json", filename=filename)
    elif format == "pdf" and FPDF:
        filename = f"answer_{document_id}.pdf"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, f"Question: {question}\n\nFinal Answer: {final_answer}\n\nSub-answers:\n")
        for sq, ans in answers:
            pdf.multi_cell(0, 10, f"- {sq}\n  {ans}\n")
        pdf.output(filename)
        return FileResponse(filename, media_type="application/pdf", filename=filename)
    else:
        return {"error": "Unsupported format or PDF export not available"}

@app.get("/export/structure")
def export_structure(document_id: str, format: str = "json"):
    doc = DOCUMENT_STORE.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    processing = doc["processing"]
    sections = processing.get("sections", [])
    export_data = {
        "document_id": document_id,
        "sections": sections
    }
    if format == "json":
        filename = f"structure_{document_id}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        return FileResponse(filename, media_type="application/json", filename=filename)
    elif format == "pdf" and FPDF:
        filename = f"structure_{document_id}.pdf"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "Document Structure (Sections):\n")
        for sec in sections:
            indent = '    ' * (sec.get('level', 1) - 1)
            pdf.multi_cell(0, 10, f"{indent}- {sec.get('title', '')}")
        pdf.output(filename)
        return FileResponse(filename, media_type="application/pdf", filename=filename)
    else:
        return {"error": "Unsupported format or PDF export not available"}

@app.post("/summarize")
async def summarize_document(document_id: str):
    doc = DOCUMENT_STORE.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    processing = doc["processing"]
    # Get the top N chunks (or all if small)
    chunks = processing.get("chunks", [])
    top_chunks = [c["text"] for c in chunks[:10]]  # Adjust N as needed
    context_text = "\n".join(top_chunks)
    prompt = (
        "You are an expert research assistant. Read the following document content and generate an executive summary that covers the main points, key findings, and any important tables, images, or code snippets.\n\n"
        f"Document Content:\n{context_text}\n\nExecutive Summary:"
    )
    gemini_response = query_gemini(prompt)
    summary = gemini_response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No summary from Gemini.")
    return {"summary": summary}

@app.get("/relationships")
def get_relationships():
    # Map: entity -> set of document_ids
    entity_map = {}
    for doc_id, doc in DOCUMENT_STORE.items():
        processing = doc["processing"]
        chunks = processing.get("chunks", [])
        for chunk in chunks:
            text = chunk["text"]
            # Use Gemini to extract entities/concepts from the chunk
            prompt = (
                "Extract a list of key entities, concepts, or topics mentioned in the following text. "
                "Return only a comma-separated list.\n\nText:\n" + text + "\nEntities:"
            )
            gemini_response = query_gemini(prompt)
            entity_str = gemini_response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            entities = [e.strip() for e in entity_str.split(",") if e.strip()]
            for entity in entities:
                if entity not in entity_map:
                    entity_map[entity] = set()
                entity_map[entity].add(doc_id)
    # Convert sets to lists for JSON serialization
    edges = [{"entity": entity, "documents": list(doc_ids)} for entity, doc_ids in entity_map.items()]
    return {"entities": list(entity_map.keys()), "edges": edges} 