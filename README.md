# Interview Chatbot — Parmesh Lata

An AI-powered interview chatbot that represents Parmesh in job interviews,
built with RAG, ChromaDB, and HuggingFace LLMs.

## Setup

```bash
git clone https://github.com/yourname/interview-chatbot
cd interview-chatbot
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
python app.py
```

## Stack
- LLM: Kimi-K2 via HuggingFace Inference API
- Embeddings: ChromaDB default (all-MiniLM-L6-v2)
- Vector Store: ChromaDB
- UI: Gradio
- Notifications: Pushover