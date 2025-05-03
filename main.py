import os, re, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import faiss, json
import numpy as np
import docx  # pip install python-docx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import openai

'''
with open("config.json") as f:
    cfg = json.load(f)

openai.api_key   = cfg["openai_api_key"]
PDF_PATH         = cfg["pdf_cv_path"]
DOCX_PATH        = cfg["docx_path"]
EMAIL_SENDER     = cfg["email_sender"]
EMAIL_PASSWORD   = cfg["email_password"]
EMAIL_RECEIVER   = cfg["email_receiver"]

'''

# === Load .env locally if available ===
load_dotenv()

# === Config from ENV ===
openai.api_key   = os.getenv("openai_api_key")
PDF_PATH         = os.getenv("pdf_cv_path", "Resume.pdf")
DOCX_PATH        = os.getenv("docx_path",  "Document.docx")
EMAIL_SENDER     = os.getenv("email_sender")
EMAIL_PASSWORD   = os.getenv("email_password")
EMAIL_RECEIVER   = os.getenv("email_receiver", EMAIL_SENDER)

# === FastAPI setup ===
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    conversation: list

# === Helpers ===
def load_docx(path: str) -> str:
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def get_embedding(txt: str) -> np.ndarray:
    resp = openai.Embedding.create(input=txt, model="text-embedding-ada-002")
    return np.array(resp["data"][0]["embedding"], dtype=np.float32)

def chunk(text: str, size: int = 500, overlap: int = 100):
    words = text.split()
    out = []
    i = 0
    while i < len(words):
        out.append(" ".join(words[i:i + size]))
        i += size - overlap
    return out

def build_index(chunks):
    mat = np.vstack([get_embedding(c) for c in chunks])
    idx = faiss.IndexFlatL2(mat.shape[1]); idx.add(mat)
    return idx, chunks

def retrieve(q: str, idx, chunks, k: int = 3):
    resp = openai.Embedding.create(input=q, model="text-embedding-ada-002")
    qemb = np.array(resp["data"][0]["embedding"], dtype=np.float32)
    D, I = idx.search(np.array([qemb]), k)
    return [chunks[i] for i in I[0]]

def send_email(subj: str, body: str):
    msg = MIMEMultipart()
    msg["From"], msg["To"], msg["Subject"] = EMAIL_SENDER, EMAIL_RECEIVER, subj
    msg.attach(MIMEText(body, "plain"))
    s = smtplib.SMTP("smtp.gmail.com", 587)
    s.starttls()
    s.login(EMAIL_SENDER, EMAIL_PASSWORD)
    s.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
    s.quit()

# === System prompt ===
SYSTEM_PROMPT = (
    "You are MoonGPT, Chandramouli Das's personal assistant. "
    "Answer strictly using information from the provided resume context. "
    "Use bullet points where appropriate. If more details are required finish with 'Do you want to know more?'."
)

# === Build FAISS index once ===
print("📄 Indexing DOCX:", DOCX_PATH)
resume_text = load_docx(DOCX_PATH)
faiss_index, all_chunks = build_index(chunk(resume_text))
print("✅ Index ready")

# === Email draft buffer ===
last_subj, last_body = "", ""

# === Main endpoint ===
@app.post("/api/chat")
def chat(req: ChatRequest):
    global last_subj, last_body
    conv = req.conversation.copy()
    user_query = next((m["content"] for m in reversed(conv) if m.get("role")=="user"), "")
    uq = user_query.lower()

    # Resume download
    if any(w in uq for w in ("cv","resume")):
        return FileResponse(PDF_PATH, media_type="application/pdf", filename="Chandramouli_Das_Resume.pdf")

    write_mail = ("mail" in uq or "email" in uq) and any(x in uq for x in ("write","draft","compose"))
    confirm    = "ok send" in uq or ("send" in uq and any(x in uq for x in ("mail","email","it")))

    if write_mail:
        conv.insert(1, {
            "role":"system",
            "content":"Write a professional email. Start with 'Subject:' then the body."
        })

    if not conv or conv[0].get("role")!="system":
        conv.insert(0, {"role":"system","content":SYSTEM_PROMPT})

    context = "\n\n".join(retrieve(uq, faiss_index, all_chunks)) if uq else ""
    conv.insert(1, {"role":"system", "content":f"Resume Context:\n{context}"})

    # Chat completion (old interface)
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=conv,
        temperature=0.7,
        max_tokens=300
    )
    answer = resp.choices[0].message.content

    # Buffer or send email
    if write_mail:
        subj, body = "", ""
        for line in answer.splitlines():
            if line.lower().startswith("subject:"):
                subj=line.split(":",1)[1].strip()
            else:
                body+=line+"\n"
        sender_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", user_query)
        body+=f"\n\n---\nSent by: {sender_match.group(0) if sender_match else 'Unknown'}"
        last_subj, last_body = subj, body
        answer += "\n\n📨 Draft saved — reply 'Ok send it' to email Chandramouli."
    elif confirm and last_subj and last_body:
        send_email(last_subj, last_body)
        answer = "📩 Email sent successfully to Chandramouli!"

    return {"answer": answer}