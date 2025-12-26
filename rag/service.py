"""
RAG Service API - Document retrieval service
Provides context from knowledge base for LLM
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

app = FastAPI(title="RAG Service", version="1.0.0")


class RetrieveRequest(BaseModel):
    """Request for document retrieval"""
    query: str
    top_k: int = 5
    filter_category: Optional[str] = None


class DocumentChunk(BaseModel):
    """Retrieved document chunk"""
    text: str
    score: float
    metadata: Dict[str, Any]


class RetrieveResponse(BaseModel):
    """Response from retrieval"""
    chunks: List[DocumentChunk]
    context: str
    sources: List[str]


# Initialize RAG retriever (lazy loading)
retriever = None


def get_retriever():
    """Get or initialize RAG retriever"""
    global retriever

    if retriever is None:
        try:
            from retriever import RAGRetriever
            retriever = RAGRetriever()

            # Build index if doesn't exist
            if not os.path.exists(retriever.index_path):
                print("Building FAISS index...")
                retriever.build_index()
                print("Index built successfully")
            else:
                print(f"Loaded existing index with {retriever.index.ntotal} vectors")

        except ImportError as e:
            print(f"Warning: Could not import RAGRetriever: {e}")
            print("RAG service will run in fallback mode")
            retriever = None
        except Exception as e:
            print(f"Warning: Could not initialize RAG: {e}")
            print("RAG service will run in fallback mode")
            retriever = None

    return retriever


class FallbackRetriever:
    """
    Simple fallback retriever for when FAISS is not available
    Uses basic keyword matching on static knowledge base
    """

    def __init__(self):
        self.knowledge_base = [
            {
                "text": "Masz 14 dni na zwrot produktu od daty otrzymania. Produkt musi być w oryginalnym opakowaniu, nieużywany. Koszt zwrotu pokrywa klient, chyba że produkt jest wadliwy.",
                "metadata": {
                    "source": "Regulamin zwrotów",
                    "category": "zwrot"
                }
            },
            {
                "text": "Oferujemy następujące opcje dostawy: kurier (1-2 dni robocze, koszt 15 zł), Paczkomat InPost (1-2 dni robocze, koszt 12 zł), odbiór osobisty (następny dzień roboczy, darmowy). Darmowa dostawa przy zamówieniach powyżej 200 zł.",
                "metadata": {
                    "source": "Polityka wysyłki",
                    "category": "dostawa"
                }
            },
            {
                "text": "Akceptujemy płatności: kartą płatniczą (Visa, Mastercard), przelewem bankowym, BLIK, płatności odroczone (PayU Pay Later). Płatność można dokonać podczas składania zamówienia.",
                "metadata": {
                    "source": "Metody płatności",
                    "category": "płatność"
                }
            },
            {
                "text": "Status zamówienia można sprawdzić w zakładce 'Moje zamówienia' po zalogowaniu. Otrzymasz również powiadomienie email o każdej zmianie statusu. Po wysłaniu otrzymasz numer do śledzenia przesyłki.",
                "metadata": {
                    "source": "FAQ: Status zamówienia",
                    "category": "status"
                }
            },
            {
                "text": "Dostępność produktów jest aktualizowana na bieżąco na stronie produktu. Jeśli produkt jest niedostępny, możesz zapisać się na powiadomienie o ponownej dostępności.",
                "metadata": {
                    "source": "FAQ: Dostępność produktów",
                    "category": "produkt"
                }
            }
        ]

    def retrieve(self, query: str, top_k: int = 5, filter_category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Simple keyword-based retrieval"""
        query_lower = query.lower()

        # Score documents based on keyword overlap
        results = []
        for doc in self.knowledge_base:
            # Simple scoring: count matching words
            doc_words = set(doc["text"].lower().split())
            query_words = set(query_lower.split())
            overlap = len(doc_words & query_words)

            # Category boost
            if filter_category and doc["metadata"]["category"] == filter_category:
                overlap += 5

            results.append({
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": float(overlap)
            })

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:top_k]

    def format_context(self, results: List[Dict[str, Any]]) -> str:
        """Format results as context"""
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result["metadata"]["source"]
            text = result["text"]
            context_parts.append(f"[Źródło {i}: {source}]\n{text}\n")
        return "\n".join(context_parts)

    def get_sources(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract source names"""
        sources = []
        seen = set()
        for result in results:
            source = result["metadata"]["source"]
            if source not in seen:
                sources.append(source)
                seen.add(source)
        return sources


fallback_retriever = FallbackRetriever()


@app.get("/")
async def root():
    """Root endpoint"""
    rag = get_retriever()
    return {
        "service": "RAG Service",
        "version": "1.0.0",
        "status": "operational",
        "mode": "faiss" if rag is not None else "fallback",
        "vectors": rag.index.ntotal if rag and hasattr(rag, 'index') else 0
    }


@app.get("/health")
async def health():
    """Health check"""
    rag = get_retriever()
    return {
        "status": "healthy",
        "mode": "faiss" if rag is not None else "fallback"
    }


@app.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(request: RetrieveRequest):
    """
    Retrieve relevant documents for query

    Args:
        request: Retrieval request with query and parameters

    Returns:
        Retrieved documents with context and sources
    """
    try:
        rag = get_retriever()

        # Use real RAG or fallback
        if rag is not None:
            results = rag.retrieve(
                query=request.query,
                top_k=request.top_k,
                filter_category=request.filter_category
            )
            context = rag.format_context(results)
            sources = rag.get_sources(results)
        else:
            # Fallback mode
            results = fallback_retriever.retrieve(
                query=request.query,
                top_k=request.top_k,
                filter_category=request.filter_category
            )
            context = fallback_retriever.format_context(results)
            sources = fallback_retriever.get_sources(results)

        # Format response
        chunks = [
            DocumentChunk(
                text=r["text"],
                score=r["score"],
                metadata=r["metadata"]
            )
            for r in results
        ]

        return RetrieveResponse(
            chunks=chunks,
            context=context,
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")


@app.get("/stats")
async def stats():
    """Get RAG statistics"""
    rag = get_retriever()

    if rag is not None and hasattr(rag, 'index'):
        return {
            "total_vectors": rag.index.ntotal,
            "total_chunks": len(rag.chunks),
            "embedding_dim": rag.embedding_dim,
            "model": rag.model_name
        }
    else:
        return {
            "total_vectors": 0,
            "total_chunks": len(fallback_retriever.knowledge_base),
            "mode": "fallback"
        }


if __name__ == "__main__":
    import uvicorn

    # Try to initialize retriever on startup
    print("Initializing RAG service...")
    get_retriever()

    uvicorn.run(app, host="0.0.0.0", port=8002)
