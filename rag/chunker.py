"""
Document chunking for RAG system
Splits documents into semantic chunks for better retrieval
"""

from typing import List, Dict, Any
import json
import re


class DocumentChunker:
    """
    Chunks documents into smaller pieces for embedding
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks for context
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks

        Args:
            text: Text to chunk
            metadata: Metadata to attach to each chunk

        Returns:
            List of chunks with metadata
        """
        if metadata is None:
            metadata = {}

        # Split by sentences first (better semantic boundaries)
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = ""
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            # If single sentence is too long, split it
            if sentence_length > self.chunk_size:
                # Add current chunk if not empty
                if current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "metadata": metadata.copy()
                    })
                    current_chunk = ""
                    current_length = 0

                # Split long sentence by words
                words = sentence.split()
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk) + len(word) + 1 <= self.chunk_size:
                        temp_chunk += word + " "
                    else:
                        if temp_chunk:
                            chunks.append({
                                "text": temp_chunk.strip(),
                                "metadata": metadata.copy()
                            })
                        temp_chunk = word + " "
                if temp_chunk:
                    chunks.append({
                        "text": temp_chunk.strip(),
                        "metadata": metadata.copy()
                    })
                continue

            # Add sentence to current chunk if it fits
            if current_length + sentence_length <= self.chunk_size:
                current_chunk += sentence + " "
                current_length += sentence_length + 1
            else:
                # Save current chunk
                if current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "metadata": metadata.copy()
                    })

                # Start new chunk with overlap
                if self.chunk_overlap > 0 and current_chunk:
                    # Take last N characters for overlap
                    overlap_text = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap_text + sentence + " "
                    current_length = len(overlap_text) + sentence_length + 1
                else:
                    current_chunk = sentence + " "
                    current_length = sentence_length + 1

        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "metadata": metadata.copy()
            })

        return chunks

    def chunk_faq(self, faq_path: str) -> List[Dict[str, Any]]:
        """
        Chunk FAQ documents

        Args:
            faq_path: Path to FAQ JSON file

        Returns:
            List of FAQ chunks
        """
        with open(faq_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        chunks = []
        for item in data.get('faq', []):
            # Each FAQ item is a separate chunk
            text = f"Pytanie: {item['question']}\n\nOdpowiedź: {item['answer']}"
            chunks.append({
                "text": text,
                "metadata": {
                    "source": "FAQ",
                    "category": item.get('category', 'general'),
                    "type": "qa_pair"
                }
            })

        return chunks

    def chunk_regulations(self, regulations_path: str) -> List[Dict[str, Any]]:
        """
        Chunk regulations documents

        Args:
            regulations_path: Path to regulations JSON file

        Returns:
            List of regulation chunks
        """
        with open(regulations_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        chunks = []
        for item in data.get('regulations', []):
            section = item['section']
            content = item['content']

            # Chunk content (regulations can be long)
            content_chunks = self.chunk_text(
                content,
                metadata={
                    "source": "Regulations",
                    "section": section,
                    "type": "regulation"
                }
            )

            # Add section header to each chunk for context
            for chunk in content_chunks:
                chunk["text"] = f"[{section}]\n\n{chunk['text']}"

            chunks.extend(content_chunks)

        return chunks

    def chunk_dialogs(self, dialogs_path: str) -> List[Dict[str, Any]]:
        """
        Chunk support dialogs

        Args:
            dialogs_path: Path to dialogs JSON file

        Returns:
            List of dialog chunks
        """
        with open(dialogs_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        chunks = []
        for dialog in data.get('dialogs', []):
            # Each dialog is a chunk
            text = f"Klient: {dialog['customer_query']}\n\nAsystent: {dialog['ai_response']}"

            chunks.append({
                "text": text,
                "metadata": {
                    "source": "Support Dialogs",
                    "category": dialog.get('category', 'general'),
                    "confidence": dialog.get('confidence', 0.0),
                    "type": "dialog"
                }
            })

        return chunks


if __name__ == "__main__":
    # Test chunking
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)

    # Test FAQ
    faq_chunks = chunker.chunk_faq("../data/public/faq.json")
    print(f"FAQ chunks: {len(faq_chunks)}")
    print("\nExample FAQ chunk:")
    print(faq_chunks[0])

    # Test regulations
    reg_chunks = chunker.chunk_regulations("../data/public/regulations.json")
    print(f"\nRegulation chunks: {len(reg_chunks)}")
    print("\nExample regulation chunk:")
    print(reg_chunks[0])

    # Test dialogs
    dialog_chunks = chunker.chunk_dialogs("../data/synthetic/support_dialogs.json")
    print(f"\nDialog chunks: {len(dialog_chunks)}")
    print("\nExample dialog chunk:")
    print(dialog_chunks[0])
