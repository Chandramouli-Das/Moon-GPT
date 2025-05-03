import json
from pathlib import Path
import requests
import streamlit as st

# ───────────────────────────────────────────────
# Page & config
# ───────────────────────────────────────────────
st.set_page_config(page_title="MoonGPT", page_icon="🌕", layout="wide")

with open("config.json", "r") as f:
    cfg = json.load(f)

PDF_PATH   = Path(cfg.get("pdf_cv_path", "Resume.pdf"))
BACKEND_URL = "http://localhost:8000/api/chat"

# ───────────────────────────────────────────────
# Global CSS – darker text, card‑like chat, tidy lists
# ───────────────────────────────────────────────
st.markdown(
    """
    <style>
        /* sidebar tint & font */
        section[data-testid="stSidebar"] > div:first-child {padding-top:1rem;font-size:0.94rem;}
        /* download button full width */
        .stDownloadButton button {width:100%;}

        /* chat bubbles as cards */
        div[data-testid="stChatMessage"] > div[data-baseweb] {
            border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,0.08);padding:8px 12px;
        }
        /* assistant bubble color */
        div[data-testid="stChatMessage"] div:nth-child(2)[data-baseweb]{background:#ffffff;}
        /* user bubble color */
        div[data-testid="stChatMessage"] div:nth-child(1)[data-baseweb]{background:#dfe6ff;}
        /* list spacing in assistant replies */
        div[data-testid="stChatMessage"] ul{margin-left:1.3rem;}
    </style>
    """,
    unsafe_allow_html=True)

# ───────────────────────────────────────────────
# Sidebar
# ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌙 MoonGPT")
    st.markdown("<span style='font-size:0.9rem'>Your personal assistant for <b>Chandramouli Das</b></span>", unsafe_allow_html=True)

    # Resume button
    if PDF_PATH.exists():
        st.download_button("📄  Download Résumé", PDF_PATH.read_bytes(), file_name=PDF_PATH.name, mime="application/pdf")
    else:
        st.error("Résumé PDF missing")

    st.markdown("### 📚 Quick Prompts")
    samples = [
        "What are Chandramouli’s key skills?",
        "Tell me about his project experience",
        "What is his current role?",
        "Write a mail to Chandramouli about a job opening"
    ]
    for q in samples:
        st.button(q, key=q, on_click=lambda txt=q: st.session_state.setdefault("queue", []).append(txt))

    st.markdown("### ✉️ Email Guide")
    st.markdown(
        "<ol style='font-size:0.85rem;padding-left:1.2rem;line-height:1.4em'>"
        "<li>Ask me to <i>write a mail/email</i> with your name, company & contact.</li>"
        "<li>Review the draft I provide.</li>"
        "<li>Reply <b>Ok send it</b> – I'll forward it to <b>chandramoulidas39@gmail.com</b>.</li>"
        "</ol>", unsafe_allow_html=True)

# ───────────────────────────────────────────────
# Title & intro
# ───────────────────────────────────────────────
st.title("🌕 MoonGPT")
with st.container():
    st.markdown(
        "<div style='max-width:740px;font-size:0.95rem;'>"
        "Chat with a résumé‑aware assistant powered by GPT. Ask about Chandramouli Das’s skills, experience & projects, or have it draft emails for you." 
        "</div>", unsafe_allow_html=True)

# ───────────────────────────────────────────────
# Session state
# ───────────────────────────────────────────────
st.session_state.setdefault("messages", [{"role":"assistant","content":"Hi! I'm MoonGPT. Ask me anything about Chandramouli Das or request a résumé/email."}])
st.session_state.setdefault("queue", [])

# helper to call backend

def backend_call(conv):
    try:
        r = requests.post(BACKEND_URL, json={"conversation": conv}, timeout=20)
        return r.json().get("answer", "No response.") if r.status_code==200 else f"API error: {r.status_code}"
    except Exception as e:
        return f"❌ {e}"

# ───────────────────────────────────────────────
# Process one queued prompt
# ───────────────────────────────────────────────
if st.session_state["queue"]:
    txt = st.session_state["queue"].pop(0)
    st.session_state["messages"].append({"role":"user","content":txt})
    with st.spinner("Thinking…"):
        ans = backend_call(st.session_state["messages"])
    st.session_state["messages"].append({"role":"assistant","content":ans})
    st.rerun()

# ───────────────────────────────────────────────
# Render chat history
# ───────────────────────────────────────────────
for m in st.session_state["messages"]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ───────────────────────────────────────────────
# User input flow – show instantly, no duplicates
# ───────────────────────────────────────────────
if prompt := st.chat_input("Ask MoonGPT about Chandramouli…"):
    # show immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    # temp convo to backend
    tmp_conv = st.session_state["messages"] + [{"role":"user","content":prompt}]
    with st.spinner("Thinking…"):
        resp = backend_call(tmp_conv)

    with st.chat_message("assistant"):
        st.markdown(resp)

    # persist and rerun
    st.session_state["messages"].extend([
        {"role":"user","content":prompt},
        {"role":"assistant","content":resp}
    ])
    st.rerun()
