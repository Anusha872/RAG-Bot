import re
from enum import Enum
from typing import List
import tiktoken


class ChunkingStrategy(str, Enum):
    FIXED_SIZE = "fixed_size"
    RECURSIVE_SEMANTIC = "recursive_semantic"


class ChunkData:
    def __init__(self, content: str, chunk_index: int, token_count: int) -> None:
        self.content = content
        self.chunk_index = chunk_index
        self.token_count = token_count


class TextChunkerService:
    """Service providing dual chunking strategies: Fixed Size Overlap vs Recursive Semantic."""

    def __init__(self) -> None:
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    def count_tokens(self, text: str) -> int:
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return len(text.split())

    def chunk_text(
        self,
        text: str,
        strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> List[ChunkData]:
        if strategy == ChunkingStrategy.RECURSIVE_SEMANTIC:
            return self._recursive_semantic_chunk(text, chunk_size, chunk_overlap)
        else:
            return self._fixed_size_chunk(text, chunk_size, chunk_overlap)

    def _fixed_size_chunk(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[ChunkData]:
        """Fixed character/token length chunking with sliding overlap."""
        chunks: List[ChunkData] = []
        if not text:
            return chunks

        step = max(1, chunk_size - chunk_overlap)
        index = 0
        chunk_idx = 0

        while index < len(text):
            end_idx = min(index + chunk_size, len(text))
            chunk_str = text[index:end_idx].strip()

            if chunk_str:
                tokens = self.count_tokens(chunk_str)
                chunks.append(ChunkData(content=chunk_str, chunk_index=chunk_idx, token_count=tokens))
                chunk_idx += 1

            if end_idx >= len(text):
                break
            index += step

        return chunks

    def _recursive_semantic_chunk(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[ChunkData]:
        """Recursive splitting by paragraphs, sentences, and words to maintain semantic context."""
        separators = ["\n\n", "\n", ". ", "? ", "! ", " "]
        raw_chunks = self._split_text_recursive(text, separators, chunk_size)

        final_chunks: List[ChunkData] = []
        chunk_idx = 0

        for chunk_str in raw_chunks:
            cleaned = chunk_str.strip()
            if cleaned:
                tokens = self.count_tokens(cleaned)
                final_chunks.append(
                    ChunkData(content=cleaned, chunk_index=chunk_idx, token_count=tokens)
                )
                chunk_idx += 1

        return final_chunks

    def _split_text_recursive(
        self,
        text: str,
        separators: List[str],
        max_size: int
    ) -> List[str]:
        if len(text) <= max_size or not separators:
            return [text]

        separator = separators[0]
        splits = text.split(separator)
        
        chunks = []
        current_chunk = ""

        for split in splits:
            item = split if not current_chunk else separator + split
            if len(current_chunk) + len(item) <= max_size:
                current_chunk += item
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                if len(split) > max_size and len(separators) > 1:
                    sub_splits = self._split_text_recursive(split, separators[1:], max_size)
                    chunks.extend(sub_splits)
                    current_chunk = ""
                else:
                    current_chunk = split

        if current_chunk:
            chunks.append(current_chunk)

        return chunks


chunker_service = TextChunkerService()
