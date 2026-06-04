"""AWS Bedrock client with streaming for Sigma DataTech Pipeline Forge."""
import boto3
import json
import logging
from typing import Generator

logger = logging.getLogger(__name__)

# Claude 3.5 Haiku — cross-region inference profile (us-east-1)
# Fast, cheap ($0.80/1M input · $4.00/1M output), great at code generation
MODEL_ID = 'us.amazon.nova-lite-v1:0'

# Pricing per 1M tokens (USD)
INPUT_PRICE_PER_M = 0.06   # Amazon Nova Lite pricing
OUTPUT_PRICE_PER_M = 0.24


class BedrockClient:
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.client = boto3.client('bedrock-runtime', region_name=region)
        self.model_id = MODEL_ID
        self._input_tokens = 0
        self._output_tokens = 0

    # ── Streaming ───────────────────────────────────────────────────────────────
    def stream_message(
        self,
        prompt: str,
        system: str = '',
        max_tokens: int = 4096
    ) -> Generator[str, None, None]:
        content = (f"{system}\n\n{prompt}") if system else prompt
        body = {
            "messages": [{"role": "user", "content": [{"text": content}]}],
            "inferenceConfig": {"maxTokens": max_tokens},
        }

        response = self.client.invoke_model_with_response_stream(
            modelId=self.model_id,
            body=json.dumps(body)
        )

        for event in response['body']:
            chunk = json.loads(event['chunk']['bytes'])
            # Nova Lite streaming format
            if 'contentBlockDelta' in chunk:
                yield chunk['contentBlockDelta'].get('delta', {}).get('text', '')
            elif 'metadata' in chunk:
                usage = chunk['metadata'].get('usage', {})
                self._input_tokens += usage.get('inputTokens', 0)
                self._output_tokens += usage.get('outputTokens', 0)

    # ── One-shot invoke ─────────────────────────────────────────────────────────
    def invoke(self, prompt: str, system: str = '', max_tokens: int = 4096) -> str:
        return ''.join(self.stream_message(prompt, system, max_tokens))

    # ── Cost tracking ───────────────────────────────────────────────────────────
    def get_cost_usd(self) -> float:
        input_cost = (self._input_tokens / 1_000_000) * INPUT_PRICE_PER_M
        output_cost = (self._output_tokens / 1_000_000) * OUTPUT_PRICE_PER_M
        return round(input_cost + output_cost, 6)

    def reset_cost(self):
        self._input_tokens = 0
        self._output_tokens = 0

    @property
    def tokens_used(self) -> dict:
        return {'input': self._input_tokens, 'output': self._output_tokens}

    # ── Health check ────────────────────────────────────────────────────────────
    def test_connection(self) -> bool:
        try:
            result = self.invoke("Reply with the single word: OK", max_tokens=10)
            return len(result.strip()) < 20
        except Exception as e:
            logger.error(f"Bedrock connection failed: {e}")
            return False
