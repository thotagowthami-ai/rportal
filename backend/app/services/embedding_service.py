from anthropic import Anthropic
from app.config import settings
from app.utils.llm_guard import llm_guard
import numpy as np
import logging
import hashlib
from typing import List, Optional
from app.services.cache_service import cache_service
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.cache_ttl = 86400  # 24 hours
        self.client: Optional[Anthropic] = None

        # Claude is OPTIONAL
        api_key = getattr(settings, "CLAUDE_API_KEY", None)

        if api_key:
            try:
                self.client = Anthropic(api_key=api_key)
                logger.info("Claude client initialized for embeddings")
            except Exception as e:
                logger.warning(f"Claude init failed, using local embeddings: {e}")
        else:
            logger.warning("CLAUDE_API_KEY not set. Using local deterministic embeddings.")

    def _generate_cache_key(self, text: str) -> str:
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"embedding:{text_hash}"

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        is_safe, sanitized_text = llm_guard.sanitize_user_input(text)

        if not is_safe:
            logger.warning("Potentially malicious text detected in embedding generation")

        cache_key = self._generate_cache_key(sanitized_text)
        cached = cache_service.get(cache_key)
        if cached:
            return cached

        try:
            # 🔹 If Claude is available → use it
            if self.client:
                safe_prompt = llm_guard.wrap_in_safe_context(
                    sanitized_text,
                    context_type="job_description",
                )

                response = await run_in_threadpool(
                    self.client.messages.create,
                    model=settings.CLAUDE_MODEL,
                    max_tokens=100,
                    messages=[
                        {
                            "role": "user",
                            "content": (
                                "Generate a semantic summary (max 50 words):\n\n"
                                f"{safe_prompt[:2000]}"
                            ),
                        }
                    ],
                )

                if (
                    not getattr(response, "content", None)
                    or not response.content
                    or not getattr(response.content[0], "text", None)
                    or not response.content[0].text.strip()
                ):
                    logger.warning("Claude returned empty or invalid content, using fallback local embedding")
                    embedding = self._text_to_vector(sanitized_text)
                else:
                    summary = response.content[0].text
                    embedding = self._text_to_vector(summary)

            # 🔹 Otherwise → local deterministic fallback
            else:
                embedding = self._text_to_vector(sanitized_text)

            cache_service.set(cache_key, embedding, ttl=self.cache_ttl)
            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    def _text_to_vector(self, text: str) -> List[float]:
        seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        vector = rng.standard_normal(1024)
        vector = vector / np.linalg.norm(vector)
        return vector.tolist()

    async def generate_batch_embeddings(
        self, texts: List[str], batch_size: int = 10
    ) -> List[Optional[List[float]]]:
        embeddings = []
        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            for text in chunk:
                embeddings.append(await self.generate_embedding(text))
        return embeddings


# ✅ SAFE global instance
embedding_service = EmbeddingService()