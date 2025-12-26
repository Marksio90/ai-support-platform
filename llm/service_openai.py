"""
LLM Service with OpenAI Integration
Alternative to rule-based LLM - uses GPT-4 for intelligent responses
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import os
from openai import AsyncOpenAI

app = FastAPI(title="LLM Service (OpenAI)", version="2.0.0")


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


# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not set - service will fail on requests")
    client = None
else:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)


# System prompt for e-commerce support
SYSTEM_PROMPT = """Jesteś pomocnym asystentem obsługi klienta w polskim sklepie internetowym.

Twoim zadaniem jest:
- Udzielanie pomocnych, uprzejmych odpowiedzi
- Używanie informacji z dostarczonego kontekstu
- Odpowiadanie PO POLSKU
- Być konkretnym i rzeczowym
- Jeśli nie masz pewności - zaproponuj kontakt z konsultantem

Zasady:
- Używaj tylko informacji z kontekstu
- Nie wymyślaj informacji o produktach, cenach, terminach
- Bądź profesjonalny ale przyjazny
- Odpowiedzi max 150-200 słów"""


class OpenAILLM:
    """OpenAI-powered LLM for e-commerce support"""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = client

    async def generate(
        self,
        query: str,
        context: str = "",
        max_tokens: int = 200,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate response using OpenAI GPT"""

        if not self.client:
            raise HTTPException(
                status_code=503,
                detail="OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
            )

        # Build prompt with context
        if context:
            user_message = f"""Kontekst z bazy wiedzy:
{context}

Pytanie klienta:
{query}

Odpowiedz na pytanie klienta używając informacji z kontekstu."""
        else:
            user_message = f"""Pytanie klienta:
{query}

Odpowiedz na pytanie klienta. Jeśli nie masz wystarczających informacji, zaproponuj kontakt z konsultantem."""

        try:
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )

            answer = response.choices[0].message.content.strip()

            # Calculate confidence based on finish reason and content
            finish_reason = response.choices[0].finish_reason
            confidence = self._estimate_confidence(answer, context, finish_reason)

            return {
                "answer": answer,
                "confidence": confidence,
                "model_used": f"openai-{self.model}"
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"OpenAI API error: {str(e)}"
            )

    def _estimate_confidence(
        self,
        answer: str,
        context: str,
        finish_reason: str
    ) -> float:
        """Estimate confidence in the response"""

        confidence = 0.85  # Base confidence for GPT-4

        # Penalize if no context provided
        if not context or len(context) < 50:
            confidence -= 0.15

        # Check finish reason
        if finish_reason != "stop":
            confidence -= 0.1

        # Check for uncertainty phrases
        uncertainty_phrases = [
            "nie jestem pewien",
            "nie mam informacji",
            "skontaktuj się",
            "nie mogę potwierdzić",
            "proponuję kontakt"
        ]

        answer_lower = answer.lower()
        if any(phrase in answer_lower for phrase in uncertainty_phrases):
            confidence -= 0.2

        # Penalize very short responses
        if len(answer) < 50:
            confidence -= 0.1

        return max(0.3, min(1.0, confidence))


# Initialize LLM
llm = OpenAILLM()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LLM Service (OpenAI)",
        "version": "2.0.0",
        "status": "operational",
        "model": llm.model if client else "not_configured"
    }


@app.get("/health")
async def health():
    """Health check"""
    status = "healthy" if client else "degraded"
    return {
        "status": status,
        "model": f"openai-{llm.model}" if client else "not_configured",
        "api_key_set": bool(client)
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Generate response for query using OpenAI GPT

    Requires OPENAI_API_KEY environment variable to be set.

    Args:
        request: Generation request with query and optional context

    Returns:
        Generated response with answer and confidence
    """
    try:
        result = await llm.generate(
            query=request.query,
            context=request.context or "",
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        return GenerateResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Generation error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    # Check API key on startup
    if not OPENAI_API_KEY:
        print("\n" + "="*60)
        print("WARNING: OPENAI_API_KEY environment variable not set!")
        print("Service will start but requests will fail.")
        print("Set OPENAI_API_KEY to use OpenAI integration.")
        print("="*60 + "\n")
    else:
        print(f"✓ OpenAI API key configured")
        print(f"✓ Using model: {llm.model}")

    uvicorn.run(app, host="0.0.0.0", port=8001)
