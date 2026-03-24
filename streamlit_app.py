"""Streamlit frontend — upload papers, ask questions, view citations."""

import os
import uuid
import streamlit as st
import requests

API = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Paper Navigator", page_icon="📄", layout="wide")

# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .block-container { max-width: 900px; padding-top: 2rem; }
    .stChatMessage { border-radius: 12px; }
    div[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
    div[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    div[data-testid="stSidebar"] .stButton button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white !important;
        border: none; border-radius: 8px; width: 100%; font-weight: 600;
    }
    div[data-testid="stSidebar"] .stButton button:hover { opacity: 0.9; }
    .citation-card {
        background: #f8fafc; border-left: 3px solid #6366f1; padding: 10px 14px;
        border-radius: 6px; margin: 6px 0; font-size: 0.88rem;
    }
    h1 { background: linear-gradient(135deg, #6366f1, #ec4899);
         -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Sidebar: Upload + Papers ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📤 Upload Paper")
    uploaded = st.file_uploader("Choose a PDF", type="pdf", label_visibility="collapsed")
    title = st.text_input("Title", placeholder="Paper title")
    authors = st.text_input("Authors", placeholder="Author names")
    year = st.number_input("Year", min_value=1900, max_value=2030, value=2024)

    if st.button("Upload") and uploaded:
        with st.spinner("Ingesting…"):
            resp = requests.post(
                f"{API}/papers/upload",
                files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                data={"title": title or "Untitled", "authors": authors or "Unknown", "year": int(year)},
            )
        if resp.ok:
            d = resp.json()
            st.success(f"✅ **{d['title']}** — {d['chunks_created']} chunks indexed")
        else:
            st.error(f"Upload failed: {resp.text}")

    st.markdown("---")
    st.markdown("## 📚 Indexed Papers")
    try:
        papers = requests.get(f"{API}/papers", timeout=3).json()
        if papers:
            for p in papers:
                st.markdown(f"**{p['title']}** ({p['year']})  \n"
                            f"_{p['authors']}_ · {p['chunk_count']} chunks")
        else:
            st.caption("No papers uploaded yet.")
    except Exception:
        st.caption("⚠️ Backend not reachable.")

    st.markdown("---")
    st.markdown("## 🔍 Filters *(optional)*")
    f_section = st.selectbox("Section", ["Any", "Abstract", "Introduction", "Methodology",
                                          "Results", "Discussion", "Conclusion"])
    f_year = st.text_input("Filter by year", placeholder="e.g. 2023")

# ── Main area: Chat ─────────────────────────────────────────────────────────
st.markdown("# 📄 Paper Navigator")
st.caption("Ask questions about your uploaded research papers.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Ask a question about your papers…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build filters
    filters = {}
    if f_section != "Any":
        filters["section"] = f_section
    if f_year and f_year.isdigit():
        filters["year"] = int(f_year)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            resp = requests.post(f"{API}/query", json={
                "question": prompt,
                "session_id": st.session_state.session_id,
                "filters": filters or None,
            })
        if resp.ok:
            data = resp.json()
            st.markdown(data["answer"])

            if data["citations"]:
                st.markdown("**Sources:**")
                for c in data["citations"]:
                    st.markdown(
                        f'<div class="citation-card">'
                        f'<strong>{c["paper_title"]}</strong> · {c["section"]}<br>'
                        f'<em>{c["authors"]}</em>, {c["year"]}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            answer_html = data["answer"]
            if data["citations"]:
                answer_html += "\n\n*Sources: " + ", ".join(
                    f'{c["paper_title"]} ({c["section"]})' for c in data["citations"]
                ) + "*"
            st.session_state.messages.append({"role": "assistant", "content": answer_html})
        else:
            err = f"⚠️ Error: {resp.text}"
            st.error(err)
            st.session_state.messages.append({"role": "assistant", "content": err})
