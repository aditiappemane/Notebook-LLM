import streamlit as st
import requests
import os

st.set_page_config(page_title="Notebook LLM - Multimodal Research Assistant")

st.title("Notebook LLM - Multimodal Research Assistant")
st.markdown("""
Welcome! This assistant can process and reason over documents containing text, images, tables, charts, and code. 

**Features:**
- Upload documents (PDF, DOCX, HTML, CSV, Excel, PowerPoint, Jupyter, images)
- Ask complex queries about your documents
- Multimodal understanding using Gemini API

---
""")

BACKEND_UPLOAD_URL = "http://localhost:8000/upload"
BACKEND_QUERY_URL = "http://localhost:8000/query"
BACKEND_STRUCTURE_URL = "http://localhost:8000/structure"

st.header("1. Upload your document")
uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "html", "csv", "xlsx", "pptx", "ipynb", "png", "jpg", "jpeg", "md", "txt", "tex"]) 

if 'document_id' not in st.session_state:
    st.session_state['document_id'] = ''
if 'processing_result' not in st.session_state:
    st.session_state['processing_result'] = None

if uploaded_file:
    st.success(f"Uploaded: {uploaded_file.name}")
    if st.button("Process Document"):
        with st.spinner("Uploading and processing..."):
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            try:
                response = requests.post(BACKEND_UPLOAD_URL, files=files)
                if response.status_code == 200:
                    result = response.json()
                    st.session_state['processing_result'] = result
                    st.session_state['document_id'] = result.get('document_id', '')
                else:
                    st.error(f"Backend error: {response.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")

if st.session_state['processing_result']:
    st.header("Processing Summary")
    st.json(st.session_state['processing_result'])

    # Section structure visualization
    st.header("Document Structure (Sections)")
    if st.session_state['document_id']:
        try:
            resp = requests.get(BACKEND_STRUCTURE_URL, params={"document_id": st.session_state['document_id']})
            if resp.status_code == 200:
                sections = resp.json().get('sections', [])
                if sections:
                    for sec in sections:
                        indent = '    ' * (sec.get('level', 1) - 1)
                        st.write(f"{indent}- {sec.get('title', '')}")
                else:
                    st.info("No section structure found.")
            else:
                st.error(f"Error fetching structure: {resp.text}")
        except Exception as e:
            st.error(f"Error fetching structure: {e}")

    # Export buttons (commented out)
    # st.header("Export")
    # col1, col2 = st.columns(2)
    # with col1:
    #     if st.button("Export Answer as PDF"):
    #         params = {
    #             "document_id": st.session_state['document_id'],
    #             "question": st.text_input("Enter your question for export", key="export_q"),
    #             "format": "pdf"
    #         }
    #         headers = {}  # Add JWT if needed
    #         resp = requests.post(f"{BACKEND_UPLOAD_URL.replace('/upload', '/export/answer')}", params=params, headers=headers)
    #         if resp.status_code == 200:
    #             with open("answer_export.pdf", "wb") as f:
    #                 f.write(resp.content)
    #             st.success("Answer exported as PDF! [Download](answer_export.pdf)")
    #         else:
    #             st.error("Export failed.")
    #     if st.button("Export Structure as PDF"):
    #         params = {
    #             "document_id": st.session_state['document_id'],
    #             "format": "pdf"
    #         }
    #         headers = {}  # Add JWT if needed
    #         resp = requests.get(f"{BACKEND_UPLOAD_URL.replace('/upload', '/export/structure')}", params=params, headers=headers)
    #         if resp.status_code == 200:
    #             with open("structure_export.pdf", "wb") as f:
    #                 f.write(resp.content)
    #             st.success("Structure exported as PDF! [Download](structure_export.pdf)")
    #         else:
    #             st.error("Export failed.")
    # with col2:
    #     if st.button("Export Answer as JSON"):
    #         params = {
    #             "document_id": st.session_state['document_id'],
    #             "question": st.text_input("Enter your question for export (JSON)", key="export_q_json"),
    #             "format": "json"
    #         }
    #         headers = {}  # Add JWT if needed
    #         resp = requests.post(f"{BACKEND_UPLOAD_URL.replace('/upload', '/export/answer')}", params=params, headers=headers)
    #         if resp.status_code == 200:
    #             with open("answer_export.json", "wb") as f:
    #                 f.write(resp.content)
    #             st.success("Answer exported as JSON! [Download](answer_export.json)")
    #         else:
    #             st.error("Export failed.")
    #     if st.button("Export Structure as JSON"):
    #         params = {
    #             "document_id": st.session_state['document_id'],
    #             "format": "json"
    #         }
    #         headers = {}  # Add JWT if needed
    #         resp = requests.get(f"{BACKEND_UPLOAD_URL.replace('/upload', '/export/structure')}", params=params, headers=headers)
    #         if resp.status_code == 200:
    #             with open("structure_export.json", "wb") as f:
    #                 f.write(resp.content)
    #             st.success("Structure exported as JSON! [Download](structure_export.json)")
    #         else:
    #             st.error("Export failed.")

    st.header("2. Ask a question about your document")
    st.write(f"Document ID: `{st.session_state['document_id']}`")
    question = st.text_input("Enter your question")
    if st.button("Submit Query"):
        with st.spinner("Querying backend..."):
            payload = {"document_id": st.session_state['document_id'], "question": question}
            try:
                response = requests.post(BACKEND_QUERY_URL, params=payload)
                if response.status_code == 200:
                    answer = response.json().get('answer', '')
                    st.success(f"**Answer:** {answer}")
                else:
                    st.error(f"Backend error: {response.text}")
            except Exception as e:
                st.error(f"Connection error: {e}") 