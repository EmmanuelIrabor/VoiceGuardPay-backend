"""
Classifies a transcribed utterance: is it a transactional command,
and if so, extract structured payment details (amount, recipient name).

Uses Azure OpenAI (a Foundry/OpenAI resource — separate from the Speech
resource used for STT/TTS) for classification.
"""

import json
import httpx
from app.core.config import settings

SYSTEM_PROMPT = """You classify spoken utterances for a payments app.
Determine if the utterance is a TRANSACTIONAL COMMAND (the user wants to
send/pay money right now) versus ORDINARY SPEECH (conversation, unrelated
talk, or describing a past payment rather than instructing one).

If transactional, extract:
- action: "pay" or "transfer"
- amount: a number, in NGN (Nigerian Naira). Convert any spoken phrasing
  like "5k" or "5,000" into a plain number.
- recipient: the name as stated, or null if unclear.

If not transactional, set is_transactional to false and leave the other
fields null.

Respond ONLY with valid JSON, no other text, no markdown formatting:
{"is_transactional": true, "action": "pay", "amount": 5000, "recipient": "Sarah"}
"""


async def classify_utterance(text: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments/"
            f"{settings.AZURE_OPENAI_DEPLOYMENT}/chat/completions"
            f"?api-version=2024-06-01",
            headers={
                "api-key": settings.AZURE_OPENAI_KEY,
                "Content-Type": "application/json",
            },
            json={
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return json.loads(content)