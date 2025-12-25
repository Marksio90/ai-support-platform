"""
E-commerce Support AI - Backend API Gateway
FastAPI application for handling support queries
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
request_counter = Counter(
    'support_ai_requests_total',
    'Total support requests',
    ['endpoint', 'status']
)
response_time = Histogram(
    'support_ai_response_seconds',
    'Response time in seconds',
    ['endpoint']
)
confidence_histogram = Histogram(
    'support_ai_confidence_score',
    'Confidence score distribution'
)

app = FastAPI(
    title="E-commerce Support AI",
    description="AI-powered customer support automation for e-commerce",
    version="1.0.0"
)

# CORS - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class SupportQuery(BaseModel):
    """Customer support query"""
    query: str = Field(..., min_length=3, max_length=1000, description="Customer question")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context (order_id, user_id, etc.)")
    language: str = Field(default="pl", description="Response language")

class SupportResponse(BaseModel):
    """AI support response"""
    answer: str = Field(..., description="AI-generated answer")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    sources: list[str] = Field(default_factory=list, description="Source documents used")
    requires_human: bool = Field(..., description="Whether human intervention is needed")
    category: Optional[str] = Field(default=None, description="Query category")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    services: Dict[str, str]

# In-memory storage for demo (replace with Redis/MongoDB in production)
query_log = []

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "E-commerce Support AI",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns status of all system components
    """
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        services={
            "api": "healthy",
            "llm": "healthy",  # TODO: Check actual LLM service
            "rag": "healthy",  # TODO: Check RAG service
            "database": "healthy"
        }
    )

@app.post("/support/ask", response_model=SupportResponse, tags=["Support"])
async def ask_support(query: SupportQuery):
    """
    Main support endpoint
    Processes customer query and returns AI-generated response
    """
    start_time = time.time()

    try:
        logger.info(f"Received query: {query.query[:100]}...")

        # TODO: Integrate with LLM + RAG services
        # For now, return a mock response

        # Simulate processing
        answer = await process_query(query)

        response = SupportResponse(
            answer=answer["text"],
            confidence=answer["confidence"],
            sources=answer["sources"],
            requires_human=answer["confidence"] < 0.7,  # Threshold
            category=answer.get("category")
        )

        # Log query and response
        query_log.append({
            "query": query.query,
            "response": response.dict(),
            "timestamp": datetime.utcnow().isoformat()
        })

        # Metrics
        duration = time.time() - start_time
        request_counter.labels(endpoint="/support/ask", status="success").inc()
        response_time.labels(endpoint="/support/ask").observe(duration)
        confidence_histogram.observe(response.confidence)

        logger.info(f"Query processed in {duration:.2f}s, confidence: {response.confidence:.2f}")

        return response

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        request_counter.labels(endpoint="/support/ask", status="error").inc()
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Prometheus metrics endpoint
    Returns metrics in Prometheus format
    """
    return JSONResponse(
        content=generate_latest().decode("utf-8"),
        media_type="text/plain"
    )

@app.get("/metrics/summary", tags=["Monitoring"])
async def metrics_summary():
    """
    Business metrics summary
    Returns aggregated statistics for business reporting
    """
    if not query_log:
        return {
            "total_queries": 0,
            "avg_confidence": 0.0,
            "automation_rate": 0.0,
            "categories": {}
        }

    total = len(query_log)
    confidences = [q["response"]["confidence"] for q in query_log]
    avg_confidence = sum(confidences) / len(confidences)
    automated = sum(1 for q in query_log if not q["response"]["requires_human"])

    # Category breakdown
    categories = {}
    for q in query_log:
        cat = q["response"].get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "total_queries": total,
        "avg_confidence": round(avg_confidence, 3),
        "automation_rate": round(automated / total * 100, 1),
        "automated_queries": automated,
        "human_required": total - automated,
        "categories": categories,
        "period": {
            "start": query_log[0]["timestamp"] if query_log else None,
            "end": query_log[-1]["timestamp"] if query_log else None
        }
    }

@app.get("/queries/recent", tags=["Monitoring"])
async def recent_queries(limit: int = 10):
    """
    Get recent queries for debugging and monitoring
    """
    return {
        "queries": query_log[-limit:],
        "total": len(query_log)
    }

# Mock processing function (will be replaced with actual LLM + RAG)
async def process_query(query: SupportQuery) -> Dict[str, Any]:
    """
    Process support query using LLM + RAG
    This is a mock implementation - will be replaced with actual integration
    """
    # TODO: Replace with actual LLM + RAG integration

    # Mock categorization
    categories = {
        "status": ["status", "gdzie", "kiedy", "śledzenie"],
        "zwrot": ["zwrot", "reklamacja", "wymiana", "wadliwy"],
        "dostawa": ["dostawa", "wysyłka", "kurier", "paczka"],
        "płatność": ["płatność", "zapłacić", "przelew", "karta"],
        "produkt": ["dostępność", "rozmiar", "kolor", "specyfikacja"]
    }

    query_lower = query.query.lower()
    detected_category = "inne"

    for category, keywords in categories.items():
        if any(kw in query_lower for kw in keywords):
            detected_category = category
            break

    # Mock responses based on category
    mock_responses = {
        "status": {
            "text": "Rozumiem, że pytasz o status zamówienia. Aby sprawdzić aktualny status Twojego zamówienia, przejdź do zakładki 'Moje zamówienia' w swoim koncie lub użyj numeru zamówienia do śledzenia przesyłki na stronie kuriera. Jeśli potrzebujesz szczegółowych informacji, podaj numer zamówienia.",
            "confidence": 0.85,
            "sources": ["FAQ: Status zamówienia", "Polityka wysyłki"]
        },
        "zwrot": {
            "text": "Zgodnie z naszą polityką zwrotów, masz 14 dni na zwrot produktu od daty otrzymania. Produkt musi być w oryginalnym opakowaniu, nieużywany. Aby rozpocząć proces zwrotu, przejdź do zakładki 'Zwroty i reklamacje' w swoim koncie. Koszt zwrotu pokrywa klient, chyba że produkt jest wadliwy.",
            "confidence": 0.90,
            "sources": ["Regulamin zwrotów", "Polityka reklamacji"]
        },
        "dostawa": {
            "text": "Oferujemy następujące opcje dostawy: kurier (1-2 dni robocze), Paczkomat (1-2 dni robocze), odbiór osobisty. Koszt dostawy zależy od wartości zamówienia - darmowa dostawa przy zamówieniach powyżej 200 zł.",
            "confidence": 0.88,
            "sources": ["Polityka wysyłki", "Cennik dostaw"]
        },
        "płatność": {
            "text": "Akceptujemy następujące formy płatności: przelew bankowy, karta płatnicza (Visa, Mastercard), BLIK, płatności odroczone (Pay Later). Płatność można dokonać podczas składania zamówienia.",
            "confidence": 0.87,
            "sources": ["Metody płatności", "FAQ: Płatności"]
        },
        "produkt": {
            "text": "Aby sprawdzić dostępność produktu, odwiedź stronę produktu na naszej stronie. Aktualne informacje o dostępności, rozmiarach i kolorach znajdziesz w szczegółach produktu. Jeśli interesuje Cię konkretny produkt, podaj jego nazwę lub kod.",
            "confidence": 0.75,
            "sources": ["Katalog produktów", "FAQ: Dostępność"]
        }
    }

    response = mock_responses.get(
        detected_category,
        {
            "text": "Dziękuję za pytanie. Aby udzielić Ci precyzyjnej odpowiedzi, potrzebuję więcej szczegółów. Czy możesz doprecyzować swoje pytanie lub skontaktować się z naszym zespołem obsługi klienta?",
            "confidence": 0.50,
            "sources": ["Ogólne FAQ"]
        }
    )

    response["category"] = detected_category
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
