import os
import openai
import faiss
import numpy as np
from dotenv import load_dotenv
from docx import Document  # (Keep this if you still use DOCX elsewhere)
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2  # Make sure to install PyPDF2 if you haven't already

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Add CORS middleware to allow requests from any origin (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change "*" to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the request model, expecting a conversation (list of messages)
class ChatRequest(BaseModel):
    conversation: list

# Function to extract text from a PDF file using PyPDF2
def load_pdf(filename: str) -> str:
    full_text = []
    with open(filename, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
    return "\n".join(full_text)

# Function to generate embeddings using OpenAI's embedding model
def get_embedding(text: str) -> np.ndarray:
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    embedding = response["data"][0]["embedding"]
    return np.array(embedding, dtype=np.float32)

# Naively split text into chunks based on word count
def chunk_text(text: str, max_tokens: int = 300) -> list:
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    for word in words:
        current_chunk.append(word)
        current_length += 1
        if current_length >= max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

# Build a FAISS index from a list of text chunks
def build_faiss_index(chunks: list) -> (faiss.IndexFlatL2, list):
    embeddings = [get_embedding(chunk) for chunk in chunks]
    embeddings_np = np.vstack(embeddings)
    dim = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings_np)
    return index, chunks

# Retrieve the top-k most similar chunks for a given query
def retrieve(query: str, index, chunks, top_k: int = 3) -> list:
    query_embedding = get_embedding(query)
    query_embedding = np.array([query_embedding])
    distances, indices = index.search(query_embedding, top_k)
    retrieved_chunks = [chunks[i] for i in indices[0]]
    return retrieved_chunks

# Extra instructions for the system message
EXTRA_INSTRUCTIONS = (
    "You are an expert assistant providing detailed and accurate information "
    "based solely on the provided document context. "
    "Please answer concisely, using bullet points for lists, and if more detail is needed, end with 'Do you want to know more?'."
)

# Define the PDF CV file path (update as needed)
pdf_cv_path = "/Users/chandramoulidas/Desktop/Resume/Resume.pdf"

# Load the PDF text for context extraction if needed
print("Loading PDF document...")
document_text = load_pdf(pdf_cv_path)
print("Processing document into chunks...")
chunks = chunk_text(document_text, max_tokens=300)
print("Building the retrieval index...")
faiss_index, all_chunks = build_faiss_index(chunks)
print("Index built successfully!")

@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    # Copy the conversation from the request
    conversation = request.conversation.copy()

    # Identify the user's most recent query (search backwards)
    user_query = None
    for msg in reversed(conversation):
        if msg.get("role") == "user":
            user_query = msg.get("content", "")
            break

    # Special case: If the user's query contains "cv" or "resume", return the PDF file directly.
    if user_query and ("cv" in user_query.lower() or "resume" in user_query.lower()):
        return FileResponse(
            path=pdf_cv_path,
            media_type="application/pdf",
            filename="MyCV.pdf"
        )

    # Retrieve document context based on the latest user query
    retrieved_context = []
    if user_query:
        retrieved_context = retrieve(user_query, faiss_index, all_chunks, top_k=3)
    context_text = "\n\n".join(retrieved_context)

    # Ensure conversation starts with a system message with instructions
    if not conversation or conversation[0].get("role") != "system":
        conversation.insert(0, {
            "role": "system",
            "content": EXTRA_INSTRUCTIONS
        })
    
    # Insert a system message with the retrieved document context
    conversation.insert(1, {
        "role": "system",
        "content": f"Relevant Document Context:\n{context_text}"
    })

    # Call the OpenAI ChatCompletion API with the full conversation
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # Adjust model name if necessary
        messages=conversation,
        temperature=0.7,
        max_tokens=300
    )
    answer = response['choices'][0]['message']['content']
    return {"answer": answer}