# MoonGPT

MoonGPT is a professional, résumé-grounded portfolio assistant for Chandramouli
Das. It combines a responsive Next.js interface with a FastAPI API, OpenAI
models, and a FAISS similarity index.

## Product stack

- Next.js 16, React 19, and TypeScript
- Framer Motion and Lucide icons
- FastAPI and Pydantic
- OpenAI Responses API and embeddings
- Heading-aware hybrid retrieval (semantic + lexical) with a cached FAISS index
- Gmail SMTP for confirmed email drafts

## Requirements

- Python 3.14
- Node.js 20.19+, 22.13+, or 24+
- An OpenAI API key

The project currently runs on Node.js 23, but an active LTS release is
recommended for long-term development.

## Configuration

Create or update `.env` in the project root:

```dotenv
OPENAI_API_KEY=your_openai_api_key
PDF_CV_PATH=Resume.pdf
DOCX_PATH=Document.docx
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
EMAIL_RECEIVER=your_email@gmail.com

# Private question analytics
QUESTION_LOGGING_ENABLED=true
QUESTION_DATABASE_PATH=data/questions.db
QUESTION_RETENTION_DAYS=90
ADMIN_USERNAME=admin
ADMIN_PASSWORD=replace_with_a_long_random_password
FRONTEND_ORIGINS=https://your-domain.com
```

The optional model settings are:

```dotenv
CHAT_MODEL=gpt-5.6-terra
EMBEDDING_MODEL=text-embedding-3-small
```

`gpt-5.6-terra` is the quality/cost-balanced default for the portfolio chat.
You can override `CHAT_MODEL` without changing code. The first request after
changing `Document.docx` or `EMBEDDING_MODEL` rebuilds `.cache/rag`; later
restarts load that index from disk.

## First-time setup

```bash
cd "/Users/chandramoulidas/Desktop/Work/Resume"

/opt/homebrew/bin/python3.14 -m venv moon-gpt
source moon-gpt/bin/activate
python -m pip install -r requirements.txt

cd frontend
npm install
cd ..
```

## Run locally

Start both services with one command:

```bash
cd "/Users/chandramoulidas/Desktop/Work/Resume"
source moon-gpt/bin/activate
python run.py
```

Local addresses:

- Web interface: <http://127.0.0.1:3000>
- API documentation: <http://127.0.0.1:8000/docs>
- API health: <http://127.0.0.1:8000/api/health>
- Private question dashboard: <http://127.0.0.1:3000/admin/questions>

Press `Ctrl+C` to stop both services.

## Question analytics in production

MoonGPT records anonymized visitor questions and their LLM answers through a
background queue, so database writes do not block chat responses. Email addresses and phone numbers
are redacted, structured recruiter email-intake messages are excluded, session
IDs are irreversibly hashed, and records older than `QUESTION_RETENTION_DAYS`
are removed when the service starts.

Set `QUESTION_DATABASE_PATH` to a persistent mounted volume in production. For
example, if the host mounts `/data`, use:

```dotenv
QUESTION_DATABASE_PATH=/data/questions.db
```

Without a persistent volume, platforms with ephemeral filesystems can erase the
analytics database during a deployment or restart. Always serve the admin page
over HTTPS in production because it uses HTTP Basic authentication.

Open `/admin/questions` and sign in with `ADMIN_USERNAME` and `ADMIN_PASSWORD`.
The dashboard provides totals, topic filters, question-and-answer review, search,
and CSV export. Repeated anonymized questions are held in an in-memory cache and supplied
as topic hints during generation without another database read or LLM request.

## Run services separately

Backend:

```bash
source moon-gpt/bin/activate
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run dev
```

## Verification

```bash
source moon-gpt/bin/activate
python -m py_compile main.py run.py backend/rag.py
python -m unittest discover -s tests -v
python -m pip check

cd frontend
npm run lint
npm run build
npm audit --omit=dev
```
