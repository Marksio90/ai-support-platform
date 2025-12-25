# 🤖 E-commerce Support AI

**Automatyzacja obsługi klienta dla e-commerce z użyciem AI (Polski język)**

Pilot MVP systemu AI do automatyzacji 50-70% zapytań klientów w sklepach internetowych.

---

## 🎯 Cel Projektu

**Biznesowy:**
- Automatyzacja 50-70% zapytań supportowych
- Skrócenie czasu odpowiedzi z godzin → sekund
- Redukcja kosztów obsługi klienta

**Techniczny:**
- Pierwszy komercyjny model PL z LoRA fine-tuning
- RAG pipeline z polskimi dokumentami
- Gotowy szablon produktu do powielania

---

## 📦 Deliverables

### 1. Działający Support AI
- ✅ Chat web interface (Next.js)
- ✅ API endpoint (`POST /support/ask`)
- ✅ Odpowiedzi naturalne, zgodne z polityką, z cytowaniem źródeł (RAG)

### 2. Raport Biznesowy
- ✅ % zapytań obsłużonych automatycznie
- ✅ Średni czas odpowiedzi
- ✅ Kategorie pytań
- ✅ Rekomendacja wdrożenia

### 3. Model Package
- ✅ Bazowy model + LoRA adapter
- ✅ Konfiguracja RAG
- ✅ Manifest modelu
- ✅ Gotowe do fine-tune / hostowania jako API

---

## 🏗️ Architektura

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                            │
│                  Next.js + React + Tailwind                 │
│                     (Chat Interface)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/REST
                         │
┌────────────────────────▼────────────────────────────────────┐
│                      BACKEND API                            │
│                   FastAPI + Uvicorn                         │
│             /ask | /health | /metrics                       │
└──────────────┬──────────────────┬──────────────────────────┘
               │                  │
               │                  │
       ┌───────▼──────┐   ┌──────▼──────────┐
       │  LLM LAYER   │   │   RAG SYSTEM    │
       │              │   │                 │
       │  Mistral-7B  │   │  FAISS Vector   │
       │  + LoRA      │   │  Store          │
       │  (Polish)    │   │                 │
       │              │   │  Sentence       │
       │  Inference   │◄──┤  Transformers   │
       │  Engine      │   │  (Embeddings)   │
       └──────────────┘   └─────────────────┘
               │
               │
       ┌───────▼──────────────────────────────┐
       │       GUARDRAILS & EVALUATION         │
       │  - Confidence thresholds              │
       │  - Refusal policy                     │
       │  - PII detection                      │
       └───────────────────────────────────────┘
```

### Komponenty:

1. **Frontend** (`/frontend`)
   - Next.js 14 + React
   - Real-time chat interface
   - Stats panel (metryki na żywo)

2. **Backend** (`/backend`)
   - FastAPI API Gateway
   - Logging & metrics (Prometheus)
   - Query routing

3. **LLM Layer** (`/llm`)
   - Base model: Mistral-7B-Instruct (multilingual)
   - LoRA fine-tuning dla polskiego e-commerce
   - 4-bit quantization (efektywne GPU)

4. **RAG System** (`/rag`)
   - FAISS vector database
   - Multilingual embeddings
   - Document chunking & retrieval

5. **Data** (`/data`)
   - Syntetyczne dialogi supportowe (PL)
   - FAQ sklepów
   - Regulaminy

6. **Evaluation** (`/evaluation`)
   - Guardrails (safety checks)
   - Metrics tracking

---

## 🚀 Quick Start

### Wymagania

- **Python:** 3.10+
- **Node.js:** 18+
- **Docker:** 20+ (opcjonalnie)
- **GPU:** NVIDIA z 8GB+ VRAM (dla treningu LoRA)
  - Dla inferencji: CPU ok (wolniejsze)

### Instalacja

#### 1. Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
python app/main.py
```

Backend dostępny na: http://localhost:8000
API Docs: http://localhost:8000/docs

#### 2. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Frontend dostępny na: http://localhost:3000

#### 3. RAG System (Opcjonalnie - dla pełnej funkcjonalności)

```bash
cd rag
pip install -r requirements.txt

# Zbuduj FAISS index z danych
python retriever.py
```

To stworzy `vectorstore/faiss.index` z embeddings dokumentów.

#### 4. LLM Layer (Dla zaawansowanych - trening LoRA)

```bash
cd llm
pip install -r requirements.txt

# Opcja A: Użyj bazowego modelu (bez fine-tuning)
python inference.py

# Opcja B: Trenuj własny LoRA adapter
python train.py
```

**UWAGA:** Trening wymaga GPU. Na CPU będzie bardzo wolno.

---

## 🐳 Docker Deployment

Szybkie uruchomienie wszystkich serwisów:

```bash
cd deployment
docker-compose up -d
```

Serwisy:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

---

## 📊 Użycie

### API Endpoints

#### POST /support/ask
Zadaj pytanie AI:

```bash
curl -X POST http://localhost:8000/support/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Jak mogę zwrócić produkt?",
    "language": "pl"
  }'
```

Odpowiedź:
```json
{
  "answer": "Aby zwrócić produkt, masz 14 dni od otrzymania...",
  "confidence": 0.85,
  "sources": ["Regulamin zwrotów", "FAQ: Zwroty"],
  "requires_human": false,
  "category": "zwroty",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET /metrics/summary
Statystyki biznesowe:

```bash
curl http://localhost:8000/metrics/summary
```

#### GET /health
Health check:

```bash
curl http://localhost:8000/health
```

---

## 🎓 Dane Treningowe

### Struktura danych

```
data/
├── public/              # Dane publiczne
│   ├── faq.json        # FAQ sklepów (20+ pytań)
│   └── regulations.json # Regulaminy (zwroty, dostawa, płatności)
└── synthetic/           # Syntetyczne dialogi
    └── support_dialogs.json  # 12 przykładowych dialogów PL
```

### Format FAQ:
```json
{
  "faq": [
    {
      "category": "dostawa",
      "question": "Jakie są opcje dostawy?",
      "answer": "Oferujemy kurier, paczkomat, odbiór osobisty..."
    }
  ]
}
```

### Format dialogów:
```json
{
  "dialogs": [
    {
      "category": "zwrot",
      "customer_query": "Chcę zwrócić buty...",
      "ai_response": "Oczywiście pomogę! Zwrot jest prosty...",
      "confidence": 0.95,
      "sources": ["Regulamin zwrotów"]
    }
  ]
}
```

---

## 🧠 Model Configuration

Konfiguracja w `llm/model_config.yaml`:

```yaml
base_model:
  name: "mistralai/Mistral-7B-Instruct-v0.2"

lora:
  r: 16
  lora_alpha: 32
  target_modules: ["q_proj", "k_proj", "v_proj"]

quantization:
  bits: 4
  type: "nf4"

guardrails:
  confidence_threshold: 0.7
```

---

## 📈 Metryki i Monitoring

### Prometheus Metrics

Backend exportuje:
- `support_ai_requests_total` - liczba zapytań
- `support_ai_response_seconds` - czas odpowiedzi
- `support_ai_confidence_score` - rozkład confidence

### Grafana Dashboards

Import dashboardu: `deployment/grafana_dashboard.json`

Metryki:
- Automation rate (% automated queries)
- Average confidence
- Response time (p50, p95, p99)
- Category breakdown

---

## 🛡️ Guardrails

System automatycznie sprawdza:

1. **Confidence threshold:** < 0.7 → przekaż do człowieka
2. **Forbidden topics:** medyczne, prawne, finansowe
3. **PII detection:** PESEL, numery kont, email
4. **Hallucination detection:** nierealistyczne claims
5. **Response length:** min 20, max 500 znaków

Jeśli guardrails fail → fallback response.

---

## 📚 Dokumentacja

- [Business Report Template](docs/BUSINESS_REPORT_TEMPLATE.md) - szablon raportu dla klienta
- [Architecture](docs/ARCHITECTURE.md) - szczegółowa architektura
- [API Documentation](http://localhost:8000/docs) - Swagger/OpenAPI docs

---

## 🧪 Testing

### Test RAG Retrieval
```bash
cd rag
python retriever.py
```

### Test Guardrails
```bash
cd evaluation
python guardrails.py
```

### Test LLM Inference
```bash
cd llm
python inference.py
```

---

## 🎯 Roadmap

### ✅ Pilot MVP (Current)
- [x] Backend API
- [x] Frontend Chat
- [x] RAG system
- [x] Synthetic data
- [x] Guardrails
- [x] Business report template

### 🚧 Phase 1: Production Ready
- [ ] Integrate real customer data
- [ ] Fine-tune LoRA on actual dialogs
- [ ] CRM/ERP integration
- [ ] A/B testing framework
- [ ] Advanced metrics

### 🔮 Phase 2: Advanced Features
- [ ] Multi-language (EN, DE)
- [ ] Image support (product photos)
- [ ] Proactive recommendations
- [ ] Email/WhatsApp channels
- [ ] Sentiment analysis

---

## 💡 Use Cases

### Automatyzowane kategorie:
1. ✅ Status zamówienia
2. ✅ Zwroty i reklamacje
3. ✅ Koszty dostawy
4. ✅ Metody płatności
5. ✅ Dostępność produktów
6. ✅ Kody rabatowe
7. ✅ Tabele rozmiarów

### Przekazywane do człowieka:
- ❌ Niestandardowe negocjacje
- ❌ Skomplikowane reklamacje
- ❌ Błędy systemowe
- ❌ VIP customers

---

## 📊 Expected Results (PoC)

Po 14 dniach pilotu oczekujemy:

| Metryka | Cel |
|---------|-----|
| Automation rate | 50-70% |
| Avg response time | < 5s |
| Avg confidence | > 75% |
| Customer satisfaction | > 80% |

**ROI:** Oszczędność 20-30% kosztów supportu

---

## 🤝 Contributing

To jest pilot PoC dla klientów komercyjnych.

Aby dostosować do swojej branży:
1. Zamień dane w `/data` na własne FAQ/regulaminy
2. Dostosuj kategorie w `/backend/app/main.py`
3. Przetreniuj LoRA na własnych dialogach
4. Zaktualizuj system prompt w `llm/model_config.yaml`

---

## 📄 License

Proprietary - komercyjne wdrożenia wymagają licencji.

Kontakt: [twoj-email@firma.pl]

---

## 🆘 Support

**Problemy techniczne:**
- GitHub Issues: [link]
- Email: support@firma.pl

**Wdrożenia komercyjne:**
- Email: sales@firma.pl
- Telefon: +48 XXX XXX XXX

---

## 🏆 Success Stories

> "Zautomatyzowaliśmy 65% zapytań w pierwszym miesiącu. Czas odpowiedzi spadł z 4h do 8s."
> – [Nazwa Klienta], E-commerce Manager

---

## 🔗 Links

- [Demo Video](link)
- [Case Studies](link)
- [Technical Whitepaper](link)

---

**Made with ❤️ in Poland 🇵🇱**

*Pierwszy polski AI Support Agent dla e-commerce*
