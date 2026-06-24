# 📐 NCERT Maths Analyzer & Resource Finder

LIVE DEMO : [youtube-topic-link-rag-ai.streamlit.app](https://youtube-topic-link-rag-ai.streamlit.app/)

A Streamlit app that analyzes CBSE Class 10 NCERT Mathematics PDFs, identifies key topics, and curates YouTube tutorial videos for each topic. Also includes a RAG-powered Q&A mode where students can ask questions and get answers grounded in the textbook.

---

## Features

| Mode                  | What it does                                                                         |
| --------------------- | ------------------------------------------------------------------------------------ |
| 📄**Auto Mode** | Upload PDF → LLaMA 3.1 extracts topics → YouTube videos fetched per topic          |
| 💬**Ask Mode**  | Type a topic/question → FAISS searches PDF → LLaMA answers → YouTube videos shown |

---

## Tech Stack

| Component    | Tool                                                               |
| ------------ | ------------------------------------------------------------------ |
| PDF Loading  | LangChain`PyPDFLoader`                                           |
| LLM          | `meta-llama/Llama-3.1-8B-Instruct` via HuggingFace Inference API |
| Embeddings   | `sentence-transformers/all-MiniLM-L6-v2` (free, local)           |
| Vector Store | FAISS (in-memory)                                                  |
| Video Search | YouTube Data API v3                                                |
| UI           | Streamlit                                                          |
| Deployment   | Streamlit Cloud                                                    |

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ncert-maths-analyzer.git
cd ncert-maths-analyzer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get API Keys

**HuggingFace Token (free)**

1. Go to https://huggingface.co/settings/tokens
2. Create new token → enable **"Make calls to Inference Providers"** permission
3. Request LLaMA access at https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct

**YouTube Data API v3 Key (free)**

1. Go to https://console.cloud.google.com → create a project
2. Enable "YouTube Data API v3" → Credentials → Create API Key
3. Free quota: 10,000 units/day = ~100 searches/day (each search = 100 units)

### 4. Create .env file

```bash
cp .env.example .env
# Edit .env and paste your keys — keys are NEVER shown in the UI
```

### 5. Run locally

```bash
streamlit run app.py
```

---

## Deploying to Streamlit Cloud (free shareable link)

1. Push code to GitHub (`.gitignore` excludes `.env`)
2. Go to https://share.streamlit.io → New app → select repo → `app.py`
3. Advanced settings → Secrets → paste:

```toml
HUGGINGFACEHUB_API_TOKEN = "hf_your_token_here"
YOUTUBE_API_KEY = "your_youtube_key_here"
```

4. Deploy → get public link in ~2 minutes

---

## Project Structure

```
ncert-maths-analyzer/
├── app.py                    # Streamlit UI (API keys read from .env only)
├── pdf_loader.py             # PDF loading + FAISS vector store
├── topic_extractor.py        # LLaMA topic extraction + RAG answering (cached)
├── youtube_fetcher.py        # YouTube Data API (cached per topic)
├── requirements.txt
├── sample_output.json        # Pre-generated sample output for demo
├── .env.example              # API key template
├── .gitignore
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

---

## Performance & Quota Notes

- **Caching**: `@st.cache_data` on `extract_topics()` and `fetch_videos()` — same PDF/topic never hits the API twice in a session
- **Token limit**: `max_new_tokens=512` keeps HF inference fast and within free quota
- **YouTube quota**: 15 topics × 2 videos = 15 API calls = 1,500 units/day (well within 10,000 free limit)
- **YouTube relevance**: improved prompt extracts specific NCERT concept names (e.g. "Euclid division lemma" not "explain the topic")

---

## Sample Output

```json
[
  {
    "topic": "Euclid's Division Lemma",
    "chapter": "Real Numbers",
    "videos": [
      {
        "title": "Euclid's Division Algorithm Class 10 | Vedantu",
        "url": "https://www.youtube.com/watch?v=...",
        "channel": "Vedantu Class 9 & 10"
      }
    ]
  }
]
```
