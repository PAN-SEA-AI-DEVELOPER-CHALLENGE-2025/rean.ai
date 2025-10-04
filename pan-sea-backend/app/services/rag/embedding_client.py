import json
import logging
import re
from typing import Any, List, Optional
import asyncio
import hashlib
from collections import OrderedDict
import boto3
import google.generativeai as genai
import numpy as np
import tiktoken
from openai import OpenAI

from app.config import settings
from app.core.cache import cache_service, CacheKeys


logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Provider-agnostic embedding and chat client with token-aware chunking."""

    def __init__(self):
        # Limits and defaults
        self.max_tokens_per_chunk = 400
        self.max_characters_per_chunk = 2000
        self.chunk_overlap_tokens = 50

        # Tokenizer (use cl100k_base as approximation)
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Failed to load tokenizer: {e}")
            self.tokenizer = None

        # OpenAI (preferred)
        try:
            self.openai_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
            self.openai_embeddings_model = getattr(settings, "openai_embeddings_model", "text-embedding-3-small")
            self.openai_chat_model = getattr(settings, "openai_chat_model", "gpt-4o-mini")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
            self.openai_client = None
            self.openai_embeddings_model = "text-embedding-3-small"
            self.openai_chat_model = "gpt-4o-mini"

        # Gemini (fallback)
        try:
            if settings.gemini_api_key:
                genai.configure(api_key=settings.gemini_api_key)
                emb_model = getattr(settings, "gemini_embeddings_model", "models/text-embedding-004")
                if not emb_model.startswith("models/"):
                    emb_model = "models/" + emb_model
                self.gemini_embeddings_model = emb_model
                self.gemini_chat_model = getattr(settings, "gemini_chat_model", "gemini-1.5-flash")
            else:
                self.gemini_embeddings_model = None
                self.gemini_chat_model = None
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini client: {e}")
            self.gemini_embeddings_model = None
            self.gemini_chat_model = None

        # Sea Lion (OpenAI-compatible; preferred for chat if configured)
        try:
            if getattr(settings, "sea_lion_api_key", None):
                self.sealion_client = OpenAI(
                    api_key=settings.sea_lion_api_key,
                    base_url=getattr(settings, "sea_lion_base_url", None),
                )
                self.sealion_chat_model = getattr(settings, "sea_lion_model", None)
            else:
                self.sealion_client = None
                self.sealion_chat_model = None
        except Exception as e:
            logger.warning(f"Failed to initialize Sea Lion client: {e}")
            self.sealion_client = None
            self.sealion_chat_model = None

        # Bedrock Cohere (last-resort fallback)
        self.bedrock_client = None
        self.embedding_model = "cohere.embed-multilingual-v3"
        try:
            self.bedrock_client = boto3.client(
                "bedrock-runtime",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
            logger.info("Successfully initialized AWS Bedrock client")
        except Exception as e:
            logger.error(f"Failed to initialize AWS Bedrock client: {e}")

        # In-memory LRU cache for embeddings to reduce duplicate provider calls
        self._embed_cache: OrderedDict[str, List[float]] = OrderedDict()
        self._embed_cache_maxsize: int = 2048
        self._cache_lock: asyncio.Lock = asyncio.Lock()

        # Retry and circuit breaker settings
        self._max_retries: int = 3
        self._base_backoff_seconds: float = 0.5
        self._failure_threshold: int = 3
        self._reset_timeout_seconds: int = 60
        self._circuit_state: dict = {}

    # -------- Internals --------
    async def _run_in_thread(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    def _cache_key(self, text: str, model_name: str) -> str:
        normalized = re.sub(r"\s+", " ", text.strip()).lower()
        return hashlib.sha256((model_name + "::" + normalized).encode("utf-8")).hexdigest()

    async def _get_cached_embedding(self, key: str) -> Optional[List[float]]:
        async with self._cache_lock:
            if key in self._embed_cache:
                # move to end (most-recently used)
                self._embed_cache.move_to_end(key)
                return self._embed_cache[key]
            return None

    async def _set_cached_embedding(self, key: str, value: List[float]) -> None:
        async with self._cache_lock:
            self._embed_cache[key] = value
            self._embed_cache.move_to_end(key)
            if len(self._embed_cache) > self._embed_cache_maxsize:
                self._embed_cache.popitem(last=False)

    # -------- Retry & Circuit helpers --------
    def _is_circuit_open(self, key: str) -> bool:
        state = self._circuit_state.get(key)
        if not state:
            return False
        if state.get("opened_until", 0) > asyncio.get_event_loop().time():
            return True
        return False

    def _record_success(self, key: str) -> None:
        self._circuit_state[key] = {"failures": 0, "opened_until": 0}

    def _record_failure(self, key: str) -> None:
        state = self._circuit_state.get(key, {"failures": 0, "opened_until": 0})
        state["failures"] = int(state.get("failures", 0)) + 1
        if state["failures"] >= self._failure_threshold:
            state["opened_until"] = asyncio.get_event_loop().time() + self._reset_timeout_seconds
        self._circuit_state[key] = state

    async def _retry_with_backoff(self, op_key: str, func, *args, **kwargs):
        if self._is_circuit_open(op_key):
            logger.warning(f"Circuit open for {op_key}, skipping call")
            raise RuntimeError("circuit_open")
        attempt = 0
        delay = self._base_backoff_seconds
        while True:
            try:
                result = await self._run_in_thread(func, *args, **kwargs)
                self._record_success(op_key)
                return result
            except Exception as e:
                attempt += 1
                self._record_failure(op_key)
                if attempt >= self._max_retries:
                    raise
                await asyncio.sleep(delay)
                delay *= 2

    # -------- Text utils --------
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text.strip())
        if len(text) < 10:
            return ""
        return text

    def count_tokens(self, text: str) -> int:
        if not self.tokenizer:
            return len(text) // 4
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            return len(text) // 4

    def chunk_text_by_tokens(self, text: str, max_tokens: int, overlap_tokens: int = 100) -> List[str]:
        try:
            if not self.tokenizer:
                return [text] if text else []
            tokens = self.tokenizer.encode(text)
            total_tokens = len(tokens)
            if total_tokens <= max_tokens:
                return [text]

            chunks: List[str] = []
            start_idx = 0
            while start_idx < total_tokens:
                end_idx = min(start_idx + max_tokens, total_tokens)
                chunk_tokens = tokens[start_idx:end_idx]
                chunk_text = self.tokenizer.decode(chunk_tokens).strip()
                if chunk_text:
                    chunks.append(chunk_text)
                if end_idx >= total_tokens:
                    break
                start_idx = end_idx - overlap_tokens
                if start_idx <= 0:
                    start_idx = end_idx
            return chunks
        except Exception as e:
            logger.error(f"Error in token-based chunking: {e}")
            return [text] if text else []

    # -------- Embeddings --------
    async def generate_embedding(self, text: str) -> List[float]:
        cleaned_text = self.clean_text(text)
        if not cleaned_text:
            return []

        # Check cache first
        provider_model_name = (
            self.openai_embeddings_model if self.openai_client else (
                self.gemini_embeddings_model if self.gemini_embeddings_model else self.embedding_model
            )
        )
        cache_key = self._cache_key(cleaned_text, provider_model_name or "unknown")
        # Try Redis cache
        try:
            redis_key = cache_service.generate_key(CacheKeys.EMBEDDING, provider_model_name or "unknown", cache_key)
            cached = await cache_service.get(redis_key)
            if isinstance(cached, list) and cached:
                return cached
        except Exception:
            cached = None
        # Try in-memory cache
        cached = cached or await self._get_cached_embedding(cache_key)
        if cached:
            return cached

        # Preferred: OpenAI
        if self.openai_client:
            try:
                resp = await self._retry_with_backoff(
                    "openai_embedding",
                    self.openai_client.embeddings.create,
                    model=self.openai_embeddings_model,
                    input=cleaned_text,
                )
                vec = resp.data[0].embedding
                if vec:
                    await self._set_cached_embedding(cache_key, vec)
                    try:
                        await cache_service.set(redis_key, vec, ttl=24*3600)
                    except Exception:
                        pass
                    return vec
            except Exception as e:
                logger.warning(f"OpenAI embedding failed, falling back: {e}")

        # Alternative: Gemini
        if self.gemini_embeddings_model:
            try:
                emb = await self._retry_with_backoff(
                    "gemini_embedding",
                    genai.embed_content,
                    model=self.gemini_embeddings_model,
                    content=cleaned_text,
                )
                vec = emb.get("embedding") or emb.get("data", {}).get("embedding")
                if vec:
                    await self._set_cached_embedding(cache_key, vec)
                    try:
                        await cache_service.set(redis_key, vec, ttl=24*3600)
                    except Exception:
                        pass
                    return vec
            except Exception as e:
                logger.warning(f"Gemini embedding failed, falling back further: {e}")

        # Fallback: Bedrock Cohere
        if not self.bedrock_client:
            logger.warning("No embedding provider available")
            return []
        try:
            if len(cleaned_text) > self.max_characters_per_chunk:
                cleaned_text = cleaned_text[: self.max_characters_per_chunk]
            request_body = {"texts": [cleaned_text], "input_type": "search_document", "truncate": "NONE"}
            response = await self._retry_with_backoff(
                "bedrock_embedding",
                self.bedrock_client.invoke_model,
                modelId=self.embedding_model,
                body=json.dumps(request_body),
                contentType="application/json",
            )
            response_body = json.loads(response["body"].read())
            embeddings = response_body.get("embeddings", [])
            if not embeddings:
                return []
            vec = embeddings[0]
            await self._set_cached_embedding(cache_key, vec)
            try:
                await cache_service.set(redis_key, vec, ttl=24*3600)
            except Exception:
                pass
            return vec
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

    async def embed_audio_transcription(self, transcription: str) -> Optional[str]:
        try:
            cleaned_text = self.clean_text(transcription)
            if not cleaned_text:
                logger.warning("No valid text to embed for audio")
                return None

            actual_tokens = self.count_tokens(cleaned_text)
            if actual_tokens <= self.max_tokens_per_chunk:
                embedding = await self.generate_embedding(cleaned_text)
                if not embedding:
                    logger.error("Failed to generate embedding for audio")
                    return None
            else:
                chunks = self.chunk_text_by_tokens(
                    cleaned_text,
                    max_tokens=self.max_tokens_per_chunk,
                    overlap_tokens=self.chunk_overlap_tokens,
                )
                if not chunks:
                    logger.error("Failed to create chunks from transcription")
                    return None
                chunk_embeddings: List[List[float]] = []
                for chunk in chunks:
                    try:
                        chunk_tokens = self.count_tokens(chunk)
                        if chunk_tokens > self.max_tokens_per_chunk:
                            continue
                        chunk_embedding = await self.generate_embedding(chunk)
                        if chunk_embedding:
                            chunk_embeddings.append(chunk_embedding)
                    except Exception:
                        continue
                if not chunk_embeddings:
                    logger.error("Failed to generate embeddings for any chunks")
                    return None
                embedding = np.mean(chunk_embeddings, axis=0).tolist()
            return json.dumps(embedding)
        except Exception as e:
            logger.error(f"Error in embed_audio_transcription: {str(e)}")
            return None

    # -------- Chat --------
    async def chat_complete(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        # Preferred: Sea Lion (if configured)
        try:
            if getattr(self, "sealion_client", None) and getattr(self, "sealion_chat_model", None):
                resp = await self._retry_with_backoff(
                    "sealion_chat",
                    self.sealion_client.chat.completions.create,
                    model=self.sealion_chat_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                return resp.choices[0].message.content
        except Exception as e:
            logger.warning(f"Sea Lion chat failed: {e}")

        # Preferred: OpenAI
        try:
            if self.openai_client:
                resp = await self._retry_with_backoff(
                    "openai_chat",
                    self.openai_client.chat.completions.create,
                    model=self.openai_chat_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                return resp.choices[0].message.content
        except Exception as e:
            logger.warning(f"OpenAI chat failed: {e}")

        # Alternative: Gemini
        try:
            if self.gemini_chat_model:
                def _gemini_chat(model_name: str, content: str):
                    model = genai.GenerativeModel(model_name)
                    return model.generate_content(content)
                resp = await self._retry_with_backoff(
                    "gemini_chat",
                    _gemini_chat,
                    self.gemini_chat_model,
                    system_prompt + "\n\n" + user_prompt,
                )
                return resp.text
        except Exception as e:
            logger.warning(f"Gemini chat failed: {e}")

        return None


