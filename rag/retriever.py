"""
RAG Retriever using FAISS vector store
Retrieves relevant documents for query answering
"""

import os
import json
import pickle
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

from chunker import DocumentChunker


class RAGRetriever:
    """
    Retrieval-Augmented Generation system
    Uses FAISS for fast vector similarity search
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        index_path: str = "./vectorstore/faiss.index",
        chunks_path: str = "./vectorstore/chunks.pkl"
    ):
        """
        Initialize RAG retriever

        Args:
            model_name: Sentence transformer model for embeddings
            index_path: Path to save/load FAISS index
            chunks_path: Path to save/load chunks
        """
        self.model_name = model_name
        self.index_path = index_path
        self.chunks_path = chunks_path

        # Load embedding model
        print(f"Loading embedding model: {model_name}")
        self.encoder = SentenceTransformer(model_name)
        self.embedding_dim = self.encoder.get_sentence_embedding_dimension()

        # Initialize FAISS index and chunks
        self.index: Optional[faiss.Index] = None
        self.chunks: List[Dict[str, Any]] = []

        # Load existing index if available
        if os.path.exists(index_path) and os.path.exists(chunks_path):
            self.load_index()

    def build_index(self, data_dir: str = "../data"):
        """
        Build FAISS index from documents

        Args:
            data_dir: Directory containing data files
        """
        print("Building index from documents...")

        # Initialize chunker
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)

        # Chunk all documents
        all_chunks = []

        # FAQ
        faq_path = os.path.join(data_dir, "public", "faq.json")
        if os.path.exists(faq_path):
            faq_chunks = chunker.chunk_faq(faq_path)
            all_chunks.extend(faq_chunks)
            print(f"Loaded {len(faq_chunks)} FAQ chunks")

        # Regulations
        reg_path = os.path.join(data_dir, "public", "regulations.json")
        if os.path.exists(reg_path):
            reg_chunks = chunker.chunk_regulations(reg_path)
            all_chunks.extend(reg_chunks)
            print(f"Loaded {len(reg_chunks)} regulation chunks")

        # Dialogs
        dialog_path = os.path.join(data_dir, "synthetic", "support_dialogs.json")
        if os.path.exists(dialog_path):
            dialog_chunks = chunker.chunk_dialogs(dialog_path)
            all_chunks.extend(dialog_chunks)
            print(f"Loaded {len(dialog_chunks)} dialog chunks")

        if not all_chunks:
            raise ValueError("No chunks loaded. Check data directory.")

        self.chunks = all_chunks
        print(f"Total chunks: {len(self.chunks)}")

        # Generate embeddings
        print("Generating embeddings...")
        texts = [chunk["text"] for chunk in self.chunks]
        embeddings = self.encoder.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # Build FAISS index
        print("Building FAISS index...")
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.index.add(embeddings.astype('float32'))

        print(f"Index built with {self.index.ntotal} vectors")

        # Save index
        self.save_index()

    def save_index(self):
        """Save FAISS index and chunks to disk"""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, self.index_path)
        print(f"Index saved to {self.index_path}")

        # Save chunks
        with open(self.chunks_path, 'wb') as f:
            pickle.dump(self.chunks, f)
        print(f"Chunks saved to {self.chunks_path}")

    def load_index(self):
        """Load FAISS index and chunks from disk"""
        # Load FAISS index
        self.index = faiss.read_index(self.index_path)
        print(f"Index loaded from {self.index_path} ({self.index.ntotal} vectors)")

        # Load chunks
        with open(self.chunks_path, 'rb') as f:
            self.chunks = pickle.load(f)
        print(f"Chunks loaded from {self.chunks_path} ({len(self.chunks)} chunks)")

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for query

        Args:
            query: User query
            top_k: Number of results to return
            filter_category: Optional category filter

        Returns:
            List of relevant chunks with scores
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")

        # Encode query
        query_embedding = self.encoder.encode([query], convert_to_numpy=True)

        # Search FAISS index
        # Get more results for filtering
        search_k = top_k * 3 if filter_category else top_k
        distances, indices = self.index.search(
            query_embedding.astype('float32'),
            search_k
        )

        # Retrieve chunks
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.chunks):  # Safety check
                chunk = self.chunks[idx].copy()
                chunk["score"] = float(distances[0][i])

                # Apply category filter if specified
                if filter_category:
                    chunk_category = chunk.get("metadata", {}).get("category", "")
                    if filter_category.lower() not in chunk_category.lower():
                        continue

                results.append(chunk)

                if len(results) >= top_k:
                    break

        return results

    def format_context(self, results: List[Dict[str, Any]]) -> str:
        """
        Format retrieved results as context for LLM

        Args:
            results: Retrieved chunks

        Returns:
            Formatted context string
        """
        context_parts = []

        for i, result in enumerate(results, 1):
            text = result["text"]
            metadata = result.get("metadata", {})
            source = metadata.get("source", "Unknown")

            context_parts.append(f"[Źródło {i}: {source}]\n{text}\n")

        return "\n".join(context_parts)

    def get_sources(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Extract source names from results

        Args:
            results: Retrieved chunks

        Returns:
            List of source names
        """
        sources = []
        seen = set()

        for result in results:
            metadata = result.get("metadata", {})
            source = metadata.get("source", "Unknown")
            section = metadata.get("section")

            # Create unique source identifier
            source_id = f"{source}: {section}" if section else source

            if source_id not in seen:
                sources.append(source_id)
                seen.add(source_id)

        return sources


if __name__ == "__main__":
    # Test retriever
    retriever = RAGRetriever()

    # Build index if not exists
    if not os.path.exists("./vectorstore/faiss.index"):
        retriever.build_index()
    else:
        print("Index already exists, loading...")

    # Test queries
    test_queries = [
        "Jak mogę zwrócić produkt?",
        "Jakie są koszty dostawy?",
        "Nie działa płatność kartą",
        "Chcę zmienić adres dostawy"
    ]

    print("\n" + "="*80)
    print("Testing RAG Retrieval")
    print("="*80)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 80)

        results = retriever.retrieve(query, top_k=3)

        for i, result in enumerate(results, 1):
            print(f"\n[Result {i}] Score: {result['score']:.4f}")
            print(f"Source: {result['metadata'].get('source', 'Unknown')}")
            print(f"Category: {result['metadata'].get('category', 'N/A')}")
            print(f"Text: {result['text'][:200]}...")

        print("\nFormatted context:")
        context = retriever.format_context(results[:2])
        print(context[:500] + "...")

        print("\nSources:", retriever.get_sources(results))
