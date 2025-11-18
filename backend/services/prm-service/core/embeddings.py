"""
Embeddings Service
Generate vector embeddings for semantic search
"""
from typing import List
from loguru import logger
from openai import AsyncOpenAI

from core.config import settings as config


class EmbeddingsService:
    """
    Generate text embeddings using OpenAI API

    Uses text-embedding-3-small model with 384 dimensions
    for optimal balance between quality and performance.
    """

    def __init__(self):
        if not config.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not configured - embeddings will fail")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

        self.model = "text-embedding-3-small"
        self.dimensions = 384

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for list of texts

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (each is list of floats)

        Raises:
            ValueError: If OpenAI API key not configured
            Exception: If API call fails
        """
        if not self.client:
            raise ValueError("OPENAI_API_KEY not configured")

        if not texts:
            return []

        try:
            logger.debug(f"Generating embeddings for {len(texts)} texts")

            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dimensions
            )

            embeddings = [item.embedding for item in response.data]

            logger.debug(f"Generated {len(embeddings)} embeddings of dimension {self.dimensions}")

            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}", exc_info=True)
            raise

    async def embed_single(self, text: str) -> List[float]:
        """
        Generate embedding for single text

        Convenience method that wraps embed()
        """
        embeddings = await self.embed([text])
        return embeddings[0] if embeddings else []


# Global instance
embeddings_service = EmbeddingsService()
