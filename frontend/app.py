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

    # Summarization button
    st.header("Summarization")
    if st.button("Generate Executive Summary"):
        with st.spinner("Generating summary..."):
            resp = requests.post("http://localhost:8000/summarize", params={"document_id": st.session_state['document_id']})
            if resp.status_code == 200:
                summary = resp.json().get("summary", "No summary returned.")
                st.success("Executive Summary:")
                st.write(summary)
            else:
                st.error(f"Summarization failed: {resp.text}")

    # Relationship mapping button
    st.header("Relationship Mapping (Entities Across Documents)")
    if st.button("Show Entity-Document Relationships"):
        with st.spinner("Extracting relationships..."):
            resp = requests.get("http://localhost:8000/relationships")
            if resp.status_code == 200:
                data = resp.json()
                st.write("**Entities and their associated documents:**")
                for edge in data.get("edges", []):
                    st.write(f"- {edge['entity']}: {', '.join(edge['documents'])}")
                # Optional: visualize as a network graph if streamlit_agraph is available
                try:
                    from streamlit_agraph import agraph, Node, Edge, Config
                    nodes = [Node(id=entity, label=entity) for entity in data.get("entities", [])]
                    doc_nodes = [Node(id=doc_id, label=doc_id, shape="box") for edge in data.get("edges", []) for doc_id in edge["documents"]]
                    all_nodes = {n.id: n for n in nodes + doc_nodes}
                    edges = [Edge(source=edge["entity"], target=doc_id) for edge in data.get("edges", []) for doc_id in edge["documents"]]
                    config = Config(width=800, height=400, directed=False, physics=True)
                    st.subheader("Entity-Document Network Graph")
                    agraph(list(all_nodes.values()), edges, config)
                except ImportError:
                    st.info("Install streamlit-agraph for network graph visualization: pip install streamlit-agraph")
            else:
                st.error(f"Relationship mapping failed: {resp.text}")

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