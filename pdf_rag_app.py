import streamlit as st
import pdfplumber
import google.generativeai as genai
import math

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="PDF Chat Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS – clean, professional design
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Background ── */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #1e293b !important;
    border-right: 1px solid #334155;
}

/*
FIX #1 — ROOT CAUSE OF THE "HIDDEN TEXT" BUG:
The old code had `section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }`
This forces LIGHT gray text on EVERY element inside the sidebar, including
native Streamlit widgets (file uploader box, drag-and-drop area) that have
a WHITE background by default. Light text + white background = invisible text.
That blanket "*" selector is the actual bug. Fixed below: target only the
elements that actually sit on the dark sidebar background, and separately
force a dark background on the widgets that default to white.
*/
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] .stMarkdown {
    color: #e2e8f0 !important;
}

/* FIX #2 — File uploader drag-and-drop box and uploaded file row.
   These default to a white card. We force a dark background AND
   dark-compatible text color together, so they never go out of sync. */
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background-color: #0f172a !important;
    border: 1px dashed #475569 !important;
    border-radius: 10px !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {
    color: #e2e8f0 !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] svg {
    fill: #94a3b8 !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] {
    background-color: #0f172a !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] * {
    color: #e2e8f0 !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"] {
    color: #22c55e !important;
}
/* delete "x" icon on uploaded file — force visible icon color */
section[data-testid="stSidebar"] [data-testid="stFileUploaderDeleteBtn"] svg {
    fill: #e2e8f0 !important;
}

/* FIX #3 — Password show/hide "eye" icon on the API key field.
   Same root cause: default icon color can vanish depending on background.
   We pin it to a visible color on both light and dark surroundings. */
[data-testid="stTextInput"] button svg,
[data-testid="baseButton-headerNoPadding"] svg,
button[title="Show password text"] svg,
button[title="Hide password text"] svg {
    fill: #94a3b8 !important;
    opacity: 1 !important;
}
[data-testid="stTextInput"] button:hover svg {
    fill: #ffffff !important;
}

/* FIX #4 (revised) — Streamlit's native "Press Enter to apply" hint
   renders ABOVE the input in some versions and its color can blend into
   the dark background. Its position can't be reliably controlled with
   CSS since it sits inside Streamlit's internal widget structure. So we
   hide it entirely and render our own hint below the input instead,
   where we control both position and color. */
[data-testid="InputInstructions"] {
    display: none !important;
}
.key-hint {
    color: #94a3b8 !important;
    font-size: 12px;
    margin-top: 4px;
    margin-bottom: 6px;
}

/* Compact checkmark badge shown BELOW the input, on its own line,
   never wrapping. */
.key-status-inline {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 6px;
    font-size: 13px;
    color: #22c55e !important;
    white-space: nowrap;
}

/* ── Header banner ── */
.header-banner {
    background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);
    border-radius: 14px;
    padding: 28px 32px;
    margin-bottom: 24px;
    text-align: center;
}
.header-banner h1 {
    color: white !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    margin: 0 !important;
}
.header-banner p {
    color: rgba(255,255,255,0.85) !important;
    font-size: 14px !important;
    margin: 6px 0 0 !important;
}

/* ── Status cards ── */
.status-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    color: #e2e8f0 !important;
    font-size: 13px;
    min-height: 24px;
}
.status-card strong {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: block;
    min-width: 0;
    flex: 1;
}
.status-card.success { border-left: 4px solid #22c55e; }
.status-card.waiting { border-left: 4px solid #f59e0b; }
.status-card.error { border-left: 4px solid #ef4444; }

/* ── Chat messages ── */
.msg-user {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 16px 16px 4px 16px;
    padding: 14px 18px;
    margin: 8px 0 8px 60px;
    color: white;
    font-size: 14px;
    line-height: 1.7;
}
.msg-bot {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 16px 16px 16px 4px;
    padding: 14px 18px;
    margin: 8px 60px 8px 0;
    color: #e2e8f0;
    font-size: 14px;
    line-height: 1.8;
}
.msg-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 5px;
    opacity: 0.6;
}
.msg-user .msg-label { color: white; }
.msg-bot .msg-label { color: #94a3b8; }

/* ── Source box ── */
.source-box {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px 14px;
    margin-top: 10px;
    font-size: 12px;
    color: #94a3b8;
}
.source-box strong { color: #06b6d4; }

/* ── Chunk info tag ── */
.chunk-tag {
    display: inline-block;
    background: #0f172a;
    border: 1px solid #475569;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    color: #94a3b8;
    margin: 4px 2px;
}

/* ── Info box ── */
.info-box {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 16px 20px;
    color: #94a3b8;
    font-size: 13px;
    line-height: 1.8;
    text-align: center;
}

/* ── Step cards (how it works) ── */
.step-card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    color: #e2e8f0;
    font-size: 13px;
}
.step-num {
    display: inline-block;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    font-size: 11px;
    font-weight: 700;
    width: 22px; height: 22px;
    border-radius: 50%;
    text-align: center;
    line-height: 22px;
    margin-right: 8px;
}

/* ── Inputs (both class-name AND data-testid, since Streamlit versions
   differ in which one is present in the DOM — relying on only one is
   what broke the main question box in the first place) ── */
.stTextInput input, .stTextArea textarea,
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
}
.stButton button, [data-testid="stBaseButton-secondary"], [data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 10px 24px !important;
    width: 100%;
}
.stButton button *, [data-testid="stFormSubmitButton"] button * {
    color: white !important;
}
.stButton button:hover, [data-testid="stFormSubmitButton"] button:hover {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    transform: translateY(-1px);
}

/* ── Streamlit default overrides ── */
.stMarkdown p, .stMarkdown li { color: #e2e8f0; }
h1,h2,h3 { color: #f1f5f9 !important; }
label { color: #94a3b8 !important; }
.stFileUploader { background: #1e293b; border-radius: 10px; }
.uploadedFileName { color: #22c55e !important; }
div[data-testid="stMetricValue"] { color: #6366f1 !important; }

/* C — Minimal Reader: warm paper, sage green, quiet typography */
.stApp { background:#f3f1eb !important; color:#283b30 !important; }
[data-testid="stHeader"] { background:transparent !important; }
.main .block-container { max-width:1220px; padding-top:2rem; padding-bottom:3rem; }
section[data-testid="stSidebar"] { background:#f7f5ee !important; border-right:1px solid #e7e3d8 !important; }
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] .stMarkdown { color:#35473a !important; }
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] { background:#fcfbf7 !important; border:1px dashed #c9d1c7 !important; border-radius:12px !important; }
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * { color:#59685c !important; }
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] svg { fill:#7c8a7d !important; }
section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] { background:#fcfbf7 !important; border:1px solid #e7e3d8 !important; border-radius:10px !important; }
section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] * { color:#35473a !important; }
section[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"] { color:#557765 !important; }
section[data-testid="stSidebar"] [data-testid="stFileUploaderDeleteBtn"] svg { fill:#737b70 !important; }
section[data-testid="stSidebar"] hr { border-color:#e7e3d8 !important; }
[data-testid="stTextInput"] button svg, [data-testid="baseButton-headerNoPadding"] svg, button[title="Show password text"] svg, button[title="Hide password text"] svg { fill:#737b70 !important; opacity:1 !important; }
.key-hint { color:#858a7f !important; }
.key-status-inline { color:#557765 !important; font-weight:600; }
.header-banner { background:#e9eee8 !important; border:1px solid #d9e1d7 !important; border-radius:18px !important; padding:34px 40px !important; margin-bottom:26px !important; text-align:left !important; box-shadow:0 8px 24px rgba(45,66,50,.06); }
.header-banner h1 { color:#283b30 !important; font-family:Georgia,serif !important; font-size:32px !important; font-weight:700 !important; letter-spacing:-.4px; }
.header-banner p { color:#657267 !important; font-size:15px !important; margin-top:9px !important; }
div[data-testid="stMetric"] { background:#fcfbf7 !important; border:1px solid #e7e3d8 !important; border-radius:14px !important; padding:15px 18px !important; box-shadow:0 3px 12px rgba(45,66,50,.035); }
div[data-testid="stMetricLabel"] p { color:#737b70 !important; font-size:13px; }
div[data-testid="stMetricValue"] { color:#283b30 !important; font-weight:700; }
.status-card { background:#fcfbf7 !important; border:1px solid #e7e3d8 !important; border-left:4px solid #72917d !important; border-radius:12px !important; color:#35473a !important; box-shadow:0 3px 12px rgba(45,66,50,.035); }
.status-card.success { border-left-color:#557765 !important; }
.status-card.waiting { border-left-color:#b58b4a !important; }
.status-card.error { border-left-color:#b8544a !important; }
.msg-user { background:#edf2ed !important; border:1px solid #dce6dc !important; border-radius:16px 16px 5px 16px; color:#35473a !important; }
.msg-bot { background:#fcfbf7 !important; border:1px solid #e7e3d8 !important; border-radius:16px 16px 16px 5px; color:#455248 !important; box-shadow:0 4px 16px rgba(45,66,50,.04); }
.msg-label, .msg-bot .msg-label { color:#737b70 !important; }
.msg-user .msg-label { color:#557765 !important; }
.source-box, .info-box { background:#fcfbf7 !important; border:1px solid #e7e3d8 !important; color:#737b70 !important; border-radius:12px !important; }
.source-box strong { color:#557765 !important; }
.chunk-tag { background:#edf2ed !important; border-color:#dce6dc !important; color:#496b56 !important; }
.step-card { background:#fcfbf7 !important; border-color:#e7e3d8 !important; color:#455248 !important; }
.step-num { background:#e7eee8 !important; color:#557765 !important; }
.stTextInput input, .stTextArea textarea, [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { background:#fcfbf7 !important; border:1px solid #d9ded5 !important; color:#283b30 !important; border-radius:10px !important; }
.stTextInput input:focus, [data-testid="stTextInput"] input:focus { border-color:#8ca998 !important; box-shadow:0 0 0 3px rgba(85,119,101,.12) !important; }
.stButton button, [data-testid="stFormSubmitButton"] button { background:#557765 !important; color:#fff !important; border:0 !important; border-radius:10px !important; font-weight:600 !important; }
.stButton button *, [data-testid="stFormSubmitButton"] button * { color:#fff !important; }
.stButton button:hover, [data-testid="stFormSubmitButton"] button:hover { background:#42634f !important; }
.stMarkdown p, .stMarkdown li { color:#455248 !important; }
h1,h2,h3 { color:#283b30 !important; }
label { color:#59685c !important; }
.stFileUploader { background:transparent !important; }
.uploadedFileName { color:#557765 !important; }
@media (max-width:700px) { .main .block-container { padding:1rem 1rem 2rem; } .header-banner { padding:25px 22px !important; } .header-banner h1 { font-size:26px !important; } .msg-user { margin-left:20px; } .msg-bot { margin-right:20px; } }
/* Streamlit native controls: align uploader and API key field with the sage theme */
hr, .stMarkdown hr { border-color:#e7e3d8 !important; background:#e7e3d8 !important; }
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button,
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button[kind="secondary"] {
    background:#557765 !important; color:#ffffff !important; border:0 !important; border-radius:9px !important; box-shadow:none !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button *,
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button span { color:#ffffff !important; }
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button:hover { background:#42634f !important; }
section[data-testid="stSidebar"] [data-testid="stTextInput"] input,
section[data-testid="stSidebar"] [data-testid="stTextInput"] [data-baseweb="input"] input {
    background:#fcfbf7 !important; color:#283b30 !important; border:1px solid #d9ded5 !important;
}
section[data-testid="stSidebar"] [data-testid="stTextInput"] input::placeholder { color:#858a7f !important; opacity:1 !important; }
section[data-testid="stSidebar"] [data-testid="stTextInput"] [data-baseweb="input"] { background:#fcfbf7 !important; border-color:#d9ded5 !important; }
section[data-testid="stSidebar"] [data-testid="stTextInput"] button { background:#efeee7 !important; border-left:1px solid #d9ded5 !important; }
section[data-testid="stSidebar"] [data-testid="stTextInput"] button svg { fill:#557765 !important; }
section[data-testid="stSidebar"] [data-testid="stTextInput"] button:hover { background:#e7eee8 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def extract_text_from_pdf(uploaded_file) -> str:
    """Extract all text from a PDF file."""
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks.
    chunk_size = words per chunk
    overlap = words shared between consecutive chunks
    """
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def get_embedding(text: str, model="models/gemini-embedding-001") -> list[float]:
    """Get embedding vector from Gemini Embeddings API."""
    result = genai.embed_content(model=model, content=text)
    return result["embedding"]


def find_top_chunks(query: str, chunk_store: list[dict], top_k: int = 4) -> list[dict]:
    """
    Embed the query, compute cosine similarity with all chunks,
    return top_k most relevant chunks.
    """
    query_vec = get_embedding(query)
    scored = []
    for item in chunk_store:
        score = cosine_similarity(query_vec, item["embedding"])
        scored.append({**item, "score": score})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def build_prompt(question: str, retrieved_chunks: list[dict]) -> str:
    """Build the final prompt for Gemini with retrieved context."""
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        context_parts.append(
            f"[Source: {chunk['pdf_name']}, Chunk {chunk['chunk_id']}]\n{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""You are a helpful AI assistant. Answer the user's question using ONLY the information provided in the document excerpts below.

If the answer is not found in the documents, say: "I could not find this information in the uploaded PDFs."

Always mention which PDF or section the answer came from.

DOCUMENT EXCERPTS:
{context}

USER QUESTION:
{question}

ANSWER:"""
    return prompt


def ask_gemini(prompt: str, model_name: str = "gemini-2.5-flash") -> str:
    """Send prompt to Gemini and return the response."""
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text


def process_pdf(uploaded_file, pdf_name: str) -> list[dict]:
    """Full pipeline: PDF → text → chunks → embeddings → list of dicts."""
    with st.spinner(f" Reading {pdf_name}..."):
        raw_text = extract_text_from_pdf(uploaded_file)

    if not raw_text:
        st.error(f" Could not extract text from {pdf_name}. Make sure it is not a scanned image PDF.")
        return []

    chunks = chunk_text(raw_text, chunk_size=400, overlap=50)

    chunk_store = []
    progress = st.progress(0, text=f" Creating embeddings for {pdf_name}...")
    for idx, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        chunk_store.append({
            "pdf_name": pdf_name,
            "chunk_id": idx + 1,
            "text": chunk,
            "embedding": embedding,
        })
        progress.progress((idx + 1) / len(chunks), text=f" Embedding chunk {idx+1}/{len(chunks)} — {pdf_name}")

    progress.empty()
    return chunk_store


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Configuration")
    st.markdown("---")

    # API Key input
    st.markdown("**Gemini API Key**", unsafe_allow_html=False)

    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="Paste your Gemini API key here",
        help="Get your free API key from https://aistudio.google.com",
        label_visibility="collapsed",
        key="api_key",
    )
    st.markdown('<div class="key-hint">Press Enter after pasting</div>', unsafe_allow_html=True)

    if api_key:
        genai.configure(api_key=api_key)
        st.markdown('<div class="key-status-inline">✓ Connected</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Upload PDFs")
    st.caption("Upload up to 2 PDF files")

    pdf1 = st.file_uploader(" PDF Document 1", type=["pdf"], key="pdf1")
    pdf2 = st.file_uploader(" PDF Document 2", type=["pdf"], key="pdf2")

    st.markdown("---")

    # Process button
    process_btn = st.button(" Process PDFs", use_container_width=True)

    st.markdown("---")

    # How it works
    st.markdown("### How it works")
    steps = [
        ("1", "PDF text extracted"),
        ("2", "Text split into chunks"),
        ("3", "Embeddings created (Gemini)"),
        ("4", "Your question embedded"),
        ("5", "Similar chunks retrieved"),
        ("6", "Gemini answers from context"),
    ]
    for num, desc in steps:
        st.markdown(
            f'<div class="step-card"><span class="step-num">{num}</span>{desc}</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    if st.button(" Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
if "chunk_store" not in st.session_state:
    st.session_state.chunk_store = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pdfs_processed" not in st.session_state:
    st.session_state.pdfs_processed = False
if "pdf_names" not in st.session_state:
    st.session_state.pdf_names = []


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="header-banner">
    <h1>PDF Chat Assistant</h1>
    <p>Upload up to 2 PDFs and ask any question — powered by Gemini AI + RAG</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# METRICS ROW (simplified — technical numbers like chunk counts
# don't mean anything to a non-technical user, so they're dropped)
# ─────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    pdfs_uploaded = sum([pdf1 is not None, pdf2 is not None])
    st.metric(" PDFs Uploaded", f"{pdfs_uploaded} / 2")
with col2:
    status = " Ready" if st.session_state.pdfs_processed else " Waiting"
    st.metric(" Status", status)

st.markdown("---")


# ─────────────────────────────────────────────
# PROCESS PDFs
# ─────────────────────────────────────────────
if process_btn:
    if not api_key:
        st.error(" Please enter your Gemini API key in the sidebar first.")
    elif not pdf1 and not pdf2:
        st.error(" Please upload at least 1 PDF.")
    else:
        st.session_state.chunk_store = []
        st.session_state.pdf_names = []
        st.session_state.chat_history = []
        st.session_state.pdfs_processed = False

        all_chunks = []

        if pdf1:
            chunks = process_pdf(pdf1, pdf1.name)
            all_chunks.extend(chunks)
            st.session_state.pdf_names.append(pdf1.name)

        if pdf2:
            chunks = process_pdf(pdf2, pdf2.name)
            all_chunks.extend(chunks)
            st.session_state.pdf_names.append(pdf2.name)

        st.session_state.chunk_store = all_chunks
        st.session_state.pdfs_processed = True

        st.success(
            f" Done! Processed **{len(st.session_state.pdf_names)} PDF(s)** → "
            f"**{len(all_chunks)} chunks** created and embedded. You can now ask questions!"
        )
        st.rerun()


# ─────────────────────────────────────────────
# PDF STATUS DISPLAY (simplified — no chunk counts)
# ─────────────────────────────────────────────
if st.session_state.pdfs_processed and st.session_state.pdf_names:
    cols = st.columns(len(st.session_state.pdf_names))
    for i, name in enumerate(st.session_state.pdf_names):
        with cols[i]:
            st.markdown(
                f'<div class="status-card success">✓ <strong title="{name}">{name}</strong></div>',
                unsafe_allow_html=True,
            )
    st.markdown("---")


# ─────────────────────────────────────────────
# CHAT INTERFACE
# ─────────────────────────────────────────────
st.markdown("### Ask Questions About Your PDFs")

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# Display chat history
if st.session_state.chat_history or st.session_state.pending_question:
    for entry in st.session_state.chat_history:
        # User message
        st.markdown(
            f'<div class="msg-user"><div class="msg-label">You</div>{entry["question"]}</div>',
            unsafe_allow_html=True,
        )
        # Bot answer
        sources_html = ""
        if entry.get("sources"):
            source_tags = "".join(
                f'<span class="chunk-tag"> {s["pdf_name"]} · Chunk {s["chunk_id"]} · Score: {s["score"]:.2f}</span>'
                for s in entry["sources"]
            )
            sources_html = f'<div class="source-box"><strong> Sources used:</strong><br>{source_tags}</div>'

        st.markdown(
            f'<div class="msg-bot"><div class="msg-label">PDF Assistant</div>'
            f'{entry["answer"]}{sources_html}</div>',
            unsafe_allow_html=True,
        )

    # FIX — question no longer vanishes during processing.
    # It's rendered here immediately, and stays on screen while the
    # answer is being generated below it, instead of disappearing when
    # the form clears and reappearing only once the answer is ready.
    if st.session_state.pending_question:
        pending_q = st.session_state.pending_question
        st.markdown(
            f'<div class="msg-user"><div class="msg-label">You</div>{pending_q}</div>',
            unsafe_allow_html=True,
        )
        with st.spinner(" Searching documents and generating answer..."):
            try:
                top_chunks = find_top_chunks(pending_q, st.session_state.chunk_store, top_k=4)
                prompt = build_prompt(pending_q, top_chunks)
                answer = ask_gemini(prompt)
                st.session_state.chat_history.append({
                    "question": pending_q,
                    "answer": answer,
                    "sources": top_chunks,
                })
            except Exception as e:
                error_msg = f" Error: {str(e)}"
                if "API_KEY" in str(e).upper() or "invalid" in str(e).lower():
                    error_msg += " Please check your Gemini API key in the sidebar."
                st.session_state.chat_history.append({
                    "question": pending_q,
                    "answer": error_msg,
                    "sources": None,
                })
        st.session_state.pending_question = None
        st.rerun()
else:
    if st.session_state.pdfs_processed:
        st.markdown(
            '<div class="info-box"> PDFs are ready! Ask your first question below.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="info-box"> Upload your PDFs in the sidebar and click <strong>Process PDFs</strong> to get started.</div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# Question input
if st.session_state.pdfs_processed:
    with st.form("question_form", clear_on_submit=True):
        question = st.text_input(
            "Your question",
            placeholder="e.g. What is the main topic of these documents? Summarize the key points...",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button(" Ask Question", use_container_width=True)

    if submitted and question.strip():
        st.session_state.pending_question = question
        st.rerun()