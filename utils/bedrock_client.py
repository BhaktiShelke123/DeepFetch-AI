"""AWS Bedrock client for LLM + local embeddings (free)."""

import json
import logging
from typing import Optional

import boto3
import numpy as np
from botocore.exceptions import ClientError
from sentence_transformers import SentenceTransformer

from config import config

logger = logging.getLogger(__name__)


class BedrockClient:
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            "bedrock-runtime",
            region_name=config.AWS_REGION,
        )
        self.model_id = config.BEDROCK_MODEL_ID

        # Free local embedding model (no AWS cost)
        logger.info("Loading local embedding model (first time may download ~90MB)...")
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.embedding_dimension = 384  # This model outputs 384-dim vectors
        logger.info("Embedding model loaded.")

    def invoke_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.2,
    ) -> str:
        messages = [{"role": "user", "content": prompt}]
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system_prompt:
            body["system"] = system_prompt

        try:
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )
            result = json.loads(response["body"].read())
            return result["content"][0]["text"]
        except ClientError as e:
            logger.error(f"Bedrock LLM call failed: {e}")
            raise

    def get_embedding(self, text: str) -> list[float]:
        vector = self.embedding_model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        vectors = self.embedding_model.encode(texts, normalize_embeddings=True)
        return vectors.tolist()


_client: Optional[BedrockClient] = None

def get_bedrock_client() -> BedrockClient:
    global _client
    if _client is None:
        _client = BedrockClient()
    return _client