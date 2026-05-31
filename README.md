# DeepFetch AI — Document Intelligence Engine

A multi-agent document intelligence system that lets you ask questions across large document collections and get accurate, cited answers — instead of manually searching hundreds of pages.

## Architecture

```
User Query
    │
    ▼
┌──────────────────┐
│ Query Understanding│  ← Classifies intent, reformulates query
└────────┬─────────┘
         ▼
┌──────────────────┐
│    Retrieval      │  ← FAISS vector search + reranking
└────────┬─────────┘
         ▼
┌──────────────────┐
│    Reasoning      │  ← AWS Bedrock LLM generates cited answer
└────────┬─────────┘
         ▼
┌──────────────────┐
│   Validation      │  ← Hallucination check + confidence scoring
└────────┬─────────┘
         ▼
    Final Answer (with citations + confidence score)
```

## 5-Agent Pipeline

| Agent | Responsibility |
|-------|---------------|
| **Ingestion** | Load PDFs/DOCX/TXT → chunk → embed → store in FAISS |
| **Query Understanding** | Classify intent, expand/reformulate query for better retrieval |
| **Retrieval** | Search FAISS index, rerank results, return top chunks with metadata |
| **Reasoning** | Generate answer with inline citations using AWS Bedrock |
| **Validation** | Check for hallucination, verify citations exist in source, score confidence |

## Tech Stack

- **Orchestration**: LangGraph (state machine with error recovery)
- **LLM**: AWS Bedrock (Claude 3 Sonnet via `anthropic.claude-3-sonnet`)
- **Vector DB**: FAISS (local, no external service needed)
- **Embeddings**: AWS Bedrock Titan Embeddings
- **Backend**: FastAPI
- **Document Processing**: PyPDF2, python-docx, tiktoken
- **Language**: Python 3.10+

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/deepfetch-ai.git
cd deepfetch-ai
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure AWS credentials

```bash
# Option A: AWS CLI (recommended)
aws configure
# Enter your Access Key, Secret Key, Region (us-east-1)

# Option B: Environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### 3. Set up environment

```bash
cp .env.example .env
# Edit .env with your preferences
```

### 4. Ingest documents

```bash
# Drop your PDFs/DOCX/TXT files into the data/ folder, then:
python cli.py ingest
```

### 5. Ask questions

```bash
# CLI mode
python cli.py ask "What is the company's PTO policy?"

# Or start the API server
python main.py
# Then open http://localhost:8000/docs for the Swagger UI
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest` | Upload and process documents |
| POST | `/query` | Ask a question, get cited answer |
| GET | `/documents` | List ingested documents |
| GET | `/health` | Health check |

## Project Structure

```
deepfetch-ai/
├── main.py                  # FastAPI application
├── cli.py                   # CLI interface
├── config.py                # Configuration
├── agents/
│   ├── ingestion.py         # Document loading + chunking + embedding
│   ├── query_understanding.py
│   ├── retrieval.py         # FAISS search + reranking
│   ├── reasoning.py         # Bedrock LLM answer generation
│   └── validation.py        # Hallucination detection + scoring
├── orchestrator/
│   └── graph.py             # LangGraph state machine
├── models/
│   └── schemas.py           # Pydantic data models
├── vectorstore/
│   └── faiss_store.py       # FAISS index wrapper
├── utils/
│   ├── document_loader.py   # Multi-format document loader
│   └── bedrock_client.py    # AWS Bedrock wrapper
├── data/                    # Drop your documents here
├── storage/                 # FAISS index persisted here
└── tests/
    └── test_pipeline.py
```

## Evaluation

The system tracks these metrics per query:
- **Retrieval Precision**: % of retrieved chunks actually relevant
- **Answer Confidence**: LLM self-assessed confidence (0-1)
- **Citation Accuracy**: % of citations that map to real source chunks
- **Latency**: End-to-end response time

## License

MIT
