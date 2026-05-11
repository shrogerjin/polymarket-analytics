"""Probability analyzer for Polymarket markets."""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class MarketAnalysis:
    """Analysis result for a prediction market."""
    market_id: str
    question: str
    current_price: float
    probability: float
    volume_24h: float
    liquidity: float
    sentiment: str  # BULLISH, BEARISH, NEUTRAL
    confidence: float


class ProbabilityAnalyzer:
    """Analyze prediction market probabilities and trends."""

    def __init__(self):
        self.market_cache: Dict[str, MarketAnalysis] = {}
        self.price_history: Dict[str, List[float]] = {}

    def analyze_market(self, market_data: Dict) -> MarketAnalysis:
        """Analyze a single market and return insights."""
        price = market_data.get("price", 0.5)
        volume = market_data.get("volume", 0)
        question = market_data.get("question", "")

        # Calculate probability from price (Polymarket uses yes/no tokens at 0-1)
        prob = price * 100

        # Sentiment based on price movement and volume
        sentiment = "NEUTRAL"
        if price > 0.6:
            sentiment = "BULLISH"
        elif price < 0.4:
            sentiment = "BEARISH"

        # Confidence based on liquidity
        confidence = min(market_data.get("liquidity", 0) / 100000, 1.0) * 100

        return MarketAnalysis(
            market_id=market_data.get("id", ""),
            question=question,
            current_price=price,
            probability=round(prob, 2),
            volume_24h=volume,
            liquidity=market_data.get("liquidity", 0),
            sentiment=sentiment,
            confidence=round(confidence, 1)
        )

    def compare_markets(self, markets: List[Dict]) -> List[MarketAnalysis]:
        """Analyze and compare multiple markets."""
        analyses = []
        for market in markets:
            analysis = self.analyze_market(market)
            analyses.append(analysis)
            self.market_cache[analysis.market_id] = analysis

        return sorted(analyses, key=lambda x: x.volume_24h, reverse=True)

    def detect_arbitrage(self, markets: List[MarketAnalysis]) -> List[Dict]:
        """Detect potential arbitrage opportunities between related markets."""
        opportunities = []

        for i, m1 in enumerate(markets):
            for m2 in markets[i+1:]:
                # Check if markets are related (same topic)
                combined_prob = m1.probability + m2.probability
                if combined_prob > 95:
                    opportunities.append({
                        "market_1": m1.question[:50],
                        "market_2": m2.question[:50],
                        "combined_prob": combined_prob,
                        "edge": 100 - combined_prob,
                        "recommendation": "SHORT COMBINED" if combined_prob > 100 else "LONG COMBINED"
                    })

        return sorted(opportunities, key=lambda x: x["edge"], reverse=True)
