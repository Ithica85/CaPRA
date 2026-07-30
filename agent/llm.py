"""
Multi-provider LLM client: Anthropic (preferred), OpenAI, Perplexity.

Uses tenacity for light retries on rate limits / transient errors.
Returns raw text; JSON parsing happens in the analyzer.
"""

from __future__ import annotations

import logging
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from agent.config import Settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when all LLM attempts fail or response is unusable."""


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        from agent.config import _normalize_anthropic_model

        self.settings = settings
        self.provider, self.model, self.api_key = settings.resolve_llm()
        if self.provider == "anthropic":
            self.model = _normalize_anthropic_model(self.model)
        logger.info("LLM provider=%s model=%s", self.provider, self.model)

    @retry(
        retry=retry_if_exception_type(LLMError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        reraise=True,
    )
    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 8192,
    ) -> str:
        """Single-turn completion. Low temperature for consistent structured JSON."""
        try:
            if self.provider == "anthropic":
                # Never pass temperature — Claude Sonnet 5+ rejects it as deprecated.
                return self._anthropic(system, user, max_tokens)
            if self.provider == "openai":
                return self._openai(system, user, temperature, max_tokens)
            if self.provider == "perplexity":
                return self._perplexity(system, user, temperature, max_tokens)
            raise LLMError(f"Unknown provider: {self.provider}")
        except LLMError:
            raise
        except Exception as exc:
            msg = str(exc).lower()
            if any(
                s in msg
                for s in ("rate", "429", "timeout", "overloaded", "529", "capacity")
            ):
                logger.warning("Retryable LLM error: %s", exc)
                raise LLMError(str(exc)) from exc
            logger.exception("LLM call failed")
            raise LLMError(str(exc)) from exc

    def _anthropic(self, system: str, user: str, max_tokens: int) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)
        candidates = [self.model]
        for alt in ("claude-sonnet-5", "claude-sonnet-4-6", "claude-sonnet-4-5-20250929"):
            if alt not in candidates:
                candidates.append(alt)

        last_err: Exception | None = None
        msg = None
        for model_id in candidates:
            # IMPORTANT: do not send temperature — rejected on Claude 5 / 4.6+.
            create_kwargs = {
                "model": model_id,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }
            try:
                msg = client.messages.create(**create_kwargs)
                if model_id != self.model:
                    logger.warning(
                        "Model %s unavailable; used %s instead", self.model, model_id
                    )
                    self.model = model_id
                break
            except Exception as exc:
                last_err = exc
                err_s = str(exc).lower()
                if "not_found" in err_s or "404" in err_s:
                    logger.warning(
                        "Anthropic model %s not found, trying next…", model_id
                    )
                    continue
                raise
        if msg is None:
            raise last_err or LLMError("Anthropic returned no response")
        parts: list[str] = []
        for block in msg.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        text = "".join(parts).strip()
        if not text:
            raise LLMError("Empty response from Anthropic")
        return text

    def _openai(
        self, system: str, user: str, temperature: float, max_tokens: int
    ) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        resp = client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
        )
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            raise LLMError("Empty response from OpenAI")
        return text

    def _perplexity(
        self, system: str, user: str, temperature: float, max_tokens: int
    ) -> str:
        """
        Perplexity exposes an OpenAI-compatible Chat Completions API.
        Useful when you want web-grounded reasoning as a secondary path.
        """
        from openai import OpenAI

        client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.perplexity.ai",
        )
        resp = client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            raise LLMError("Empty response from Perplexity")
        return text

    def info(self) -> dict[str, Any]:
        return {"provider": self.provider, "model": self.model}
