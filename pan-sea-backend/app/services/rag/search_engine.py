import json
import logging
import re
from typing import Any, Dict, List, Optional

import numpy as np

from app.database.database import db_manager
from app.core.cache import cache_service, CacheKeys


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


class SearchEngine:
    def __init__(self, embedding_client):
        self.embedding_client = embedding_client

    def _clamp_limit(self, limit: int) -> int:
        try:
            value = int(limit)
        except Exception:
            value = 10
        if value < 1:
            value = 1
        if value > 50:
            value = 50
        return value

    async def _extract_relevant_excerpt(self, full_text: str, query: str, max_length: int = 300) -> str:
        try:
            sentences = re.split(r"[.!?]+", full_text)
            query_words = set(query.lower().split())
            relevant_sentences: List[str] = []
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 10:
                    continue
                sentence_words = set(sentence.lower().split())
                if query_words.intersection(sentence_words):
                    relevant_sentences.append(sentence)
            if not relevant_sentences:
                relevant_sentences = sentences[:3]
            excerpt = ""
            for sentence in relevant_sentences:
                if len(excerpt + sentence) > max_length:
                    break
                excerpt += sentence.strip() + ". "
            return excerpt.strip() or full_text[:max_length] + "..."
        except Exception as e:
            logger.error(f"Error extracting excerpt: {str(e)}")
            return full_text[:max_length] + "..."

    def get_supported_subjects(self) -> List[str]:
        return list(self._get_domain_expansions().keys())

    def get_subject_keywords(self, subject: str) -> Dict[str, List[str]]:
        domain_expansions = self._get_domain_expansions()
        return domain_expansions.get(subject.lower(), {})

    def _get_domain_expansions(self) -> Dict[str, Dict[str, List[str]]]:
        # Copied from original with no changes
        return {
            "biology": {
                "dna": ["dna", "genetic material", "nucleic acid", "chromosome", "gene", "genetics"],
                "cell": ["cell", "cellular", "cytoplasm", "membrane", "organelle", "cytology"],
                "evolution": ["evolution", "natural selection", "adaptation", "species", "darwin", "evolutionary"],
                "moon": ["moon", "lunar", "satellite", "theia", "collision", "impact", "formation"],
                "earth": ["earth", "planet", "terrestrial", "formation", "geology", "planetary"],
                "protein": ["protein", "amino acid", "enzyme", "polypeptide", "biochemistry"],
                "metabolism": ["metabolism", "metabolic", "energy", "atp", "cellular respiration", "biochemical"],
                "photosynthesis": ["photosynthesis", "chlorophyll", "light reaction", "calvin cycle", "glucose"],
                "mitosis": ["mitosis", "cell division", "chromosome", "prophase", "metaphase", "anaphase"],
                "ecosystem": ["ecosystem", "environment", "ecology", "habitat", "biodiversity", "biome"],
            },
            "chemistry": {
                "atom": ["atom", "atomic", "nucleus", "electron", "proton", "neutron", "element"],
                "molecule": ["molecule", "molecular", "compound", "chemical bond", "covalent", "ionic"],
                "reaction": ["reaction", "chemical reaction", "catalyst", "reactant", "product", "equation"],
                "acid": ["acid", "acidic", "ph", "hydrogen ion", "proton donor", "corrosive"],
                "base": ["base", "basic", "alkaline", "hydroxide", "ph", "proton acceptor"],
                "periodic": ["periodic table", "element", "group", "period", "atomic number", "mendeleev"],
                "organic": ["organic", "carbon", "hydrocarbon", "functional group", "polymer"],
                "bond": ["chemical bond", "covalent", "ionic", "metallic", "hydrogen bond", "intermolecular"],
            },
            "physics": {
                "force": ["force", "newton", "acceleration", "momentum", "energy", "mechanics"],
                "energy": ["energy", "kinetic", "potential", "conservation", "work", "power"],
                "wave": ["wave", "frequency", "wavelength", "amplitude", "oscillation", "vibration"],
                "light": ["light", "photon", "electromagnetic", "optics", "reflection", "refraction"],
                "electricity": ["electricity", "current", "voltage", "resistance", "circuit", "electrical"],
                "magnetism": ["magnetism", "magnetic field", "electromagnet", "pole", "flux"],
                "quantum": ["quantum", "quantum mechanics", "particle", "uncertainty", "wave-particle"],
                "relativity": ["relativity", "einstein", "spacetime", "gravity", "mass-energy"],
            },
            "mathematics": {
                "algebra": ["algebra", "equation", "variable", "polynomial", "linear", "quadratic"],
                "calculus": ["calculus", "derivative", "integral", "limit", "differential", "function"],
                "geometry": ["geometry", "triangle", "circle", "angle", "area", "volume", "shape"],
                "statistics": ["statistics", "probability", "mean", "median", "distribution", "data"],
                "trigonometry": ["trigonometry", "sine", "cosine", "tangent", "angle", "triangle"],
                "matrix": ["matrix", "vector", "linear algebra", "determinant", "eigenvalue"],
                "function": ["function", "domain", "range", "graph", "polynomial", "exponential"],
            },
            "history": {
                "war": ["war", "battle", "conflict", "military", "army", "warfare", "combat"],
                "empire": ["empire", "kingdom", "dynasty", "civilization", "ruler", "territory"],
                "revolution": ["revolution", "uprising", "rebellion", "reform", "change", "movement"],
                "democracy": ["democracy", "government", "voting", "election", "political", "republic"],
                "industrial": ["industrial revolution", "factory", "manufacturing", "technology", "steam"],
                "ancient": ["ancient", "civilization", "archaeological", "historical", "antiquity"],
                "medieval": ["medieval", "middle ages", "feudal", "knight", "castle", "monarchy"],
            },
            "literature": {
                "poetry": ["poetry", "poem", "verse", "rhyme", "metaphor", "literary device"],
                "novel": ["novel", "fiction", "narrative", "character", "plot", "story"],
                "drama": ["drama", "play", "theater", "dialogue", "act", "scene", "performance"],
                "theme": ["theme", "motif", "symbol", "meaning", "interpretation", "analysis"],
                "author": ["author", "writer", "poet", "playwright", "novelist", "literary"],
                "genre": ["genre", "style", "literary form", "category", "classification"],
                "rhetoric": ["rhetoric", "persuasion", "argument", "speech", "oratory", "discourse"],
            },
        }

    async def _enhance_query(self, query: str, subject: Optional[str] = None) -> Dict[str, Any]:
        try:
            enhanced_query: Dict[str, Any] = {
                "original": query,
                "expanded_terms": [],
                "entities": [],
                "search_strategies": [],
                "detected_subjects": [],
            }
            query_lower = query.lower()
            domain_expansions = self._get_domain_expansions()
            search_domains: List[str] = []
            if subject and subject.lower() in domain_expansions:
                search_domains = [subject.lower()]
                enhanced_query["detected_subjects"].append(subject.lower())
            else:
                search_domains = list(domain_expansions.keys())
            for domain in search_domains:
                domain_terms = domain_expansions.get(domain, {})
                found_match = False
                for key, expansions in domain_terms.items():
                    if key in query_lower:
                        enhanced_query["expanded_terms"].extend(expansions)
                        if domain not in enhanced_query["detected_subjects"]:
                            enhanced_query["detected_subjects"].append(domain)
                        found_match = True
                if not subject and found_match:
                    logger.debug(f"Detected subject domain: {domain}")
            if not enhanced_query["expanded_terms"]:
                enhanced_query["expanded_terms"] = query.lower().split()
            seen = set()
            unique_terms: List[str] = []
            for term in enhanced_query["expanded_terms"]:
                if term not in seen:
                    seen.add(term)
                    unique_terms.append(term)
            enhanced_query["expanded_terms"] = unique_terms
            enhanced_query["search_strategies"] = [
                {"type": "exact", "query": query},
                {"type": "expanded", "query": " OR ".join(enhanced_query["expanded_terms"][:5])},
                {"type": "semantic", "query": query},
            ]
            if enhanced_query["detected_subjects"]:
                subject_terms: List[str] = []
                for detected_subject in enhanced_query["detected_subjects"]:
                    if detected_subject in domain_expansions:
                        subject_domain = domain_expansions[detected_subject]
                        for terms in list(subject_domain.values())[:3]:
                            subject_terms.extend(terms[:2])
                if subject_terms:
                    enhanced_query["search_strategies"].append(
                        {"type": "subject_context", "query": " OR ".join(list(set(subject_terms))[:10])}
                    )
            return enhanced_query
        except Exception as e:
            logger.error(f"Error enhancing query: {str(e)}")
            return {
                "original": query,
                "expanded_terms": [query],
                "search_strategies": [{"type": "exact", "query": query}],
                "detected_subjects": [],
            }

    async def _semantic_search_pgvector(
        self,
        query: str,
        class_id: Optional[str] = None,
        lesson_id: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        try:
            limit = self._clamp_limit(limit)
            try:
                test_query = "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
                test_result = await db_manager.execute_query(test_query)
                pgvector_available = len(test_result) > 0
            except Exception:
                pgvector_available = False
            if not pgvector_available:
                return await self._semantic_search(query, class_id, lesson_id, limit, similarity_threshold)
            query_embedding = await self.embedding_client.generate_embedding(query)
            if not query_embedding:
                return []
            query_vector = np.array(query_embedding)
            base_query = (
                """
                SELECT l.id, l.class_id, l.lecture_title, l.transcription, l.created_at,
                       1 - (l.embedding_vector <=> $1) as similarity_score,
                       c.class_code as class_title, c.subject
                FROM lessons l
                JOIN classes c ON l.class_id = c.id
                WHERE l.transcription IS NOT NULL 
                AND l.embedding_vector IS NOT NULL
                """
            )
            params: List[Any] = [query_vector.tolist()]
            if lesson_id:
                base_query += " AND l.id = $" + str(len(params) + 1)
                params.append(str(lesson_id))
            elif class_id:
                base_query += " AND l.class_id = $" + str(len(params) + 1)
                params.append(str(class_id))
            base_query += f" AND (1 - (l.embedding_vector <=> $1)) >= ${len(params) + 1}"
            params.append(similarity_threshold)
            base_query += f" ORDER BY l.embedding_vector <=> $1 LIMIT ${len(params) + 1}"
            params.append(limit)
            lesson_records = await db_manager.execute_query(base_query, *params)
            if not lesson_records:
                return []
            results: List[Dict[str, Any]] = []
            for row in lesson_records:
                try:
                    excerpt = await self._extract_relevant_excerpt(row["transcription"], query, max_length=300)
                    results.append(
                        {
                            "id": row["id"],
                            "similarity_score": float(row["similarity_score"]),
                            "transcription": excerpt,
                            "lecture_title": row["lecture_title"],
                            "class_id": row["class_id"],
                            "created_at": row["created_at"],
                            "class_title": row.get("class_title", ""),
                            "subject": row.get("subject", ""),
                            "search_method": "pgvector_cosine",
                        }
                    )
                except Exception as e:
                    logger.error(f"Error processing lesson record {row.get('id')}: {str(e)}")
                    continue
            return results
        except Exception as e:
            logger.error(f"Error in pgvector semantic search: {str(e)}")
            return await self._semantic_search(query, class_id, lesson_id, limit, similarity_threshold)

    async def _semantic_search(
        self,
        query: str,
        class_id: Optional[str] = None,
        lesson_id: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        try:
            limit = self._clamp_limit(limit)
            query_embedding = await self.embedding_client.generate_embedding(query)
            if not query_embedding:
                return []
            base_query = (
                """
                SELECT l.id, l.class_id, l.lecture_title, l.transcription, l.embedding, l.created_at,
                       c.class_code as class_title, c.subject
                FROM lessons l
                JOIN classes c ON l.class_id = c.id
                WHERE l.transcription IS NOT NULL AND l.embedding IS NOT NULL
                """
            )
            params: List[Any] = []
            if lesson_id:
                base_query += " AND l.id = $1"
                params.append(str(lesson_id))
            elif class_id:
                base_query += " AND l.class_id = $1"
                params.append(str(class_id))
            base_query += " ORDER BY l.created_at DESC"
            lesson_records = await db_manager.execute_query(base_query, *params)
            if not lesson_records:
                return []
            results: List[Dict[str, Any]] = []
            for row in lesson_records:
                try:
                    stored_embedding = row["embedding"]
                    if isinstance(stored_embedding, str):
                        stored_embedding = json.loads(stored_embedding)
                    elif not isinstance(stored_embedding, list):
                        continue
                    similarity = _cosine_similarity(query_embedding, stored_embedding)
                    if similarity >= similarity_threshold:
                        excerpt = await self._extract_relevant_excerpt(row["transcription"], query, max_length=300)
                        results.append(
                            {
                                "id": row["id"],
                                "similarity_score": similarity,
                                "transcription": excerpt,
                                "lecture_title": row["lecture_title"],
                                "class_id": row["class_id"],
                                "created_at": row["created_at"],
                                "class_title": row.get("class_title", ""),
                                "subject": row.get("subject", ""),
                            }
                        )
                except Exception as e:
                    logger.error(f"Error processing lesson record {row.get('id')}: {str(e)}")
                    continue
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return results[:limit]
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return []

    async def _fallback_text_search(
        self, query: str, class_id: Optional[str] = None, lesson_id: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        try:
            limit = self._clamp_limit(limit)
            base_query = (
                """
                SELECT l.id, l.class_id, l.lecture_title, l.transcription, l.created_at,
                       c.class_code as class_title, c.subject
                FROM lessons l
                JOIN classes c ON l.class_id = c.id
                WHERE l.transcription IS NOT NULL 
                AND l.transcription ILIKE $1
                """
            )
            params: List[Any] = [f"%{query}%"]
            if lesson_id:
                base_query += " AND l.id = $2"
                params.append(str(lesson_id))
            elif class_id:
                base_query += " AND l.class_id = $2"
                params.append(str(class_id))
            base_query += " ORDER BY l.created_at DESC LIMIT $3"
            params.append(limit)
            lesson_records = await db_manager.execute_query(base_query, *params)
            results: List[Dict[str, Any]] = []
            if lesson_records:
                for row in lesson_records:
                    try:
                        excerpt = await self._extract_relevant_excerpt(row["transcription"], query, max_length=300)
                        results.append(
                            {
                                "id": row["id"],
                                "similarity_score": 0.5,
                                "transcription": excerpt,
                                "lecture_title": row["lecture_title"],
                                "class_id": row["class_id"],
                                "created_at": row["created_at"],
                                "class_title": row.get("class_title", ""),
                                "subject": row.get("subject", ""),
                            }
                        )
                    except Exception as e:
                        logger.error(f"Error processing lesson record {row.get('id')}: {str(e)}")
                        continue
            return results
        except Exception as e:
            logger.error(f"Error in fallback text search: {str(e)}")
            return []

    async def search_audio_transcriptions(
        self,
        query: str,
        class_id: Optional[str] = None,
        subject: Optional[str] = None,
        lesson_id: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        try:
            limit = self._clamp_limit(limit)
            # Redis cache key (lesson-scoped queries bypass wide cache to ensure freshness)
            cache_key = None
            if not lesson_id:
                cache_key = cache_service.generate_key(
                    CacheKeys.AUDIO_RECORDING,
                    "search",
                    query,
                    class_id or "*",
                    subject or "*",
                    str(limit),
                    str(similarity_threshold),
                )
                cached = await cache_service.get(cache_key)
                if isinstance(cached, list):
                    return cached
            enhanced_query = await self._enhance_query(query, subject)
            if lesson_id:
                focused_result = await self._search_within_specific_lesson(
                    query=query, lesson_id=lesson_id, similarity_threshold=similarity_threshold
                )
                return [focused_result] if focused_result else []
            query_embedding = await self.embedding_client.generate_embedding(query)
            all_results: List[Dict[str, Any]] = []
            if query_embedding:
                try:
                    pgvector_results = await self._semantic_search_pgvector(
                        query, class_id, lesson_id, limit, similarity_threshold * 0.8
                    )
                    if pgvector_results:
                        for result in pgvector_results:
                            result["search_strategy"] = "semantic_pgvector"
                            result["original_similarity"] = result.get("similarity_score", 0)
                        all_results.extend(pgvector_results)
                    else:
                        semantic_results = await self._semantic_search(
                            query, class_id, lesson_id, limit, similarity_threshold * 0.8
                        )
                        for result in semantic_results:
                            result["search_strategy"] = "semantic_manual"
                            result["original_similarity"] = result.get("similarity_score", 0)
                        all_results.extend(semantic_results)
                except Exception:
                    semantic_results = await self._semantic_search(
                        query, class_id, lesson_id, limit, similarity_threshold * 0.8
                    )
                    for result in semantic_results:
                        result["search_strategy"] = "semantic_manual"
                        result["original_similarity"] = result.get("similarity_score", 0)
                    all_results.extend(semantic_results)
            expanded_query = " ".join(enhanced_query["expanded_terms"][:5])
            keyword_results = await self._fallback_text_search(expanded_query, class_id, lesson_id, limit)
            for result in keyword_results:
                result["search_strategy"] = "keyword_expanded"
                result["similarity_score"] = result.get("similarity_score", 0.4) + 0.1
            all_results.extend(keyword_results)
            if enhanced_query.get("detected_subjects"):
                for strategy in enhanced_query["search_strategies"]:
                    if strategy["type"] == "subject_context":
                        subject_results = await self._fallback_text_search(strategy["query"], class_id, lesson_id, limit)
                        for result in subject_results:
                            result["search_strategy"] = "subject_context"
                            result["similarity_score"] = result.get("similarity_score", 0.3) + 0.15
                        all_results.extend(subject_results)
                        break
            seen_ids = set()
            final_results: List[Dict[str, Any]] = []
            for result in all_results:
                result_id = result.get("id")
                if result_id not in seen_ids:
                    seen_ids.add(result_id)
                    is_semantic = "semantic" in str(result.get("search_strategy", ""))
                    semantic_score = result.get("original_similarity", result.get("similarity_score", 0)) if is_semantic else 0
                    keyword_score = 0.4 if result.get("search_strategy") == "keyword_expanded" else 0
                    subject_score = 0.3 if result.get("search_strategy") == "subject_context" else 0
                    strategy_boost = 0.2 if len([r for r in all_results if r.get("id") == result_id]) > 1 else 0
                    subject_bonus = 0.1 if enhanced_query.get("detected_subjects") and subject else 0
                    final_score = max(semantic_score, keyword_score, subject_score) + strategy_boost + subject_bonus
                    result["combined_relevance_score"] = final_score
                    result["detected_subjects"] = enhanced_query.get("detected_subjects", [])
                    final_results.append(result)
            final_results.sort(key=lambda x: x.get("combined_relevance_score", x.get("similarity_score", 0)), reverse=True)
            final_results = final_results[:limit]
            if cache_key:
                try:
                    await cache_service.set(cache_key, final_results, ttl=300)
                except Exception:
                    pass
            return final_results
        except Exception as e:
            logger.error(f"Error in enhanced search: {str(e)}")
            try:
                return await self._fallback_text_search(query, class_id, lesson_id, limit)
            except Exception:
                return []

    async def _search_within_specific_lesson(
        self, query: str, lesson_id: str, similarity_threshold: float = 0.0
    ) -> Optional[Dict[str, Any]]:
        try:
            lesson_query = (
                """
                SELECT l.id, l.class_id, l.lecture_title, l.transcription, l.embedding, l.created_at,
                       c.class_code as class_title, c.subject
                FROM lessons l
                JOIN classes c ON l.class_id = c.id
                WHERE l.id = $1 AND l.transcription IS NOT NULL
                """
            )
            lesson_rows = await db_manager.execute_query(lesson_query, str(lesson_id))
            if not lesson_rows:
                return None
            row = lesson_rows[0]
            similarity_score = 0.0
            try:
                stored_embedding = row.get("embedding")
                if isinstance(stored_embedding, str):
                    stored_embedding = json.loads(stored_embedding)
                if isinstance(stored_embedding, list) and len(stored_embedding) > 0:
                    query_embedding = await self.embedding_client.generate_embedding(query)
                    if query_embedding:
                        similarity_score = _cosine_similarity(query_embedding, stored_embedding)
            except Exception as sim_err:
                logger.warning(f"Similarity computation failed for lesson {lesson_id}: {sim_err}")
            excerpt = await self._extract_relevant_excerpt(row["transcription"], query, max_length=300)
            return {
                "id": row["id"],
                "similarity_score": float(similarity_score),
                "transcription": excerpt,
                "lecture_title": row.get("lecture_title", ""),
                "class_id": row.get("class_id"),
                "created_at": row.get("created_at"),
                "class_title": row.get("class_title", ""),
                "subject": row.get("subject", ""),
                "search_strategy": "lesson_scoped",
            }
        except Exception as e:
            logger.error(f"Error in single-lesson search: {e}")
            return None

    async def search_lecture_summaries(
        self, query: str, class_id: Optional[str] = None, limit: int = 10, similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        try:
            limit = self._clamp_limit(limit)
            base_query = (
                """
                SELECT ls.*, c.class_code as class_title, c.subject
                FROM lesson_summaries ls
                JOIN classes c ON ls.class_id = c.id
                WHERE (ls.summary ILIKE $1 
                       OR ls.topics_discussed::text ILIKE $1 
                       OR ls.learning_objectives::text ILIKE $1 
                       OR ls.key_points::text ILIKE $1)
                """
            )
            params: List[Any] = [f"%{query}%"]
            if class_id:
                base_query += " AND ls.class_id = $2"
                params.append(str(class_id))
            base_query += " ORDER BY ls.created_at DESC LIMIT $3"
            params.append(limit)
            summary_records = await db_manager.execute_query(base_query, *params)
            results: List[Dict[str, Any]] = []
            if summary_records:
                for row in summary_records:
                    try:
                        topics_discussed = json.loads(row.get("topics_discussed", "[]"))
                        learning_objectives = json.loads(row.get("learning_objectives", "[]"))
                        key_points = json.loads(row.get("key_points", "[]"))
                        excerpt = await self._extract_relevant_excerpt(row["summary"], query, max_length=300)
                        results.append(
                            {
                                "id": row["id"],
                                "type": "summary",
                                "similarity_score": 0.6,
                                "summary": excerpt,
                                "topics_discussed": topics_discussed,
                                "learning_objectives": learning_objectives,
                                "key_points": key_points,
                                "duration": row.get("duration", 0),
                                "class_id": row["class_id"],
                                "created_at": row["created_at"],
                                "class_title": row["class_title"],
                                "subject": row["subject"],
                            }
                        )
                    except Exception as e:
                        logger.error(f"Error processing summary record {row.get('id')}: {str(e)}")
                        continue
            return results
        except Exception as e:
            logger.error(f"Error searching lecture summaries: {str(e)}")
            return []

    async def search_combined(
        self,
        query: str,
        class_id: Optional[str] = None,
        subject: Optional[str] = None,
        limit: int = 10,
        include_transcriptions: bool = True,
        include_summaries: bool = True,
    ) -> Dict[str, Any]:
        try:
            results: Dict[str, Any] = {
                "query": query,
                "subject": subject,
                "transcriptions": [],
                "summaries": [],
                "combined": [],
            }
            if include_transcriptions:
                transcription_results = await self.search_audio_transcriptions(
                    query, class_id, subject, None, limit // 2 if include_summaries else limit
                )
                results["transcriptions"] = transcription_results
                for result in transcription_results:
                    result["type"] = "transcription"
                    results["combined"].extend(transcription_results)
            if include_summaries:
                summary_results = await self.search_lecture_summaries(
                    query, class_id, limit // 2 if include_transcriptions else limit
                )
                results["summaries"] = summary_results
                results["combined"].extend(summary_results)
            results["combined"].sort(
                key=lambda x: x.get("combined_relevance_score", x.get("similarity_score", 0)), reverse=True
            )
            results["combined"] = results["combined"][:limit]
            return results
        except Exception as e:
            logger.error(f"Error in combined search: {str(e)}")
            return {
                "query": query,
                "subject": subject,
                "transcriptions": [],
                "summaries": [],
                "combined": [],
                "error": str(e),
            }

    async def get_audio_by_class(self, class_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            limit = self._clamp_limit(limit)
            query = (
                "SELECT l.id, l.class_id, l.lecture_title, l.transcription, l.created_at, "
                "c.class_code as class_title, c.subject "
                "FROM lessons l JOIN classes c ON l.class_id = c.id "
                "WHERE l.class_id = $1 ORDER BY l.created_at DESC LIMIT $2"
            )
            lesson_records = await db_manager.execute_query(query, str(class_id), limit)
            results: List[Dict[str, Any]] = []
            if lesson_records:
                for row in lesson_records:
                    transcription_excerpt = (row.get("transcription", "") or "")[:300]
                    results.append(
                        {
                            "id": row["id"],
                            "transcription": transcription_excerpt,
                            "lecture_title": row.get("lecture_title", ""),
                            "class_id": row.get("class_id"),
                            "created_at": row.get("created_at"),
                            "class_title": row.get("class_title", ""),
                            "subject": row.get("subject", ""),
                        }
                    )
            return results
        except Exception as e:
            logger.error(f"Error getting audio by class: {str(e)}")
            return []


