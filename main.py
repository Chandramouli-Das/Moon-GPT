import json, os, re, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import openai
import faiss
import numpy as np
import docx  # pip install python-docx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# === load config ===
'''
with open("config.json", "r") as f:
    cfg = json.load(f)

openai.api_key   = cfg.get("openai_api_key")
DOCX_PATH        = cfg.get("docx_path",  "Document.docx")      # Word file used for RAG
PDF_PATH         = cfg.get("pdf_cv_path", "Resume.pdf")        # just for download
email_sender     = cfg.get("email_sender")
email_password   = cfg.get("email_password")
email_receiver   = cfg.get("email_receiver", "chandramoulidas39@gmail.com")
'''

# === Load from Environment ===
openai.api_key = os.getenv("openai_api_key")
pdf_cv_path = "Resume.pdf"
docx_path = "Document.docx"
email_sender = os.getenv("email_sender")
email_password = os.getenv("email_password")
email_receiver = os.getenv("email_receiver")


# === fastapi app ===
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    conversation: list  # list[{role, content}]

# === helpers ===

def load_docx(path: str) -> str:
    """Return all paragraph text joined by newlines."""
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def get_embedding(txt: str) -> np.ndarray:
    emb = openai.Embedding.create(model="text-embedding-ada-002", input=txt)
    return np.array(emb["data"][0]["embedding"], dtype=np.float32)


def chunk(text: str, size: int = 300):
    words, buf, out = text.split(), [], []
    for w in words:
        buf.append(w)
        if len(buf) >= size:
            out.append(" ".join(buf)); buf = []
    if buf:
        out.append(" ".join(buf))
    return out


def build_index(chunks):
    mat = np.vstack([get_embedding(c) for c in chunks])
    idx = faiss.IndexFlatL2(mat.shape[1]); idx.add(mat)
    return idx, chunks


def retrieve(q: str, idx, chunks, k: int = 3):
    _, I = idx.search(np.array([get_embedding(q)]), k)
    return [chunks[i] for i in I[0]]


def send_email(subj: str, body: str):
    msg = MIMEMultipart(); msg["From"], msg["To"], msg["Subject"] = email_sender, email_receiver, subj
    msg.attach(MIMEText(body, "plain"))
    s = smtplib.SMTP("smtp.gmail.com", 587); s.starttls(); s.login(email_sender, email_password)
    s.sendmail(email_sender, email_receiver, msg.as_string()); s.quit()

# === system prompt ===
SYSTEM_PROMPT = (
    "You are MoonGPT, Chandramouli Das's personal assistant. "
    "Answer strictly using information from the provided resume context. "
    "Use bullet points where appropriate. If more details are required finish with 'Do you want to know more?'."
)

# === build FAISS index once ===
print("Indexing", DOCX_PATH)
resume_text                = load_docx(DOCX_PATH)
faiss_index, all_chunks    = build_index(chunk(resume_text))
print("Index ready ✔")

# === email draft buffer ===
last_subj, last_body = "", ""

# === endpoint ===
@app.post("/api/chat")
def chat(req: ChatRequest):
    global last_subj, last_body
    conv = req.conversation.copy()

    user_query = next((m["content"] for m in reversed(conv) if m.get("role") == "user"), "")
    uq = user_query.lower()

    # resume download
    if any(t in uq for t in ["cv", "resume"]):
        return FileResponse(PDF_PATH, media_type="application/pdf", filename="Chandramouli_Das_Resume.pdf")

    write_mail = ("mail" in uq or "email" in uq) and any(x in uq for x in ["write", "draft", "compose"])
    confirm    = "ok send" in uq or ("send" in uq and any(x in uq for x in ["mail", "email", "it"]))

    if write_mail:
        conv.insert(1, {"role": "system", "content": "Write a professional email per user's request. Begin with 'Subject:' then the body."})

    # prepend context
    if not conv or conv[0].get("role") != "system":
        conv.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    context = "\n\n".join(retrieve(uq, faiss_index, all_chunks)) if uq else ""
    conv.insert(1, {"role": "system", "content": f"Resume Context:\n{context}"})

    # get answer
    answer = openai.ChatCompletion.create(model="gpt-4o-mini", messages=conv, temperature=0.7, max_tokens=300)["choices"][0]["message"]["content"]

    # buffer draft
    if write_mail:
        subj, body = "", ""
        for line in answer.splitlines():
            if line.lower().startswith("subject:"):
                subj = line.split(":",1)[1].strip()
            else:
                body += line + "\n"
        sender = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", user_query)
        body += f"\n\n---\nSent by: {sender.group(0) if sender else 'Unknown'}"
        last_subj, last_body = subj, body
        answer += "\n\n📨 Draft saved — reply 'Ok send it' to email Chandramouli."

    elif confirm and last_subj and last_body:
        send_email(last_subj, last_body)
        answer = "📩 Email sent successfully to Chandramouli!"

    return {"answer": answer}
