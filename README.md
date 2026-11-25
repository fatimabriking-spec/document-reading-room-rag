# PDF Chat Assistant

AI-powered RAG chatbot — upload up to 2 PDFs and ask anything about them.
Built with Python, Streamlit, and the Gemini API.

**Live Demo:** [pdf-chat-assistant-gemini](https://pdf-chat-assistant-gemini-dkpymfj77ttxxhwkldjdwx.streamlit.app/)

---

## Features

- Upload up to 2 PDFs and ask questions about their content
- Answers generated only from your PDFs — true RAG, no hallucination from outside knowledge
- Shows which PDF and chunk each answer was pulled from
- Dark theme UI with proper contrast — readable file names, buttons, and inputs
- Your question stays visible on screen while the answer is being generated
- No heavy ML libraries required — pure Python and the Gemini API do everything

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run pdf_rag_app.py
```

### 3. In the browser
1. Paste your Gemini API key in the sidebar
2. Upload 1 or 2 PDF files
3. Click **Process PDFs**
4. Ask any question!

---

## Get a Free Gemini API Key

1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Click "Create API Key" — no cost, no card required

---

## How It Works, Step by Step

This app is a RAG (Retrieval-Augmented Generation) pipeline built from
scratch, with no framework in between — just Python and the Gemini API.

### Step 1 — PDF Text Extraction
```python
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
```
Opens the uploaded PDF and reads every page's text using `pdfplumber`.

### Step 2 — Chunking
```python
def chunk_text(text, chunk_size=400, overlap=50):
    words = text.split()
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
```
Splits the extracted text into 400-word chunks with a 50-word overlap
between them, so no information gets lost right at a chunk boundary.

**Why chunk at all?** A full PDF is too long to search through directly.
Small, overlapping chunks make it possible to zero in on exactly the
relevant passage.

### Step 3 — Embeddings
```python
def get_embedding(text):
    result = genai.embed_content(model="models/gemini-embedding-001", content=text)
    return result["embedding"]
```
Converts each chunk into a vector — a list of numbers that captures the
meaning of the text, using Gemini's embedding model.

**Why?** Computers can't compare raw text for similarity, but they can
compare numbers mathematically.

### Step 4 — Cosine Similarity Search
```python
def cosine_similarity(vec_a, vec_b):
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    ...
    return dot / (mag_a * mag_b)

def find_top_chunks(query, chunk_store, top_k=4):
    query_vec = get_embedding(query)
    # Compare query vector against every chunk vector
    # Return the top 4 most similar chunks
```
When a question comes in, it's embedded the same way, then compared
against every chunk's vector using cosine similarity — the top 4 closest
matches win.

**Why?** This is the core of RAG retrieval: matching by meaning, not just
keyword overlap.

### Step 5 — Prompt Building
```python
def build_prompt(question, retrieved_chunks):
    context = "\n".join([chunk["text"] for chunk in retrieved_chunks])
    prompt = f"Answer using ONLY this context:\n{context}\n\nQuestion: {question}"
```
Combines the top 4 retrieved chunks with the user's question into a
single prompt.

**Why?** Gemini only ever sees the relevant slice of the document, not
the entire PDF — faster, cheaper, and more accurate.

### Step 6 — Answer Generation
```python
def ask_gemini(prompt):
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text
```
Sends the final prompt to Gemini 2.5 Flash and returns a natural-language
answer, grounded entirely in the retrieved context.

---

## Project Files

```
pdf_rag_app.py      Main app - all logic lives here
requirements.txt    Dependencies to install
README.md           This file
```

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python | Core language |
| Streamlit | Web UI |
| pdfplumber | PDF text extraction |
| google-generativeai | Gemini API - embeddings and chat |
| math (built-in) | Cosine similarity calculation |

---

## What Makes This a RAG System?

- **R — Retrieval:** finds the most relevant chunks from your PDFs for the question asked
- **A — Augmented:** injects those chunks into the prompt as grounding context
- **G — Generation:** Gemini writes the final answer using only that context

Without RAG, an LLM answers purely from its training data and can
hallucinate. With RAG, it is constrained to answer only from your
uploaded documents.

---

## Known Limitations

- Limited to 2 PDFs at a time — not built for large document collections
- Cosine similarity search runs in plain Python with no vector index, so
  it scales fine for a handful of documents but would not hold up for a
  large-scale knowledge base
- No OCR — scanned, image-only PDFs will not extract any text

---

Built by Salma Bibi | AI/ML Engineer
