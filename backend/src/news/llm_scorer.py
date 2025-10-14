from __future__ import annotations

import time
from dataclasses import dataclass

from ..infra.logger import JsonlEventLogger
from .cache import get_cached, set_cached


@dataclass
class ScoredNews:
    title: str
    summary: str
    impact_score: float  # -1..+1 bias
    topic: str | None = None


def score_with_llm(titles_and_summaries: list[tuple[str, str]]) -> list[ScoredNews]:
    """
    Placeholder for LLM summarization and impact scoring.
    Replace with OpenAI or local LLM call; return normalized impact_score.
    """
    out: list[ScoredNews] = []
    logger = JsonlEventLogger()
    for title, summary in titles_and_summaries:
        key_text = f"{title} {summary}"
        cached = get_cached(key_text)
        if cached is not None:
            score = float(cached.get("impact", 0.0))
        else:
            score = 0.0
            lower = key_text.lower()
            if any(
                k in lower
                for k in [
                    "approval",
                    "etf",
                    "integration",
                    "launch",
                    "partnership",
                    "upgrade",
                ]
            ):
                score = 0.4
            if any(
                k in lower
                for k in ["hack", "ban", "lawsuit", "delay", "halt", "exploit"]
            ):
                score = -0.6
            set_cached(key_text, {"impact": score, "ts": time.time()})
        out.append(ScoredNews(title=title, summary=summary, impact_score=score))
        logger.write("NEWS_SCORE", {"title": title, "impact": score})
    return out
