<div align="center">

# ScholarMind

**Interrogate any research paper through plain English conversation**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-black?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1.3.2-teal?logo=chainlink&logoColor=white)](https://www.langchain.com/)
[![Groq](https://img.shields.io/badge/Groq-llama--3.1--8b-orange)](https://console.groq.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-1.5.9-purple)](https://www.trychroma.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## Live Demo

**[https://scholarmind-iaxr.onrender.com](https://scholarmind-iaxr.onrender.com)**

---

## What is ScholarMind?

ScholarMind is an AI research assistant built for students and researchers. Upload any academic PDF. A thesis, journal paper, or textbook chapter, and ask questions about it in plain English. Every answer cites the exact page it came from.

ChatGPT hallucinates when asked about specific documents because it has no access to them. ScholarMind answers only from what is in your PDF. If the answer is not there, it says so.

```
> Upload: deodorant_study.pdf

You: What is the result of this study?

ScholarMind: The study found no significant difference in the performance
             of the researchers' innovation and commercially available
             deodorant in terms of effectiveness in fighting body odor,
             effects on skin, and comfort.

             Page 48  · Chapter 5 Presentation, Analysis, and
             Interpretation of Data. This chapter deals with the summary
             of findings, conclusions, and recommendations...

             Page 7   · Hypothesis H0: There is no significant difference
             in the performance of the researchers' innovation and
             commercially available product...

You: What were the weighted mean scores for body odor effectiveness?

ScholarMind: Statement 1 scored a WAM of 3.50 (the mint helped me stay
             cool), Statement 4 scored 3.42 (no foul odor leaked),
             Statements 3 and 5 scored 3.33, and Statement 2 scored 3.25
             (the deodorant eliminated body odor rather than masking it).
             The overall WAM for this category was 3.37, indicating strong
             agreement across respondents.

             Page 38  · 2.2 Effectiveness in Fighting Body Odor...
             Page 39  · the product's effectiveness in fighting body odor...
```

---

## Features

**Retrieval**
- Parent document retrieval: small child chunks (400 tokens) for precise matching, full parent pages returned to the LLM for context
- Per-document isolated vector stores where multiple PDFs stay separate, no cross-document bleed
- Conversation memory across follow-up questions within the same session

**Interface**
- Terminal-themed dark UI, no JavaScript framework
- Upload via drag-and-drop or file picker
- Progress bar during PDF processing
- Page-level source citations on every answer
- Document switcher in the sidebar. Click to change active document mid-session

**API**
- Clean REST endpoints for upload, query, remove, and reset
- JSON responses with answer and sources array
- 16 MB PDF size limit, PDF-only validation

---

## How It Works

ScholarMind uses Retrieval-Augmented Generation (RAG) with a parent document retrieval strategy.

**On upload:**

1. PyPDF extracts text page by page, preserving page number metadata
2. Each page is split into 400-token child chunks with 50-token overlap
3. Child chunks are embedded using `all-MiniLM-L6-v2` via SentenceTransformers
4. Embeddings are stored in an in-memory ChromaDB instance
5. Full parent pages are stored alongside in an `InMemoryStore`

**On query:**

1. The question is embedded and matched against child chunks
2. The parent pages containing those chunks are retrieved
3. Full page content plus conversation history is passed to the Groq LLM
4. The model answers using only the retrieved pages

**Why parent retrieval matters:**

Standard chunk retrieval returns whichever fragments score highest against the query. For academic papers, a question about Chapter 5 findings might match a chunk from the methodology section that shares vocabulary. The actual results table, formatted as numbered rows, scores lower because its token distribution looks different.

The parent retriever uses small chunks for matching precision but returns the full page. For a 50-page thesis, this is the difference between retrieving the hypothesis statement from page 7 and retrieving the actual data tables from pages 38 through 43.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq (llama-3.1-8b-instant) |
| Orchestration | LangChain Classic 1.0.7 |
| Embeddings | SentenceTransformers (all-MiniLM-L6-v2) |
| Vector Store | ChromaDB 1.5.9 |
| Retrieval | ParentDocumentRetriever |
| PDF Parsing | PyPDF 6.12.2 |
| Backend | Flask 3.1.3 |
| Frontend | Vanilla HTML, CSS, JavaScript |
| Package Manager | uv |

---

## Project Structure

```
scholarmind/
├── app/
│   ├── app.py                  # Flask API. upload, ask, remove, reset routes
│   ├── templates/
│   │   └── index.html          # Main UI
│   └── static/
│       ├── style.css           # Terminal-themed styles
│       └── script.js           # Upload handler, chat logic, document switcher
├── src/
│   ├── document_processor.py   # PDF loading, page splitting, metadata tagging
│   ├── vector_store.py         # ChromaDB setup, parent retriever construction
│   ├── qa_chain.py             # LLM chain, custom prompt, conversation memory
│   └── logger.py               # Timestamped file-based logging
├── data/
│   └── uploads/                # Temporary PDF storage
├── vectorstore/                # ChromaDB on-disk persistence
├── notebooks/
│   └── 01_pipeline_test.ipynb  # End-to-end pipeline validation
├── .env                        # GROQ_API_KEY (not committed)
├── requirements.txt
├── Procfile
└── README.md
```

---

## Local Setup

**Requirements:** Python 3.11+, uv

```bash
git clone https://github.com/yourusername/scholarmind.git
cd scholarmind

uv venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

uv pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free Groq API key at [console.groq.com](https://console.groq.com). No credit card required.

Run the app:

```bash
python app/app.py
```

Open `http://127.0.0.1:5000`.

---

## API Reference

### `POST /upload`

Upload a PDF for processing. Each document gets its own isolated vector store and conversation memory.

**Request:** `multipart/form-data` with a `file` field. PDF only, max 16 MB.

**Response:**
```json
{
  "message": "Document processed successfully",
  "chunks": 142,
  "filename": "paper.pdf"
}
```

---

### `POST /ask`

Ask a question about a loaded document.

**Request:**
```json
{
  "question": "What datasets were used for evaluation?",
  "filename": "paper.pdf"
}
```

**Response:**
```json
{
  "answer": "The authors evaluated on CIFAR-10 and a custom medical imaging dataset described in Section 4.2.",
  "sources": [
    {
      "page": 7,
      "excerpt": "...evaluated their approach on three datasets — CIFAR-10, ImageNet..."
    }
  ]
}
```

---

### `POST /remove`

Remove a document, its vector store, and its uploaded file.

**Request:**
```json
{ "filename": "paper.pdf" }
```

---

### `POST /reset`

Clear all loaded documents and conversation memory for the current session.

---

## Known Limitations

- **No persistent sessions.** The in-memory document store resets on server restart. Users need to re-upload documents after a restart.
- **Text-only PDFs.** Scanned documents without an OCR layer extract poorly or not at all.
- **Single-user.** No authentication layer. On a shared server, all users share the same document pool.
- **Groq rate limits.** The free tier caps requests per minute. Under heavy use, responses may queue or fail.

---

## Roadmap

- Persistent storage with SQLite and disk-based ChromaDB
- User authentication and per-user document isolation
- Multi-document querying across an entire paper collection
- Conversation export as PDF
- Automatic 3-sentence summary on upload

---

## Development Notes

Delete the vectorstore directory before re-uploading a PDF during development to avoid stale chunk conflicts:

```bash
# Windows
rd /s /q vectorstore && mkdir vectorstore

# macOS / Linux
rm -rf vectorstore && mkdir vectorstore
```

The development build in `app.py` wipes the vectorstore on every Flask restart automatically. Remove that block before deploying to production.

---

## Author

| Name | Role |
|---|---|
| Gil Bryan Guillermo | Developer |

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Disclaimer

ScholarMind is a research and educational tool. It answers from the content of uploaded documents only and does not browse the internet or access external knowledge bases. Accuracy depends on the quality of the source PDF and the retrieved context.
