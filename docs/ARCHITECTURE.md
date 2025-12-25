# E-commerce Support AI - Architektura Techniczna

## Spis Treści
1. [Overview](#overview)
2. [Komponenty Systemu](#komponenty-systemu)
3. [Data Flow](#data-flow)
4. [Model Training Pipeline](#model-training-pipeline)
5. [RAG System](#rag-system)
6. [Deployment Architecture](#deployment-architecture)
7. [Security & Compliance](#security--compliance)
8. [Scalability](#scalability)

---

## Overview

System E-commerce Support AI to multi-tier aplikacja łącząca:
- **LLM (Large Language Model)** z LoRA fine-tuning
- **RAG (Retrieval-Augmented Generation)** dla grounding
- **Guardrails** dla safety i compliance

### High-Level Architecture

```
┌─────────────┐
│   Browser   │
│  (Client)   │
└──────┬──────┘
       │ HTTPS
       │
┌──────▼──────────┐
│   Next.js       │ ◄─── Frontend Layer
│   Frontend      │      - React components
└──────┬──────────┘      - State management
       │                 - API client
       │ REST API
       │
┌──────▼──────────┐
│   FastAPI       │ ◄─── API Gateway Layer
│   Backend       │      - Request routing
│   (Gateway)     │      - Logging & metrics
└──────┬──────────┘      - Rate limiting
       │
       ├─────────────────┬─────────────────┐
       │                 │                 │
┌──────▼──────┐   ┌─────▼──────┐   ┌─────▼──────┐
│  LLM        │   │  RAG       │   │ Guardrails │
│  Inference  │   │  Retriever │   │  Engine    │
│             │   │            │   │            │
│ Mistral-7B  │   │  FAISS +   │   │ Safety     │
│ + LoRA      │◄──┤  Sentence  │   │ Checks     │
│             │   │  Transform.│   │            │
└─────────────┘   └────────────┘   └────────────┘
```

---

## Komponenty Systemu

### 1. Frontend (Next.js)

**Technologie:**
- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS

**Struktur katalogów:**
```
frontend/src/
├── app/
│   ├── page.tsx          # Main chat page
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Global styles
├── components/
│   ├── ChatMessage.tsx   # Message bubble
│   ├── ChatInput.tsx     # Input field
│   └── StatsPanel.tsx    # Metrics sidebar
└── lib/
    └── api.ts            # API client
```

**Funkcjonalności:**
- Real-time chat interface
- Message history
- Confidence indicators
- Source citations
- Live metrics dashboard

---

### 2. Backend (FastAPI)

**Technologie:**
- FastAPI 0.109+
- Uvicorn (ASGI server)
- Pydantic (validation)
- Prometheus (metrics)

**Endpointy:**

| Endpoint | Method | Opis |
|----------|--------|------|
| `/` | GET | Root info |
| `/health` | GET | Health check |
| `/support/ask` | POST | Main AI query |
| `/metrics` | GET | Prometheus metrics |
| `/metrics/summary` | GET | Business stats |
| `/queries/recent` | GET | Recent queries |

**Request/Response Models:**

```python
# Request
class SupportQuery(BaseModel):
    query: str
    context: Optional[Dict[str, Any]]
    language: str = "pl"

# Response
class SupportResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[str]
    requires_human: bool
    category: Optional[str]
    timestamp: datetime
```

**Middleware:**
- CORS (cross-origin)
- Rate limiting (SlowAPI)
- Request logging
- Error handling

---

### 3. LLM Layer

**Base Model:**
- `mistralai/Mistral-7B-Instruct-v0.2`
- 7 billion parameters
- Multilingual (good Polish support)
- Instruction-tuned

**LoRA Fine-tuning:**

```yaml
LoRA Configuration:
  r: 16                    # Rank
  lora_alpha: 32
  target_modules:
    - q_proj               # Query projection
    - k_proj               # Key projection
    - v_proj               # Value projection
    - o_proj               # Output projection
  lora_dropout: 0.05
```

**Quantization:**
- 4-bit NormalFloat (NF4)
- BitsAndBytes library
- ~2GB VRAM (vs 14GB full precision)

**Inference Optimization:**
- Batch size: 1 (real-time)
- Max tokens: 512
- Temperature: 0.7 (balanced creativity)
- Top-p: 0.9 (nucleus sampling)

---

### 4. RAG System

**Pipeline:**

```
User Query
    ↓
[1] Query Embedding
    ↓ (sentence-transformers)
[2] Vector Similarity Search
    ↓ (FAISS)
[3] Retrieve Top-K Documents
    ↓ (k=5)
[4] Format Context
    ↓
[5] LLM Generation
    ↓
Response
```

**Components:**

#### 4.1 Document Chunker
```python
chunker = DocumentChunker(
    chunk_size=500,      # Characters per chunk
    chunk_overlap=50     # Overlap for context
)
```

Chunking strategies:
- **FAQ:** 1 Q&A = 1 chunk
- **Regulations:** Semantic paragraphs (500 chars)
- **Dialogs:** 1 dialog = 1 chunk

#### 4.2 Embedding Model
```python
model = SentenceTransformer(
    "paraphrase-multilingual-MiniLM-L12-v2"
)
```

Specs:
- Dimension: 384
- Multilingual (100+ languages)
- Polish F1: 0.89

#### 4.3 Vector Store (FAISS)
```python
index = faiss.IndexFlatL2(embedding_dim)
index.add(embeddings)
```

Index types:
- **Pilot:** IndexFlatL2 (exact search)
- **Production:** IndexIVFFlat (faster, approximate)

#### 4.4 Retrieval
```python
results = retriever.retrieve(
    query="Jak zwrócić produkt?",
    top_k=5
)
```

Returns:
```python
[
  {
    "text": "...",
    "metadata": {"source": "FAQ", "category": "zwroty"},
    "score": 0.123
  }
]
```

---

### 5. Guardrails Engine

**Safety Checks:**

```python
class Guardrails:
    def check_response(self, query, response, confidence, sources):
        # 1. Confidence threshold
        if confidence < 0.7:
            return requires_human = True

        # 2. Forbidden topics
        if detect_medical/legal/financial(query):
            return blocked = True

        # 3. PII detection
        if contains_pesel/email/phone(response):
            return blocked = True

        # 4. Hallucination detection
        if overly_specific_claims(response):
            return requires_human = True

        return passed = True
```

**Fallback Responses:**

Jeśli guardrails fail:
```
"Przepraszam, ale nie mogę odpowiedzieć na to pytanie.
Przekażę Cię do naszego zespołu obsługi klienta.

📧 pomoc@sklep.pl
📞 22 123 45 67"
```

---

## Data Flow

### Complete Request Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User sends query via Frontend                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Frontend → POST /support/ask                             │
│    Body: {query: "Jak zwrócić produkt?", language: "pl"}   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Backend validates request (Pydantic)                     │
│    - Check query length                                      │
│    - Rate limiting                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. RAG Retrieval                                            │
│    - Encode query → embedding                               │
│    - FAISS search → top 5 docs                              │
│    - Format context                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. LLM Inference                                            │
│    - Build prompt (system + context + query)               │
│    - Generate response (LoRA model)                         │
│    - Calculate confidence                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Guardrails Check                                         │
│    - Confidence threshold                                    │
│    - Forbidden topics                                        │
│    - PII detection                                           │
│    - Hallucination check                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Log & Metrics                                            │
│    - Save to database                                        │
│    - Update Prometheus counters                              │
│    - Increment category stats                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Return response to Frontend                              │
│    {answer, confidence, sources, requires_human, ...}       │
└─────────────────────────────────────────────────────────────┘
```

**Timing:**
- Typical end-to-end latency: **500-2000ms**
  - RAG retrieval: 50-100ms
  - LLM generation: 400-1800ms
  - Guardrails: 10-50ms
  - Network: 40ms

---

## Model Training Pipeline

### LoRA Fine-tuning Workflow

```
┌──────────────────┐
│ 1. Data Prep     │
│ - Load dialogs   │
│ - Format prompts │
│ - Train/val split│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 2. Load Base     │
│ - Download model │
│ - Quantize 4-bit │
│ - Freeze weights │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 3. Add LoRA      │
│ - Inject adapters│
│ - r=16, α=32     │
│ - Target: QKV    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 4. Train         │
│ - Epochs: 3      │
│ - Batch: 4       │
│ - LR: 2e-4       │
│ - AdamW 8-bit    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 5. Evaluate      │
│ - Val loss       │
│ - ROUGE/BLEU     │
│ - Human eval     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 6. Save Adapter  │
│ - LoRA weights   │
│ - Config         │
│ - Tokenizer      │
└──────────────────┘
```

**Training Script:**
```bash
python llm/train.py \
  --data data/synthetic/support_dialogs.json \
  --output models/ecommerce-support-lora \
  --epochs 3 \
  --batch_size 4
```

**Hardware Requirements:**
- GPU: NVIDIA RTX 3090 / A100
- VRAM: 8GB minimum (24GB recommended)
- Training time: ~2-4 hours (12 dialogs × 3 epochs)

---

## Deployment Architecture

### Production Setup (Docker Compose)

```
                     ┌─────────────┐
                     │   Nginx     │
                     │  (Reverse   │
                     │   Proxy)    │
                     └──────┬──────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
       ┌──────▼─────┐            ┌───────▼────┐
       │  Frontend  │            │  Backend   │
       │  Next.js   │            │  FastAPI   │
       │  :3000     │            │  :8000     │
       └────────────┘            └─────┬──────┘
                                       │
                    ┌──────────────────┼──────────────┐
                    │                  │              │
             ┌──────▼─────┐     ┌─────▼─────┐  ┌────▼─────┐
             │   Redis    │     │  MongoDB  │  │ LLM      │
             │  (Cache)   │     │  (Logs)   │  │ Service  │
             └────────────┘     └───────────┘  └──────────┘
                    │
             ┌──────▼─────┐
             │ Prometheus │
             │  :9090     │
             └──────┬─────┘
                    │
             ┌──────▼─────┐
             │  Grafana   │
             │  :3001     │
             └────────────┘
```

**Services:**
- **nginx:** SSL termination, load balancing
- **frontend:** Next.js static + SSR
- **backend:** FastAPI workers (gunicorn)
- **llm-service:** Dedicated inference server
- **redis:** Response caching, rate limiting
- **mongodb:** Query logging, analytics
- **prometheus:** Metrics collection
- **grafana:** Dashboards

---

## Security & Compliance

### 1. Data Privacy (RODO/GDPR)

**PII Protection:**
- ✅ No PII in responses (guardrails block)
- ✅ Query logging anonymized
- ✅ 30-day retention policy
- ✅ User consent required

**Data Processing:**
```python
# Anonymization
def anonymize_query(query):
    query = remove_emails(query)
    query = remove_phone_numbers(query)
    query = remove_names(query)  # NER
    return query
```

### 2. AI Safety

**Guardrails:**
- Confidence thresholds
- Forbidden topics blocking
- Hallucination detection
- Human-in-the-loop for edge cases

**Monitoring:**
- All responses logged
- Weekly audit of low-confidence responses
- Monthly model retraining

### 3. API Security

- **Authentication:** API keys (production: OAuth2)
- **Rate Limiting:** 100 req/min per IP
- **HTTPS:** SSL/TLS encryption
- **CORS:** Restricted origins

---

## Scalability

### Horizontal Scaling

```
          Load Balancer
               │
       ┌───────┼───────┬───────┐
       │       │       │       │
    API-1   API-2  API-3   API-N
       │       │       │       │
       └───────┴───────┴───────┘
               │
          Shared Redis
```

**Metrics:**
- **Current capacity:** 1000 req/day
- **Single instance:** 100 req/min
- **With 3 replicas:** 300 req/min = 432K req/day

### Vertical Scaling

**LLM Inference:**
- CPU (current): 2-4s per request
- GPU (T4): 0.5-1s per request
- GPU (A100): 0.2-0.4s per request

**Cost Optimization:**
- Batch inference (10 queries)
- Model quantization (4-bit)
- Response caching (Redis)

---

## Future Enhancements

### Phase 2 (Production)
- [ ] Multi-GPU inference (vLLM)
- [ ] Advanced RAG (ColBERT, hybrid search)
- [ ] A/B testing framework
- [ ] Real-time model updates

### Phase 3 (Scale)
- [ ] Multi-region deployment
- [ ] CDN for frontend
- [ ] Kubernetes orchestration
- [ ] Auto-scaling based on load

---

**Dokument przygotowany:** 2024-01-15
**Wersja architektury:** 1.0 (Pilot MVP)
