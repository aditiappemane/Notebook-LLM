import os
from typing import Dict, Any
from unstructured.partition.auto import partition
from PIL import Image
import base64
import io
import re

# Optional imports for new formats
try:
    import markdown
except ImportError:
    markdown = None
try:
    from pylatexenc.latex2text import LatexNodes2Text
except ImportError:
    LatexNodes2Text = None

SUPPORTED_FORMATS = [
    ".pdf", ".docx", ".html", ".csv", ".xlsx", ".pptx", ".ipynb", ".png", ".jpg", ".jpeg", ".md", ".txt", ".tex"
]

CHART_KEYWORDS = ["chart", "graph", "plot", "figure", "diagram"]

def is_chart_image(el) -> bool:
    caption = getattr(el, 'caption', '') or ''
    alt_text = getattr(el, 'alt_text', '') or ''
    text = getattr(el, 'text', '') or ''
    combined = f"{caption} {alt_text} {text}".lower()
    return any(kw in combined for kw in CHART_KEYWORDS)

def extract_sections(text: str, ext: str):
    sections = []
    if ext == ".md":
        # Markdown: headers start with #
        for line in text.splitlines():
            m = re.match(r'^(#+)\s+(.*)', line)
            if m:
                level = len(m.group(1))
                title = m.group(2).strip()
                sections.append({"level": level, "title": title})
    elif ext == ".tex":
        # LaTeX: \section{}, \subsection{}, etc.
        for m in re.finditer(r'\\(sub)*section\*?\{([^}]*)\}', text):
            level = 2 if m.group(1) == 'sub' else 1
            title = m.group(2).strip()
            sections.append({"level": level, "title": title})
    elif ext == ".txt":
        # Plain text: look for numbered or all-caps lines
        for line in text.splitlines():
            if re.match(r'^[0-9]+(\.[0-9]+)*\s+.+', line) or line.isupper():
                sections.append({"level": 1, "title": line.strip()})
    return sections

def process_document(file_path: str) -> Dict[str, Any]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        return {"error": f"Unsupported file type: {ext}"}

    # Special handling for new formats
    if ext == ".md":
        with open(file_path, "r", encoding="utf-8") as f:
            md_text = f.read()
        if markdown:
            html = markdown.markdown(md_text)
            text_chunks = [{"text": html, "type": "text"}]
        else:
            text_chunks = [{"text": md_text, "type": "text"}]
        sections = extract_sections(md_text, ext)
        return {
            "num_chunks": len(text_chunks),
            "num_images": 0,
            "num_charts": 0,
            "num_tables": 0,
            "num_code_blocks": 0,
            "chunks": text_chunks,
            "text_preview": [c["text"] for c in text_chunks[:2]],
            "image_paths": [],
            "charts": [],
            "sections": sections,
            "status": "processed"
        }
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            txt = f.read()
        text_chunks = [{"text": txt, "type": "text"}]
        sections = extract_sections(txt, ext)
        return {
            "num_chunks": len(text_chunks),
            "num_images": 0,
            "num_charts": 0,
            "num_tables": 0,
            "num_code_blocks": 0,
            "chunks": text_chunks,
            "text_preview": [c["text"] for c in text_chunks[:2]],
            "image_paths": [],
            "charts": [],
            "sections": sections,
            "status": "processed"
        }
    elif ext == ".tex":
        with open(file_path, "r", encoding="utf-8") as f:
            tex = f.read()
        if LatexNodes2Text:
            text = LatexNodes2Text().latex_to_text(tex)
        else:
            text = re.sub(r'\\[a-zA-Z]+|\{.*?\}', '', tex)
        text_chunks = [{"text": text, "type": "text"}]
        sections = extract_sections(tex, ext)
        return {
            "num_chunks": len(text_chunks),
            "num_images": 0,
            "num_charts": 0,
            "num_tables": 0,
            "num_code_blocks": 0,
            "chunks": text_chunks,
            "text_preview": [c["text"] for c in text_chunks[:2]],
            "image_paths": [],
            "charts": [],
            "sections": sections,
            "status": "processed"
        }

    # Use unstructured to partition the document for other formats
    try:
        elements = partition(filename=file_path)
    except Exception as e:
        return {"error": f"Failed to parse document: {str(e)}"}

    text_chunks = []
    images = []
    image_paths = []
    charts = []
    tables = []
    code_blocks = []
    data_dir = os.path.join(os.path.dirname(file_path))
    for idx, el in enumerate(elements):
        if hasattr(el, 'text') and el.text:
            chunk_type = "text"
            if el.category == "Code":
                chunk_type = "code"
                code_blocks.append(el)
            elif el.category == "Table":
                chunk_type = "table"
                tables.append(el)
            text_chunks.append({"text": el.text, "type": chunk_type})
        if el.category == "Image":
            if hasattr(el, 'image') and el.image is not None:
                img: Image.Image = el.image
                img_path = os.path.join(data_dir, f"extracted_image_{idx}.png")
                img.save(img_path)
                image_paths.append(img_path)
                if is_chart_image(el):
                    charts.append({"path": img_path, "index": idx, "type": "chart"})
            images.append(el)

    all_text = "\n".join([c["text"] for c in text_chunks])
    sections = extract_sections(all_text, ext)

    return {
        "num_chunks": len(text_chunks),
        "num_images": len(images),
        "num_charts": len(charts),
        "num_tables": len(tables),
        "num_code_blocks": len(code_blocks),
        "chunks": text_chunks,
        "text_preview": [c["text"] for c in text_chunks[:2]],
        "image_paths": image_paths,
        "charts": charts,
        "sections": sections,
        "status": "processed"
    } 