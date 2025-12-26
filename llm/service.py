"""
LLM Service API - Lightweight inference service
Uses simplified LLM for e-commerce support
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

app = FastAPI(title="LLM Service", version="1.0.0")


class GenerateRequest(BaseModel):
    """Request for text generation"""
    query: str
    context: Optional[str] = None
    max_tokens: int = 200
    temperature: float = 0.7


class GenerateResponse(BaseModel):
    """Response from text generation"""
    answer: str
    confidence: float
    model_used: str


# Simple rule-based system for MVP (can be replaced with real LLM)
class SimpleLLM:
    """
    Simplified LLM using templates and rules
    For production, replace with actual model inference
    """

    def __init__(self):
        self.templates = {
            "zwrot": """Zgodnie z naszą polityką zwrotów, {context}

Aby dokonać zwrotu:
1. Przejdź do zakładki "Zwroty i reklamacje" w swoim koncie
2. Wybierz zamówienie i produkty do zwrotu
3. Wydrukuj etykietę zwrotną
4. Wyślij paczkę w ciągu 14 dni od otrzymania

Zwrot kosztów następuje w ciągu 14 dni od otrzymania przesyłki.""",

            "dostawa": """Oferujemy następujące opcje dostawy: {context}

• Kurier (DPD, InPost) - 1-2 dni robocze
• Paczkomat InPost - 1-2 dni robocze
• Odbiór osobisty - następny dzień roboczy

Darmowa dostawa przy zamówieniach powyżej 200 zł.""",

            "płatność": """Akceptujemy następujące formy płatności: {context}

• Karta płatnicza (Visa, Mastercard)
• Przelew bankowy
• BLIK
• Płatności odroczone (PayU, PayPo)

Płatność można dokonać podczas składania zamówienia lub po jego złożeniu.""",

            "status": """Aby sprawdzić status zamówienia: {context}

1. Zaloguj się do swojego konta
2. Przejdź do zakładki "Moje zamówienia"
3. Znajdź zamówienie i kliknij "Szczegóły"
4. Zobacz aktualny status i numer do śledzenia przesyłki

Status jest aktualizowany na bieżąco.""",

            "produkt": """Informacje o produkcie: {context}

Aby sprawdzić dostępność, rozmiary i kolory:
1. Odwiedź stronę produktu
2. Sprawdź sekcję "Dostępność"
3. Wybierz odpowiedni rozmiar/kolor

Jeśli produkt jest niedostępny, możesz zapisać się na powiadomienie o ponownej dostępności."""
        }

        self.keywords = {
            "zwrot": ["zwrot", "zwrócić", "reklamacja", "wadliwy", "wymiana"],
            "dostawa": ["dostawa", "wysyłka", "kurier", "paczka", "paczkomat"],
            "płatność": ["płatność", "zapłacić", "przelew", "karta", "blik"],
            "status": ["status", "gdzie", "kiedy", "śledzenie", "track"],
            "produkt": ["dostępność", "rozmiar", "kolor", "specyfikacja", "parametry"]
        }

    def detect_category(self, query: str) -> str:
        """Detect query category based on keywords"""
        query_lower = query.lower()

        for category, keywords in self.keywords.items():
            if any(kw in query_lower for kw in keywords):
                return category

        return "general"

    def generate(self, query: str, context: str = "") -> Dict[str, Any]:
        """Generate response based on query and context"""
        category = self.detect_category(query)

        # Use template if available
        if category in self.templates:
            # Extract relevant info from context
            context_summary = context[:200] if context else "szczegółowe informacje znajdziesz w naszym regulaminie."
            answer = self.templates[category].format(context=context_summary)
            confidence = 0.85
        else:
            # Generic response
            answer = f"""Dziękuję za pytanie. {context[:200] if context else ''}

Aby udzielić Ci precyzyjnej odpowiedzi, proszę o podanie więcej szczegółów lub skontaktuj się z naszym zespołem obsługi klienta:
- Email: support@sklep.pl
- Tel: +48 123 456 789
- Chat na żywo: dostępny pn-pt 9-17"""
            confidence = 0.50

        return {
            "answer": answer.strip(),
            "confidence": confidence,
            "model_used": "rule-based-v1"
        }


# Initialize LLM
llm = SimpleLLM()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LLM Service",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "model": "rule-based-v1"
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Generate response for query

    Args:
        request: Generation request with query and optional context

    Returns:
        Generated response with answer and confidence
    """
    try:
        result = llm.generate(
            query=request.query,
            context=request.context or ""
        )

        return GenerateResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
