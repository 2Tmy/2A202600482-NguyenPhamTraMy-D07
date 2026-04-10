from __future__ import annotations
from typing import Callable
import math
import re

class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        
        # Tách câu dựa trên các dấu kết thúc quy định
        sentences = re.split(r'(?<=[.!?])\s+|(?<=\.\n)', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk = " ".join(sentences[i : i + self.max_sentences_per_chunk])
            chunks.append(chunk)
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
        
        if not remaining_separators:
            return [current_text]

        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]
        
        parts = current_text.split(sep) if sep != "" else list(current_text)
        final_chunks = []
        current_buffer = ""

        for part in parts:
            connector = sep if current_buffer else ""
            if len(current_buffer) + len(connector) + len(part) <= self.chunk_size:
                current_buffer += connector + part
            else:
                if current_buffer:
                    final_chunks.append(current_buffer)
                
                if len(part) > self.chunk_size:
                    final_chunks.extend(self._split(part, next_seps))
                    current_buffer = ""
                else:
                    current_buffer = part

        if current_buffer:
            final_chunks.append(current_buffer)
            
        return final_chunks

class AgenticChunker:
    """
    Splits text into chunks based on semantic meaning and logical propositions 
    determined by an LLM, rather than fixed lengths or punctuation.
    """
    def __init__(self, llm_fn: Callable[[str], str], max_chunk_size: int = 800) -> None:
        self.llm_fn = llm_fn
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[str]:
            if not text: return []
            
            # Chia nhỏ văn bản thô để tránh lỗi giới hạn output của LLM
            temp_chunker = RecursiveChunker(chunk_size=10000)
            segments = temp_chunker.chunk(text)

            refined_chunks = []
            fallback_chunker = FixedSizeChunker(chunk_size=self.max_chunk_size, overlap=50)

            for segment in segments:
                try:
                    prompt = f"Insert '|||' to split this text into semantic sections. Do not change text.\n\n{segment}"
                    response = self.llm_fn(prompt)
                    initial_chunks = [c.strip() for c in response.split("|||") if c.strip()]
                    
                    for c in initial_chunks:
                        if len(c) > self.max_chunk_size:
                            refined_chunks.extend(fallback_chunker.chunk(c))
                        else:
                            refined_chunks.append(c)
                except Exception:
                    refined_chunks.extend(fallback_chunker.chunk(segment))
                    
            return refined_chunks

def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_val = _dot(vec_a, vec_b)
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(x * x for x in vec_b))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_val / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""
    def compare(self, text: str, chunk_size: int = 200, llm_fn: Callable[[str], str] | None = None) -> dict:
            """Run all built-in chunking strategies and compare their results."""
            
            # Sửa lỗi typo 'trategies' thành 'strategies'
            strategies = {
                "fixed_size": FixedSizeChunker(chunk_size=chunk_size),
                "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
                "recursive": RecursiveChunker(chunk_size=chunk_size),
            }
            
            # Kiểm tra llm_fn trước khi thêm AgenticChunker vào dict
            if llm_fn is not None:
                strategies["agentic"] = AgenticChunker(llm_fn=llm_fn, max_chunk_size=chunk_size)
            
            comparison = {}
            for name, chunker_instance in strategies.items():
                chunks = chunker_instance.chunk(text)
                comparison[name] = {
                    "count": len(chunks),
                    "avg_length": sum(len(c) for c in chunks) / len(chunks) if chunks else 0,
                    "chunks": chunks
                }
            return comparison