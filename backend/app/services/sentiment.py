"""
Simple keyword-based sentiment analyzer for financial news headlines.
Uses predefined word lists - no ML dependencies, no API costs.
"""

from typing import Optional

# Positive financial sentiment words
POSITIVE_WORDS = {
    # Strong positive
    "surge", "soar", "jump", "rally", "boom", "breakout", "record", "best",
    "beat", "exceed", "outperform", "upgrade", "bullish", "gain", "profit",
    "growth", "expand", "rise", "climb", "advance", "recover", "rebound",
    # Moderate positive
    "up", "higher", "positive", "strong", "good", "better", "improve",
    "increase", "win", "success", "opportunity", "optimistic", "confident",
    "buy", "accumulate", "overweight", "recommend", "approve", "launch",
    "innovation", "breakthrough", "milestone", "partnership", "deal",
}

# Negative financial sentiment words
NEGATIVE_WORDS = {
    # Strong negative
    "crash", "plunge", "tank", "collapse", "crisis", "disaster", "worst",
    "miss", "fail", "downgrade", "bearish", "loss", "decline", "drop",
    "fall", "sink", "tumble", "slump", "selloff", "sell-off", "warning",
    # Moderate negative
    "down", "lower", "negative", "weak", "bad", "worse", "concern",
    "decrease", "cut", "reduce", "risk", "threat", "uncertainty", "fear",
    "sell", "underweight", "avoid", "reject", "delay", "lawsuit", "fraud",
    "investigation", "recall", "layoff", "layoffs", "restructure",
}

# Amplifier words that increase sentiment magnitude
AMPLIFIERS = {
    "very", "extremely", "significantly", "sharply", "dramatically",
    "massive", "huge", "major", "big", "substantial", "record",
}

# Negation words that flip sentiment
NEGATORS = {
    "not", "no", "never", "neither", "without", "lack", "fail", "failed",
    "barely", "hardly", "unlikely", "despite",
}


def score_sentiment(text: str) -> float:
    """
    Calculate sentiment score for a text.

    Args:
        text: Text to analyze (typically a headline)

    Returns:
        Score from -1.0 (very negative) to 1.0 (very positive)
    """
    if not text:
        return 0.0

    words = text.lower().split()
    words_set = set(words)

    positive_count = 0
    negative_count = 0
    amplifier_present = bool(words_set & AMPLIFIERS)
    negator_present = bool(words_set & NEGATORS)

    for word in words:
        # Clean punctuation
        clean_word = word.strip(".,!?;:'\"()[]")

        if clean_word in POSITIVE_WORDS:
            positive_count += 1
        elif clean_word in NEGATIVE_WORDS:
            negative_count += 1

    # Calculate base score
    total = positive_count + negative_count
    if total == 0:
        return 0.0

    score = (positive_count - negative_count) / total

    # Apply amplifier (increase magnitude)
    if amplifier_present:
        score *= 1.5

    # Apply negator (flip sentiment)
    if negator_present:
        score *= -0.5  # Partial flip, negation is often imperfect

    # Clamp to [-1, 1]
    return max(-1.0, min(1.0, score))


def aggregate_sentiment(texts: list[str]) -> Optional[float]:
    """
    Calculate average sentiment across multiple texts.

    Args:
        texts: List of texts to analyze

    Returns:
        Average sentiment score, or None if no texts
    """
    if not texts:
        return None

    scores = [score_sentiment(text) for text in texts]
    return sum(scores) / len(scores)


def get_sentiment_label(score: float) -> str:
    """
    Convert sentiment score to human-readable label.

    Args:
        score: Sentiment score (-1 to 1)

    Returns:
        Label string
    """
    if score >= 0.5:
        return "Very Positive"
    elif score >= 0.2:
        return "Positive"
    elif score > -0.2:
        return "Neutral"
    elif score > -0.5:
        return "Negative"
    else:
        return "Very Negative"
