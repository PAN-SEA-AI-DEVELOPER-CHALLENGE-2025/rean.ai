from typing import List, Dict, Any, Optional
import logging

from app.config import settings
from app.services.rag.embedding_client import EmbeddingClient
from app.services.rag.search_engine import SearchEngine
from app.services.rag.indexer import Indexer

logger = logging.getLogger(__name__)


class RAGService:
    """Thin facade over embedding, indexing, and search components."""
    
    def __init__(self):
        self.embedding = EmbeddingClient()
        self.search_engine = SearchEngine(self.embedding)
        self.indexer = Indexer(self.embedding)

        # Expose key limits/tokenizer for compatibility with tests/usages
        self.max_tokens_per_chunk = self.embedding.max_tokens_per_chunk
        self.max_characters_per_chunk = self.embedding.max_characters_per_chunk
        self.chunk_overlap_tokens = self.embedding.chunk_overlap_tokens
        self.tokenizer = self.embedding.tokenizer

    # ---- Embeddings and chunking wrappers ----
    async def generate_embedding(self, text: str) -> List[float]:
        return await self.embedding.generate_embedding(text)
    
    def _clean_text(self, text: str) -> str:
        return self.embedding.clean_text(text)
    
    def _count_tokens(self, text: str) -> int:
        return self.embedding.count_tokens(text)
    
    def _chunk_text_by_tokens(self, text: str, max_tokens: int, overlap_tokens: int = 100) -> List[str]:
        return self.embedding.chunk_text_by_tokens(text, max_tokens, overlap_tokens)

    async def embed_audio_transcription(self, transcription: str) -> Optional[str]:
        return await self.embedding.embed_audio_transcription(transcription)

    # ---- Indexing and Q&A wrappers ----
    async def index_lesson_transcription(self, lesson_id: str, transcription: str) -> Dict[str, Any]:
        return await self.indexer.index_lesson_transcription(lesson_id, transcription)

    async def retrieve_top_chunks(self, lesson_id: str, question: str, top_k: int = 8) -> List[Dict[str, Any]]:
        return await self.indexer.retrieve_top_chunks(lesson_id, question, top_k)

    async def answer_question(self, lesson_id: str, question: str, top_k: int = 8) -> Dict[str, Any]:
        return await self.indexer.answer_question(lesson_id, question, top_k)

    async def get_index_status(self, lesson_id: str) -> Dict[str, Any]:
        return await self.indexer.get_index_status(lesson_id)

    async def store_embedding_vector(self, lesson_id: str, embedding: List[float]) -> bool:
        return await self.indexer.store_embedding_vector(lesson_id, embedding)

    # ---- Search wrappers ----
    async def _semantic_search_pgvector(
        self, 
        query: str, 
        class_id: Optional[str] = None,
        lesson_id: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        return await self.search_engine._semantic_search_pgvector(
            query, class_id, lesson_id, limit, similarity_threshold
        )
    
    async def _semantic_search(
        self, 
        query: str, 
        class_id: Optional[str] = None,
        lesson_id: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        return await self.search_engine._semantic_search(
            query, class_id, lesson_id, limit, similarity_threshold
        )
    
    async def _fallback_text_search(
        self, 
        query: str, 
        class_id: Optional[str] = None, 
        lesson_id: Optional[str] = None, 
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        return await self.search_engine._fallback_text_search(query, class_id, lesson_id, limit)
            
    def get_supported_subjects(self) -> List[str]:
        return self.search_engine.get_supported_subjects()
    
    def get_subject_keywords(self, subject: str) -> Dict[str, List[str]]:
        return self.search_engine.get_subject_keywords(subject)
    
    def _get_domain_expansions(self) -> Dict[str, Dict[str, List[str]]]:
        return self.search_engine._get_domain_expansions()

    async def _enhance_query(self, query: str, subject: Optional[str] = None) -> Dict[str, Any]:
        return await self.search_engine._enhance_query(query, subject)

    async def search_audio_transcriptions(
        self, 
        query: str, 
        class_id: Optional[str] = None,
        subject: Optional[str] = None,
        lesson_id: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        return await self.search_engine.search_audio_transcriptions(
            query, class_id, subject, lesson_id, limit, similarity_threshold
        )

    async def _search_within_specific_lesson(
        self, query: str, lesson_id: str, similarity_threshold: float = 0.0
    ) -> Optional[Dict[str, Any]]:
        return await self.search_engine._search_within_specific_lesson(
            query, lesson_id, similarity_threshold
        )

    async def search_lecture_summaries(
        self, query: str, class_id: Optional[str] = None, limit: int = 10, similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        return await self.search_engine.search_lecture_summaries(
            query, class_id, limit, similarity_threshold
        )

    async def search_combined(
        self, 
        query: str, 
        class_id: Optional[str] = None,
        subject: Optional[str] = None,
        limit: int = 10,
        include_transcriptions: bool = True,
        include_summaries: bool = True,
    ) -> Dict[str, Any]:
        return await self.search_engine.search_combined(
            query, class_id, subject, limit, include_transcriptions, include_summaries
        )

    async def get_audio_by_class(self, class_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return await self.search_engine.get_audio_by_class(class_id, limit)



# Global instance
rag_service = RAGService()
