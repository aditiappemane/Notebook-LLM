import os
import requests

load_dotenv = None
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=" + GEMINI_API_KEY
GEMINI_EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key=" + GEMINI_API_KEY

def query_gemini(text, images=None):
    """
    Send a multimodal query (text + images) to Gemini and return the response.
    images: list of image base64 strings (optional)
    """
    contents = [{"parts": [{"text": text}]}]
    if images:
        for img_b64 in images:
            contents[0]["parts"].append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": img_b64
                }
            })
    payload = {"contents": contents}
    headers = {"Content-Type": "application/json"}
    response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}

def decompose_query(query):
    prompt = (
        "Decompose the following question into a list of simpler sub-questions. "
        "Return only the list, one per line.\n\n"
        f"Question: {query}"
    )
    response = query_gemini(prompt)
    # Parse the response to extract sub-questions (split by lines)
    if 'candidates' in response:
        text = response['candidates'][0]['content']['parts'][0]['text']
        sub_questions = [line.strip('- ').strip() for line in text.splitlines() if line.strip()]
        return sub_questions
    return [query] 