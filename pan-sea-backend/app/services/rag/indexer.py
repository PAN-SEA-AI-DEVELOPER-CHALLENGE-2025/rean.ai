import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
from asyncio import Queue
import re

import numpy as np
import uuid

from app.database.database import db_manager


logger = logging.getLogger(__name__)


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    try:
        a = np.array(vec1)
        b = np.array(vec2)
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)
    except Exception:
        return 0.0


def _contains_khmer(text: str) -> bool:
    """Detect if a string contains Khmer script characters."""
    try:
        return bool(re.search(r"[\u1780-\u17FF\u19E0-\u19FF]", text or ""))
    except Exception:
        return False


class Indexer:
    """Handles chunk indexing, retrieval, and persistence tasks."""

    def __init__(self, embedding_client):
        self.embedding_client = embedding_client
        # Background indexing queue
        self._queue: Queue = Queue(maxsize=100)
        self._worker_task: Optional[asyncio.Task] = None

    async def start_worker(self) -> None:
        if self._worker_task and not self._worker_task.done():
            return
        async def _worker():
            while True:
                try:
                    job = await self._queue.get()
                    if job is None:
                        break
                    lesson_id, transcription = job
                    await self.index_lesson_transcription(lesson_id, transcription)
                except Exception as e:
                    logger.error(f"Index worker error: {e}")
                finally:
                    self._queue.task_done()
        self._worker_task = asyncio.create_task(_worker())

    async def stop_worker(self) -> None:
        try:
            await self._queue.put(None)
        except Exception:
            pass
        if self._worker_task:
            await self._worker_task

    async def enqueue_indexing(self, lesson_id: str, transcription: str) -> None:
        try:
            await self._queue.put((lesson_id, transcription))
        except asyncio.QueueFull:
            logger.warning("Indexing queue full, indexing inline")
            await self.index_lesson_transcription(lesson_id, transcription)

    async def index_lesson_transcription(self, lesson_id: str, transcription: str) -> Dict[str, Any]:
        try:
            cleaned_text = self.embedding_client.clean_text(transcription)
            if not cleaned_text:
                return {"success": False, "error": "empty_transcription"}

            chunks = self.embedding_client.chunk_text_by_tokens(
                cleaned_text,
                self.embedding_client.max_tokens_per_chunk,
                self.embedding_client.chunk_overlap_tokens,
            )
            if not chunks:
                return {"success": False, "error": "no_chunks"}

            # Clear previous chunks for this lesson
            await db_manager.execute_command(
                "DELETE FROM lesson_chunks WHERE lesson_id = $1", str(lesson_id)
            )

            # Generate embeddings concurrently with a small cap to avoid provider rate limits
            semaphore = asyncio.Semaphore(5)

            async def embed_chunk(index: int, text: str) -> Optional[Dict[str, Any]]:
                async with semaphore:
                    vec = await self.embedding_client.generate_embedding(text)
                    if not vec:
                        return None
                    return {
                        "index": index,
                        "text": text,
                        "tokens": self.embedding_client.count_tokens(text),
                        "vec": vec,
                    }

            embed_tasks = [embed_chunk(idx, chunk_text) for idx, chunk_text in enumerate(chunks)]
            embedded_results = await asyncio.gather(*embed_tasks)

            inserted = 0
            insert_sql = (
                """
                INSERT INTO lesson_chunks (
                    id, lesson_id, chunk_index, text, token_count, start_offset, end_offset, embedding, embedding_vector
                ) VALUES (
                    $1, $2, $3, $4, $5, NULL, NULL, $6, $7
                )
                """
            )
            for res in embedded_results:
                if not res:
                    continue
                await db_manager.execute_command(
                    insert_sql,
                    str(uuid.uuid4()),
                    str(lesson_id),
                    res["index"],
                    res["text"],
                    res["tokens"],
                    json.dumps(res["vec"]),
                    json.dumps(res["vec"]),
                )
                inserted += 1

            return {"success": True, "chunks": inserted}
        except Exception as e:
            logger.error(f"Indexing failed for lesson {lesson_id}: {e}")
            return {"success": False, "error": str(e)}

    async def retrieve_top_chunks(self, lesson_id: str, question: str, top_k: int = 8) -> List[Dict[str, Any]]:
        try:
            q_vec = await self.embedding_client.generate_embedding(question)
            if not q_vec:
                return []

            # Try pgvector first
            try:
                test_query = "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
                test_result = await db_manager.execute_query(test_query)
                pgvector_available = len(test_result) > 0
            except Exception:
                pgvector_available = False

            if pgvector_available:
                try:
                    rows = await db_manager.execute_query(
                        """
                        SELECT id, chunk_index, text, 1 - (embedding_vector <=> $1) AS similarity
                        FROM lesson_chunks
                        WHERE lesson_id = $2 AND embedding_vector IS NOT NULL
                        ORDER BY embedding_vector <=> $1
                        LIMIT $3
                        """,
                        list(q_vec),
                        str(lesson_id),
                        top_k,
                    )
                    return [
                        {
                            "id": row["id"],
                            "chunk_index": row["chunk_index"],
                            "text": row["text"],
                            "similarity": float(row["similarity"]),
                        }
                        for row in rows or []
                    ]
                except Exception:
                    # Fall back to manual similarity below
                    pass

            # Manual similarity fallback
            rows = await db_manager.execute_query(
                """
                SELECT id, chunk_index, text, embedding
                FROM lesson_chunks
                WHERE lesson_id = $1
                ORDER BY chunk_index ASC
                """,
                str(lesson_id),
            )
            scored: List[Dict[str, Any]] = []
            for row in rows or []:
                emb = row.get("embedding")
                if isinstance(emb, str):
                    try:
                        emb = json.loads(emb)
                    except Exception:
                        emb = None
                if not isinstance(emb, list):
                    continue
                sim = _cosine_similarity(q_vec, emb)
                scored.append(
                    {
                        "id": row["id"],
                        "chunk_index": row["chunk_index"],
                        "text": row["text"],
                        "similarity": sim,
                    }
                )
            scored.sort(key=lambda x: x["similarity"], reverse=True)
            return scored[:top_k]
        except Exception as e:
            logger.error(f"Chunk retrieval failed: {e}")
            return []

    async def answer_question(self, lesson_id: str, question: str, top_k: int = 8) -> Dict[str, Any]:
        try:
            top_chunks = await self.retrieve_top_chunks(lesson_id, question, top_k)
            if not top_chunks:
                return {"success": False, "error": "no_chunks_found", "answer": "I'm not sure based on this lesson."}

            context_blocks = []
            citations = []
            for c in top_chunks:
                context_blocks.append(f"[Chunk {c['chunk_index']}]\n{c['text']}")
                citations.append({"chunk_index": c["chunk_index"], "id": c["id"], "similarity": c["similarity"]})

            # Decide output language based on lesson language and user question
            combined_context = " ".join([c.get("text", "") for c in top_chunks])
            lesson_is_khmer = _contains_khmer(combined_context)
            question_is_khmer = _contains_khmer(question)
            answer_language = "Khmer" if (lesson_is_khmer or (not lesson_is_khmer and question_is_khmer)) else "English"

            system_prompt = (
                "You are a helpful teaching assistant. Answer using ONLY the provided lesson context. "
                "If the answer is not in the context, say you don't know. "
                "Do NOT include citations, chunk numbers, or any bracketed references in your reply. "
                "Write in a clear, professional tone. "
                f"Respond in {answer_language}."
            )
            user_prompt = (
                "Lesson context:\n\n" + "\n\n".join(context_blocks)
                + "\n\nQuestion: "
                + question
                + "\n\nAnswer concisely for a student audience."
            )

            answer = await self.embedding_client.chat_complete(system_prompt, user_prompt)
            if answer is None:
                return {"success": False, "error": "no_llm_configured"}
            # Remove any stray [Chunk N] bracketed references if produced by the model
            try:
                answer = re.sub(r"\[\s*Chunk\s*\d+\s*\]", "", answer, flags=re.IGNORECASE)
            except Exception:
                pass
            return {"success": True, "answer": answer, "citations": citations}
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_index_status(self, lesson_id: str) -> Dict[str, Any]:
        try:
            row = await db_manager.execute_query(
                "SELECT COUNT(*) as count FROM lesson_chunks WHERE lesson_id = $1",
                str(lesson_id),
            )
            count = row[0]["count"] if row else 0
            return {"lesson_id": lesson_id, "chunks_indexed": count}
        except Exception as e:
            logger.error(f"Index status failed: {e}")
            return {"lesson_id": lesson_id, "chunks_indexed": 0, "error": str(e)}

    async def store_embedding_vector(self, lesson_id: str, embedding: List[float]) -> bool:
        now_ts = datetime.utcnow()
        try:
            update_both_query = """
                UPDATE lessons 
                SET embedding = $1,
                    embedding_vector = $2,
                    updated_at = $3
                WHERE id = $4
            """
            await db_manager.execute_command(
                update_both_query, json.dumps(embedding), list(embedding), now_ts, lesson_id
            )
            logger.info(f"Successfully stored embedding (JSONB + vector) for lesson {lesson_id}")
            return True
        except Exception as vector_err:
            logger.warning(
                f"Vector column unavailable or incompatible for lesson {lesson_id}, falling back to JSONB only: {vector_err}"
            )
            try:
                update_json_only_query = """
                    UPDATE lessons 
                    SET embedding = $1,
                        updated_at = $2
                    WHERE id = $3
                """
                await db_manager.execute_command(
                    update_json_only_query, json.dumps(embedding), now_ts, lesson_id
                )
                logger.info(f"Stored embedding in JSONB for lesson {lesson_id}")
                return True
            except Exception as json_err:
                logger.error(f"Failed to store embedding JSONB for lesson {lesson_id}: {json_err}")
                return False


