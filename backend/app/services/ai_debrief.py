"""
AI Trade Debrief service.
Analyzes trades using local Ollama (qwen3.5:9b) and produces structured feedback.
"""
import json
import logging
import time
from datetime import datetime, date, timezone
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.models import Trade, JournalEntry, Screenshot, Tag

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen3.5:9b"
CACHE_TTL_SECONDS = 3600  # cache lives 1 hour

# In-memory cache: trade_id -> {result, timestamp}
_debrief_cache: dict[int, dict] = {}

# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

TRADE_DEBRIEF_SYSTEM_PROMPT = """You are an expert trading coach and analyst. Review the trade details below and provide a structured analysis in valid JSON only.

Your response must be a single JSON object with these exact keys:
- "analysis": A 2-3 paragraph analysis of what happened in the trade (strengths, weaknesses, decision quality)
- "entry_rating": One of "Excellent", "Good", "Average", "Poor", "Bad"
- "exit_rating": One of "Excellent", "Good", "Average", "Poor", "Bad"
- "risk_management": A 1-2 paragraph assessment of risk management
- "emotional_state": Analysis of the trader's emotional state based on journal entries
- "lessons_learned": Array of 2-5 specific, actionable lessons
- "overall_score": Integer 1-10 (10 = perfect trade)

Be honest and constructive. Focus on process over outcome — a losing trade can have good process, and a winning trade can have bad habits.
Return ONLY valid JSON, no markdown, no backticks, no other text."""

AUTO_TAG_SYSTEM_PROMPT = """You are a trading journal analyst. Based on the trade details below, suggest relevant tags that describe the trading behavior, patterns, and psychology.

Return ONLY a JSON array of tag strings (max 5 tags). Examples: "fomo_entry", "held_too_long", "good_rr", "scalp", "breakout", "revenge_trading", "planned_trade", "cut_losses_early", "let_runners", "overtrading", "emotional", "discipline_good", "missed_exit". Return ONLY valid JSON array, no other text."""

DAILY_SUMMARY_SYSTEM_PROMPT = """You are a trading coach reviewing today's performance. Based on the list of today's trades below, provide a daily summary.

Return ONLY valid JSON with these exact keys:
- "summary": A 2-3 paragraph daily performance summary
- "best_trade": Brief description of the best trade today
- "worst_trade": Brief description of the worst trade today
- "pattern_observed": A key pattern or behavior to work on
- "tip_for_tomorrow": One specific actionable tip
- "daily_score": Integer 1-10
Return ONLY valid JSON, no markdown, no backticks."""

# ---------------------------------------------------------------------------
# Core: call Ollama
# ---------------------------------------------------------------------------


async def _call_ollama(prompt: str, system_prompt: str, timeout: int = 60) -> str:
    """Send a prompt to Ollama and return the raw response text."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "temperature": 0.3,
        "max_tokens": 2000,
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(OLLAMA_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
    except httpx.ConnectError:
        logger.warning("Ollama not running at %s", OLLAMA_URL)
        raise ConnectionError(
            "Ollama is not running. Please start it with: ollama run qwen3.5:9b"
        )
    except httpx.TimeoutException:
        logger.warning("Ollama request timed out after %ds", timeout)
        raise TimeoutError("Ollama request timed out. The model might be busy.")
    except Exception as e:
        logger.error("Ollama API error: %s", e)
        raise RuntimeError(f"Ollama API error: {e}")


def _extract_json(text: str) -> dict:
    """Extract and parse JSON from model output, handling markdown fences."""
    text = text.strip()
    # Remove markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first and last fence lines
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object or array in the text
    import re

    # Look for { ... } or [ ... ]
    for pattern in [r"\{.*\}", r"\[.*\]"]:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    logger.error("Could not parse JSON from Ollama response: %s", text[:500])
    raise ValueError("Failed to parse structured output from AI model")


# ---------------------------------------------------------------------------
# Trade context builder
# ---------------------------------------------------------------------------


def _build_trade_context(trade: Trade) -> str:
    """Build a detailed trade description string for the prompt."""
    instr = trade.instrument
    symbol = instr.symbol if instr else f"ID:{trade.instrument_id}"
    direction = trade.direction.upper()
    status = trade.status
    volume = trade.volume or 0

    lines = [
        f"Trade #{trade.id}",
        f"Instrument: {symbol}",
        f"Direction: {direction}",
        f"Volume: {volume}",
        f"Entry Price: ${trade.entry_price:.2f}" if trade.entry_price else "Entry Price: N/A",
        f"Exit Price: ${trade.exit_price:.2f}" if trade.exit_price else "Exit Price: N/A (still open)",
        f"Entry Time: {trade.entry_time.isoformat() if trade.entry_time else 'N/A'}",
        f"Exit Time: {trade.exit_time.isoformat() if trade.exit_time else 'N/A'}",
        f"PnL: ${trade.pnl:.2f}" if trade.pnl is not None else "PnL: N/A",
        f"PnL%: {trade.pnl_pct:.2f}%" if trade.pnl_pct is not None else "",
        f"Status: {status}",
        f"Strategy: {trade.strategy_tag or 'N/A'}",
        f"Broker: {trade.broker or 'N/A'}",
        f"Commission: ${trade.commission:.2f}" if trade.commission else "",
        f"Rating (1-5): {trade.rating}" if trade.rating else "",
        f"Notes: {trade.notes}" if trade.notes else "",
    ]

    # Legs (scaling in/out)
    legs = trade.legs or []
    if legs:
        lines.append("\nTrade Legs:")
        for leg in legs:
            lines.append(
                f"  - [{leg.type}] Price: ${leg.price:.2f}, Vol: {leg.volume}, "
                f"Time: {leg.time.isoformat() if leg.time else 'N/A'}"
            )

    # Journal entries
    entries = trade.journal_entries or []
    if entries:
        lines.append(f"\nJournal Entries ({len(entries)}):")
        for je in sorted(entries, key=lambda x: x.created_at or datetime.min):
            lines.append(f"  - [{je.created_at.isoformat() if je.created_at else ''}] "
                         f"Sentiment: {je.sentiment or 'N/A'} | {je.content[:200]}")
            if je.mood_before:
                lines.append(f"    Mood before: {je.mood_before}")
            if je.mood_after:
                lines.append(f"    Mood after: {je.mood_after}")

    # Screenshots
    screenshots = trade.screenshots or []
    if screenshots:
        lines.append(f"\nScreenshots ({len(screenshots)}):")
        for ss in sorted(screenshots, key=lambda x: x.captured_at or datetime.min):
            lines.append(f"  - Type: {ss.type}, Captured: {ss.captured_at.isoformat() if ss.captured_at else 'N/A'}")

    # Tags
    tags = trade.tags or []
    if tags:
        lines.append(f"\nTags: {', '.join(t.name for t in tags)}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def analyze_trade(db: Session, trade_id: int) -> dict:
    """
    Analyze a trade using Ollama. Returns structured JSON debrief.
    Caches results per trade_id for CACHE_TTL_SECONDS.
    """
    now = time.time()

    # Check cache
    cached = _debrief_cache.get(trade_id)
    if cached and (now - cached["timestamp"]) < CACHE_TTL_SECONDS:
        logger.info("Returning cached debrief for trade %d", trade_id)
        return cached["result"]

    # Load trade with all relationships eagerly
    trade = (
        db.query(Trade)
        .filter(Trade.id == trade_id)
        .first()
    )
    if not trade:
        raise ValueError(f"Trade #{trade_id} not found")

    # Build context
    context = _build_trade_context(trade)

    # Call Ollama
    raw = await _call_ollama(
        prompt=f"Please review this trade:\n\n{context}",
        system_prompt=TRADE_DEBRIEF_SYSTEM_PROMPT,
    )

    result = _extract_json(raw)

    # Validate required keys, fill defaults
    defaults = {
        "analysis": "Analysis not available.",
        "entry_rating": "Average",
        "exit_rating": "Average",
        "risk_management": "Risk management analysis not available.",
        "emotional_state": "Emotional state analysis not available.",
        "lessons_learned": [],
        "overall_score": 5,
    }
    for key, default in defaults.items():
        if key not in result:
            result[key] = default

    # Ensure overall_score is int 1-10
    score = result.get("overall_score", 5)
    try:
        score = int(score)
    except (ValueError, TypeError):
        score = 5
    result["overall_score"] = max(1, min(10, score))

    # Ensure lessons_learned is a list
    if not isinstance(result.get("lessons_learned"), list):
        result["lessons_learned"] = [str(result.get("lessons_learned", ""))] if result.get("lessons_learned") else []

    # Cache the result
    _debrief_cache[trade_id] = {
        "result": result,
        "timestamp": now,
    }

    return result


def get_cached_debrief(trade_id: int) -> Optional[dict]:
    """Get a cached debrief if available and fresh."""
    cached = _debrief_cache.get(trade_id)
    if cached and (time.time() - cached["timestamp"]) < CACHE_TTL_SECONDS:
        return cached["result"]
    return None


async def auto_tag_trade(db: Session, trade_id: int) -> list[str]:
    """
    Suggest tags for a trade based on AI analysis.
    Returns a list of suggested tag strings.
    """
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise ValueError(f"Trade #{trade_id} not found")

    context = _build_trade_context(trade)
    raw = await _call_ollama(
        prompt=f"Suggest tags for this trade:\n\n{context}",
        system_prompt=AUTO_TAG_SYSTEM_PROMPT,
    )

    result = _extract_json(raw)

    # result should be a list; if it's a dict with tags key, handle that
    if isinstance(result, dict):
        for key in ("tags", "suggested_tags", "tag_list"):
            if key in result and isinstance(result[key], list):
                result = result[key]
                break

    if not isinstance(result, list):
        logger.warning("Auto-tag returned unexpected format: %s", type(result))
        return []

    # Clean tags: lowercase, strip, max 30 chars
    cleaned = []
    for tag in result:
        if isinstance(tag, str):
            t = tag.strip().lower().replace(" ", "_")[:30]
            if t:
                cleaned.append(t)
        elif isinstance(tag, dict) and "name" in tag:
            t = str(tag["name"]).strip().lower().replace(" ", "_")[:30]
            if t:
                cleaned.append(t)

    return cleaned[:5]


async def generate_daily_summary(db: Session, target_date: Optional[str] = None) -> dict:
    """
    Generate a daily summary of trades for a given date (default: today).
    """
    if target_date:
        try:
            day = datetime.fromisoformat(target_date).date()
        except (ValueError, TypeError):
            day = date.today()
    else:
        day = date.today()

    start_dt = datetime(day.year, day.month, day.day, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(day.year, day.month, day.day, 23, 59, 59, tzinfo=timezone.utc)

    trades = (
        db.query(Trade)
        .filter(
            Trade.entry_time >= start_dt,
            Trade.entry_time <= end_dt,
        )
        .order_by(Trade.entry_time.asc())
        .all()
    )

    if not trades:
        return {
            "summary": f"No trades found for {day.isoformat()}.",
            "best_trade": "N/A",
            "worst_trade": "N/A",
            "pattern_observed": "N/A",
            "tip_for_tomorrow": "Take a trade tomorrow!",
            "daily_score": None,
        }

    # Build context
    lines = [f"Daily Summary for {day.isoformat()}", f"Total Trades: {len(trades)}\n"]
    for t in trades:
        symbol = t.instrument.symbol if t.instrument else f"ID:{t.instrument_id}"
        pnl_str = f"${t.pnl:.2f}" if t.pnl is not None else "open"
        lines.append(
            f"Trade #{t.id}: {symbol} {t.direction.upper()} "
            f"Entry ${t.entry_price:.2f} → Exit ${t.exit_price:.2f if t.exit_price else 'N/A'} "
            f"PnL: {pnl_str}"
        )
        if t.notes:
            lines.append(f"  Notes: {t.notes[:200]}")

    context = "\n".join(lines)
    raw = await _call_ollama(
        prompt=f"Review today's trades:\n\n{context}",
        system_prompt=DAILY_SUMMARY_SYSTEM_PROMPT,
    )

    result = _extract_json(raw)

    # Ensure defaults
    defaults = {
        "summary": "Summary not available.",
        "best_trade": "N/A",
        "worst_trade": "N/A",
        "pattern_observed": "N/A",
        "tip_for_tomorrow": "Keep trading your plan.",
        "daily_score": None,
    }
    for key, default in defaults.items():
        if key not in result:
            result[key] = default

    # Validate score
    score = result.get("daily_score")
    if score is not None:
        try:
            score = int(score)
            result["daily_score"] = max(1, min(10, score))
        except (ValueError, TypeError):
            result["daily_score"] = None

    return result
