import os
import time
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components

# ───────────────────────────────────────────────
# Page & config
# ───────────────────────────────────────────────
st.set_page_config(page_title="MoonGPT - Futuristic AI Assistant", page_icon="🚀", layout="wide")


def _secret(name: str, default=None):
    """Safely read from st.secrets with a fallback."""
    return st.secrets[name] if name in st.secrets else default


PDF_PATH = Path(os.getenv("PDF_CV_PATH") or _secret("PDF_CV_PATH", "Resume.pdf"))
DOCX_PATH = Path(os.getenv("DOCX_PATH") or _secret("DOCX_PATH", "Document.docx"))
BACKEND_URL = os.getenv("BACKEND_URL") or _secret(
    "BACKEND_URL", "https://moon-gpt.onrender.com/api/chat"
)
EMAIL_SENDER = os.getenv("EMAIL_SENDER") or _secret("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") or _secret("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER") or _secret("EMAIL_RECEIVER", "")

# ───────────────────────────────────────────────
# Global CSS – Futuristic chatbot UI with neon glows, animations, and modern design
# ───────────────────────────────────────────────
st.markdown(
    """
    <style>
        :root {
            --bg: #0a0a0a;
            --card: #1a1a2e;
            --card-2: #16213e;
            --text: #ffffff;
            --muted: #a0a0a0;
            --accent: #00d4ff;
            --accent-soft: #0f3460;
            --user-bg: #e91e63;
            --assistant-bg: #4a148c;
            --border: rgba(0, 212, 255, 0.3);
            --glow: 0 0 20px rgba(0, 212, 255, 0.5);
            --user-glow: 0 0 20px rgba(233, 30, 99, 0.5);
            --assistant-glow: 0 0 20px rgba(74, 20, 140, 0.5);
        }

        .stApp {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            color: var(--text);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* Animated background particles */
        .stApp::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: radial-gradient(circle at 20% 80%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
                              radial-gradient(circle at 80% 20%, rgba(233, 30, 99, 0.1) 0%, transparent 50%),
                              radial-gradient(circle at 40% 40%, rgba(74, 20, 140, 0.1) 0%, transparent 50%);
            animation: float 20s ease-in-out infinite;
            z-index: -1;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }

        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem;
            font-size: 0.95rem;
            background: rgba(26, 26, 46, 0.95);
            border-right: 1px solid var(--border);
            box-shadow: inset 0 0 20px rgba(0, 212, 255, 0.1);
        }

        /* Sidebar typography */
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: var(--text);
            letter-spacing: 0.5px;
            text-shadow: 0 0 10px var(--accent);
        }

        section[data-testid="stSidebar"] .moon-muted {
            color: var(--muted);
            font-size: 0.92rem;
        }

        /* Sidebar cards with glow */
        .moon-side-card {
            background: linear-gradient(180deg, rgba(26, 26, 46, 0.95) 0%, rgba(22, 33, 62, 0.98) 100%);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: var(--glow);
            transition: all 0.3s ease;
        }

        .moon-side-card:hover {
            box-shadow: 0 0 30px rgba(0, 212, 255, 0.7);
            transform: translateY(-2px);
        }

        .moon-side-card .moon-card-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--accent);
        }

        .stDownloadButton button,
        .stButton button {
            border-radius: 15px;
            border: 1px solid var(--border);
            background: linear-gradient(45deg, var(--card-2), var(--accent-soft));
            color: var(--text);
            transition: all 0.3s ease;
            box-shadow: var(--glow);
        }

        .stDownloadButton button:hover,
        .stButton button:hover {
            box-shadow: 0 0 25px var(--accent);
            transform: scale(1.05);
        }

        .stDownloadButton button {
            width: 100%;
        }

        /* Futuristic header */
        .moon-header {
            background: linear-gradient(135deg, #00d4ff 0%, #e91e63 50%, #4a148c 100%);
            color: white;
            padding: 1.5rem 2rem;
            border-radius: 25px;
            box-shadow: 0 0 40px rgba(0, 212, 255, 0.5);
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        }

        .moon-header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: conic-gradient(from 0deg, transparent, rgba(255,255,255,0.1), transparent);
            animation: rotate 10s linear infinite;
        }

        @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .moon-header > div:first-child {
            font-size: 2rem;
            font-weight: 700;
            text-shadow: 0 0 20px rgba(255,255,255,0.8);
            z-index: 1;
            position: relative;
        }

        .moon-subtitle {
            color: rgba(255,255,255,0.9);
            font-size: 1rem;
            margin-top: 0.5rem;
            z-index: 1;
            position: relative;
        }

        /* Chat bubbles with animations and glows */
        div[data-testid="stChatMessage"] > div[data-baseweb] {
            border-radius: 20px;
            box-shadow: var(--glow);
            padding: 1rem 1.5rem;
            border: 1px solid var(--border);
            background: var(--card);
            animation: slideIn 0.5s ease-out;
            margin: 0.5rem 0;
            position: relative;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* User bubble */
        div[data-testid="stChatMessage"][data-testid*="user"] > div[data-baseweb] {
            background: linear-gradient(135deg, var(--user-bg), #ff6b9d);
            border: 1px solid rgba(233, 30, 99, 0.5);
            box-shadow: var(--user-glow);
            margin-left: 2rem;
        }

        /* Assistant bubble */
        div[data-testid="stChatMessage"][data-testid*="assistant"] > div[data-baseweb] {
            background: linear-gradient(135deg, var(--assistant-bg), #7b1fa2);
            border: 1px solid rgba(74, 20, 140, 0.5);
            box-shadow: var(--assistant-glow);
            margin-right: 2rem;
        }

        /* Chat input futuristic */
        div[data-testid="stChatInput"] {
            margin-bottom: 80px !important;
            margin-right: 70px !important;
            z-index: 100;
            position: relative;
        }

        div[data-testid="stChatInput"] textarea {
            border-radius: 20px;
            border: 1px solid var(--border);
            background: linear-gradient(45deg, var(--card-2), var(--accent-soft));
            color: var(--text);
            box-shadow: var(--glow);
            transition: all 0.3s ease;
            padding: 15px 20px !important;
            font-size: 16px !important;
            min-height: 50px !important;
        }

        div[data-testid="stChatInput"] textarea:focus {
            box-shadow: 0 0 30px var(--accent);
            transform: scale(1.02);
        }

        div[data-testid="stChatInput"] textarea::placeholder {
            color: var(--muted);
        }

        /* Helper text */
        .moon-helper {
            color: var(--muted);
            font-size: 0.95rem;
            margin: 0.5rem 0;
            text-align: center;
        }

        /* Code blocks */
        section[data-testid="stSidebar"] pre {
            background: var(--card-2);
            color: var(--text);
            border: 1px solid var(--border);
            border-radius: 15px;
            box-shadow: var(--glow);
        }

        /* Email guide */
        .moon-email-guide {
            margin: 0.2rem 0;
            padding-left: 1.5rem;
            color: var(--text);
        }
        .moon-email-guide li {
            margin-bottom: 0.5rem;
            color: var(--text);
        }

        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            background: rgba(26, 26, 46, 0.8);
            border-radius: 15px;
            padding: 0.5rem;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            transition: all 0.3s ease;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: var(--accent);
            color: white;
            box-shadow: var(--glow);
        }

        /* Quick prompt buttons */
        .stButton button {
            background: linear-gradient(45deg, var(--card-2), var(--accent-soft));
            border: 1px solid var(--border);
            color: var(--text);
            transition: all 0.3s ease;
        }

        /* Floating scroll to bottom button */
        #scroll-to-bottom {
            position: fixed;
            bottom: 120px;
            right: 20px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 20px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0, 212, 255, 0.5);
            display: none;
            z-index: 999;
            transition: all 0.3s ease;
        }

        #scroll-to-bottom:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(0, 212, 255, 0.7);
        }
    </style>
    <button id="scroll-to-bottom" title="Scroll to latest">⬇️</button>
    """,
    unsafe_allow_html=True,
)

# ───────────────────────────────────────────────
# Session state helpers
# ───────────────────────────────────────────────
INITIAL_MESSAGE = {
    "role": "assistant",
    "content": "🚀 **Greetings!** I'm MoonGPT, your futuristic AI assistant for Chandramouli Das. Ask me about his skills, experience, or draft professional emails. Let's explore the cosmos of knowledge! 🌌",
}

pdf_bytes = PDF_PATH.read_bytes() if PDF_PATH.exists() else None


def reset_chat():
    st.session_state["messages"] = [INITIAL_MESSAGE]
    st.session_state["queue"] = []


def enqueue_prompt(text: str):
    st.session_state.setdefault("queue", []).append(text)

# ───────────────────────────────────────────────
# Sidebar
# ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚀 MoonGPT")
    st.markdown(
        "<div class='moon-muted'>Personal assistant for <b>Chandramouli Das</b></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='moon-side-card'>", unsafe_allow_html=True)
    st.markdown("<div class='moon-card-title'>⚙️ Actions</div>", unsafe_allow_html=True)
    st.button("🧹 Clear Chat", use_container_width=True, on_click=reset_chat)
    st.caption("Clean slate for a new conversation.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Resume download
    st.markdown("<div class='moon-side-card'>", unsafe_allow_html=True)
    st.markdown("<div class='moon-card-title'>📄 Resume</div>", unsafe_allow_html=True)
    if pdf_bytes:
        st.download_button(
            "Download Résumé",
            pdf_bytes,
            file_name=PDF_PATH.name,
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.error("Résumé PDF missing")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 📚 Quick Prompts")
    samples = [
        "What are Chandramouli’s key skills?",
        "Tell me about his project experience",
        "What is his current role?",
        "Write a mail to my Boss for an Update",
        "Book an appointment with my Boss",
    ]
    for q in samples:
        st.button(q, key=f"sb_{q}", use_container_width=True, on_click=enqueue_prompt, args=(q,))

    st.markdown("### ✉️ Email Guide")
    st.markdown("<div class='moon-side-card'>", unsafe_allow_html=True)
    st.markdown(
        "<ol class='moon-email-guide'>"
        "<li>Ask me to <i>write a mail/email</i> with your name, company, and contact.</li>"
        "<li>Review the draft I provide.</li>"
        "<li>Add your email ID and phone number as contact details.</li>"
        "<li>Reply <b>Ok send it</b> — I’ll forward it to <b>chandramoulidas39@gmail.com</b>.</li>"
        "</ol>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ───────────────────────────────────────────────
# Title & intro
# ───────────────────────────────────────────────
st.markdown(
    """
    <div class="moon-header">
        <div style="font-size:1.65rem;font-weight:700;">🚀 MoonGPT</div>
        <div class="moon-subtitle">
            Futuristic AI Assistant for Chandramouli Das — Navigate skills, experience, projects, and email hyperspace.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='moon-helper'>Tip: try a quick prompt below or ask a specific question.</div>",
    unsafe_allow_html=True,
)

# Main tabs
chat_tab, resume_tab = st.tabs(["💬 Chat", "📥 Download Resume"])

# ───────────────────────────────────────────────
# Session state
# ───────────────────────────────────────────────
st.session_state.setdefault("messages", [INITIAL_MESSAGE])
st.session_state.setdefault("queue", [])

# helper to call backend

def backend_call(conv):
    try:
        r = requests.post(BACKEND_URL, json={"conversation": conv}, timeout=30)
        return (
            r.json().get("answer", "No response.")
            if r.status_code == 200
            else f"API error: {r.status_code}"
        )
    except Exception as e:
        return f"❌ {e}"

# ───────────────────────────────────────────────
# Process one queued prompt
# ───────────────────────────────────────────────
if st.session_state["queue"]:
    txt = st.session_state["queue"].pop(0)
    st.session_state["messages"].append({"role":"user","content":txt})
    # Typing indicator for queued
    with st.chat_message("assistant"):
        temp_placeholder = st.empty()
        temp_placeholder.markdown("🤖 *MoonGPT is typing...* <span class='typing'>▌</span>", unsafe_allow_html=True)
        time.sleep(1.5)
        ans = backend_call(st.session_state["messages"])
        temp_placeholder.markdown(ans)
        
        # Show download button if download mentioned
        if "download" in ans.lower() and pdf_bytes:
            st.download_button(
                "⬇️ Download Resume",
                pdf_bytes,
                file_name="Chandramouli_Das_Resume.pdf",
                mime="application/pdf",
                key="queued_download"
            )
    st.session_state["messages"].append({"role":"assistant","content":ans})
    st.rerun()

with chat_tab:
    # Quick prompts in main area (faster than scrolling the sidebar)
    quick_prompts = [
        "Summarize his profile in 5 bullets",
        "Top 5 skills with examples",
        "Best projects to highlight",
        "Draft a recruiter outreach email",
    ]
    qp_cols = st.columns(len(quick_prompts))
    for col, prompt_text in zip(qp_cols, quick_prompts):
        with col:
            st.button(
                prompt_text,
                key=f"main_{prompt_text}",
                use_container_width=True,
                on_click=enqueue_prompt,
                args=(prompt_text,),
            )

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

        # Typing indicator with blinking cursor
        with st.chat_message("assistant"):
            typing_placeholder = st.empty()
            typing_placeholder.markdown("🤖 *MoonGPT is typing...* <span class='typing'>▌</span>", unsafe_allow_html=True)
            time.sleep(1.5)  # Wait for typing effect

            resp = backend_call(tmp_conv)

            typing_placeholder.markdown(resp)

            # If download mentioned, show download button
            if "download" in resp.lower() and pdf_bytes:
                st.download_button(
                    "⬇️ Download Resume",
                    pdf_bytes,
                    file_name="Chandramouli_Das_Resume.pdf",
                    mime="application/pdf",
                    key="chat_download"
                )

        # persist and rerun
        st.session_state["messages"].extend([
            {"role":"user","content":prompt},
            {"role":"assistant","content":resp}
        ])
        st.rerun()

with resume_tab:
    st.markdown("### 📄 Resume Download")
    st.markdown(
        "<div class='moon-side-card'>"
        "<div class='moon-card-title'>Get the latest résumé</div>"
        "<div class='moon-muted'>No need to open the sidebar—download it right here.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    if pdf_bytes:
        st.download_button(
            "⬇️ Download Résumé (PDF)",
            pdf_bytes,
            file_name=PDF_PATH.name,
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.error("Résumé PDF missing")

# Auto-scroll script
components.html(
    """
    <script>
        const scrollButton = document.getElementById('scroll-to-bottom');
        let isAtBottom = true;

        function isNearBottom() {
            return window.scrollY + window.innerHeight >= document.body.scrollHeight - 100;
        }

        function scrollToBottom() {
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
            isAtBottom = true;
            if (scrollButton) scrollButton.style.display = 'none';
        }

        function checkScroll() {
            if (isNearBottom()) {
                isAtBottom = true;
                if (scrollButton) scrollButton.style.display = 'none';
            } else {
                isAtBottom = false;
                if (scrollButton) scrollButton.style.display = 'block';
            }
        }

        // Initial check
        setTimeout(checkScroll, 100);

        // On scroll, check position
        window.addEventListener('scroll', checkScroll);

        // On new content, auto-scroll if at bottom
        const observer = new MutationObserver(() => {
            if (isAtBottom) {
                setTimeout(scrollToBottom, 200);  // Delay to ensure content is rendered
            } else {
                if (scrollButton) scrollButton.style.display = 'block';
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });

        // Button click
        if (scrollButton) {
            scrollButton.addEventListener('click', scrollToBottom);
        }
    </script>
    """,
    height=0,
)
