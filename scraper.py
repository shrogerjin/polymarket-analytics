"""
Polymarket Analytics
Scrapes and analyzes prediction market data from Polymarket.
"""

import asyncio
import logging
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketPhase(Enum):
    TRADING = "trading"
    CLOSED = "closed"
    RESOLVED = "resolved"
    PENDING = "pending"


@dataclass
class Question:
    """A Polymarket question."""
    id: str
    question: str
    description: str
    markets: List["Market"]
    category: str
    created_at: datetime
    closes_at: Optional[datetime]
    phase: MarketPhase
    volume: float
    liquidity: float


@dataclass
class Market:
    """A market within a question."""
    outcome: str
    price: float  # CLOB price (cents)
    probability: float  # Derived probability
    volume: float
    top_bid: float
    top_ask: float
    share_amount: float


@dataclass
class PriceHistory:
    """Price history for a market."""
    timestamps: List[datetime]
    prices: List[float]
    volumes: List[float]


class PolymarketScraper:
    """Scrapes Polymarket API and subgraph."""

    GRAPH_URL = "https://api.thegraph.com/subgraphs/name/polymarket/matic-markets"
    API_BASE = "https://clob.polymarket.com"

    def __init__(self):
        self._session = None
        self._cache: Dict[str, dict] = {}
        self._cache_time: float = 0
        self._cache_ttl = 30  # seconds

    async def fetch_markets(self, limit: int = 50) -> List[Question]:
        """Fetch active markets."""
        # Simulated data for demo
        markets = []

        sample_questions = [
            ("Will ETH hit $5000 by end of 2026?", "crypto", 0.62),
            ("Will BTC exceed $100k in 2026?", "crypto", 0.45),
            ("Will FED cut rates 3+ times in 2026?", "macro", 0.55),
            ("Will AI pass AGI benchmark by 2027?", "tech", 0.25),
            ("Will Ethereum ETFs see $50B inflows in 2026?", "crypto", 0.70),
            ("Will a crypto exchange go bankrupt in 2026?", "crypto", 0.15),
            ("Will US unemployment exceed 5%?", "macro", 0.40),
            ("Will Solana process 10k TPS?", "tech", 0.50),
            ("Will a16z launch $10B crypto fund?", "crypto", 0.75),
            ("Will CBDC launch in major economy by 2027?", "macro", 0.35),
        ]

        for i, (q, cat, prob) in enumerate(sample_questions):
            mkt = Market(
                outcome="Yes",
                price=prob * 100,
                probability=prob,
                volume=10000 + i * 5000,
                top_bid=prob * 100 - 1,
                top_ask=prob * 100 + 1,
                share_amount=0,
            )
            mkt_no = Market(
                outcome="No",
                price=(1 - prob) * 100,
                probability=1 - prob,
                volume=10000 + i * 5000,
                top_bid=(1 - prob) * 100 - 1,
                top_ask=(1 - prob) * 100 + 1,
                share_amount=0,
            )

            question = Question(
                id=f"q_{i:04d}",
                question=q,
                description=f"Polymarket question about {cat}",
                markets=[mkt, mkt_no],
                category=cat,
                created_at=datetime.now() - timedelta(days=i * 2),
                closes_at=datetime.now() + timedelta(days=30 - i * 3),
                phase=MarketPhase.TRADING,
                volume=mkt.volume * mkt.price / 100 + mkt_no.volume * mkt_no.price / 100,
                liquidity=50000 + i * 10000,
            )
            markets.append(question)

        return markets

    async def get_market_price_history(self, question_id: str, hours: int = 24) -> PriceHistory:
        """Get price history for a market."""
        now = datetime.now()
        timestamps = []
        prices = []
        volumes = []

        base_price = 50.0
        for h in range(hours):
            t = now - timedelta(hours=hours - h)
            timestamps.append(t)
            variation = ((h % 6) - 3) * 0.5
            price = max(1, min(99, base_price + variation))
            prices.append(price)
            volumes.append(1000 + h * 50)

        return PriceHistory(timestamps=timestamps, prices=prices, volumes=volumes)

    async def get_top_markets(self, category: str = "", limit: int = 20) -> List[Question]:
        """Get top markets by volume."""
        all_markets = await self.fetch_markets(limit * 2)
        if category:
            all_markets = [m for m in all_markets if m.category == category]

        return sorted(all_markets, key=lambda m: m.volume, reverse=True)[:limit]


class MarketAnalyzer:
    """Analyzes prediction market data."""

    def __init__(self):
        self.scraper = PolymarketScraper()

    async def analyze_market(self, question: Question) -> dict:
        """Analyze a single market."""
        yes_market = question.markets[0] if question.markets[0].outcome == "Yes" else question.markets[1]
        no_market = question.markets[1] if yes_market.outcome == "Yes" else question.markets[0]

        # Calculate spread
        spread = yes_market.top_ask - yes_market.top_bid

        # Calculate volume imbalance
        vol_balance = yes_market.volume / (yes_market.volume + no_market.volume) if (yes_market.volume + no_market.volume) > 0 else 0.5

        # Confidence score
        confidence = min(100, (1 - spread / 100) * 100)

        return {
            "question": question.question,
            "yes_price": yes_market.price,
            "no_price": no_market.price,
            "probability": yes_market.probability,
            "spread_bps": spread * 100,
            "volume_balance": vol_balance,
            "confidence": confidence,
            "volume_usd": question.volume,
            "liquidity": question.liquidity,
        }

    async def detect_arbitrage(self, questions: List[Question]) -> List[dict]:
        """Detect cross-market arbitrage opportunities."""
        opportunities = []

        # Compare Polymarket prices to conventional sources
        external_predictions = {
            "crypto": {"bullish": 0.65, "bearish": 0.35},
            "macro": {"bullish": 0.50, "bearish": 0.50},
            "tech": {"bullish": 0.45, "bearish": 0.55},
        }

        for q in questions:
            external = external_predictions.get(q.category, {"bullish": 0.5, "bearish": 0.5})
            yes_prob = q.markets[0].probability if q.markets[0].outcome == "Yes" else q.markets[1].probability

            diff = abs(yes_prob - external["bullish"])
            if diff > 0.20:
                opportunities.append({
                    "question": q.question,
                    "polymarket_yes": yes_prob,
                    "external_estimate": external["bullish"],
                    "difference": diff,
                    "edge": diff * q.liquidity,
                })

        return opportunities

    async def calculate_funding_rate(self, question: Question, historical_prices: List[float]) -> float:
        """Calculate implied funding rate."""
        if len(historical_prices) < 2:
            return 0.0

        start_price = historical_prices[0]
        end_price = historical_prices[-1]
        hours_elapsed = len(historical_prices)

        if hours_elapsed == 0:
            return 0.0

        annualized = ((end_price / start_price) - 1) * (365 * 24 / hours_elapsed)
        return annualized * 100  # percentage

    async def generate_market_report(self, questions: List[Question]) -> str:
        """Generate a comprehensive market report."""
        if not questions:
            return "No markets to report."

        total_volume = sum(q.volume for q in questions)
        avg_prob = sum(q.markets[0].probability for q in questions) / len(questions)

        report_lines = [
            "=" * 60,
            "POLYMARKET ANALYTICS REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
            "=" * 60,
            f"Total Active Questions: {len(questions)}",
            f"Aggregate Volume: ${total_volume:,.2f}",
            f"Average Yes Probability: {avg_prob:.1%}",
            "",
            "TOP MARKETS BY VOLUME:",
            "-" * 60,
        ]

        for q in sorted(questions, key=lambda x: x.volume, reverse=True)[:10]:
            yes_prob = q.markets[0].probability if q.markets[0].outcome == "Yes" else q.markets[1].probability
            report_lines.append(f"  [{q.category.upper()}] {q.question[:50]}...")
            report_lines.append(f"    Yes: {yes_prob:.1%} | Volume: ${q.volume:,.2f} | Closes: {q.closes_at.strftime('%Y-%m-%d') if q.closes_at else 'TBD'}")

        report_lines.append("-" * 60)
        return "\n".join(report_lines)


class Tracker:
    """Tracks markets over time."""

    def __init__(self):
        self.price_history: Dict[str, List[Tuple[datetime, float]]] = {}
        self.alerts: List[dict] = []

    async def track_market(self, question_id: str, scraper: PolymarketScraper):
        """Track a market over time."""
        history = await scraper.get_market_price_history(question_id, hours=24)

        if question_id not in self.price_history:
            self.price_history[question_id] = []

        for ts, price in zip(history.timestamps, history.prices):
            self.price_history[question_id].append((ts, price))

    async def detect_price_move(self, question_id: str, threshold_pct: float = 10) -> Optional[dict]:
        """Detect significant price movements."""
        if question_id not in self.price_history:
            return None

        history = self.price_history[question_id]
        if len(history) < 2:
            return None

        start_price = history[0][1]
        end_price = history[-1][1]
        change_pct = abs((end_price - start_price) / start_price) * 100

        if change_pct >= threshold_pct:
            return {
                "question_id": question_id,
                "start_price": start_price,
                "end_price": end_price,
                "change_pct": change_pct,
                "timestamp": history[-1][0],
            }

        return None

    def get_price_trend(self, question_id: str) -> str:
        """Get price trend direction."""
        if question_id not in self.price_history or len(self.price_history[question_id]) < 3:
            return "insufficient_data"

        prices = [p for _, p in self.price_history[question_id]]
        if prices[-1] > prices[0]:
            return "bullish"
        elif prices[-1] < prices[0]:
            return "bearish"
        return "neutral"


class PolymarketAnalytics:
    """Main Polymarket analytics system."""

    def __init__(self, config: dict):
        self.config = config
        self.scraper = PolymarketScraper()
        self.analyzer = MarketAnalyzer()
        self.tracker = Tracker()
        self._stats = {"markets_analyzed": 0, "arbitrage_found": 0}

    async def run_analysis(self):
        """Run the analytics loop."""
        logger.info("Starting Polymarket Analytics...")

        # Fetch markets
        markets = await self.scraper.fetch_markets(limit=50)
        logger.info(f"Fetched {len(markets)} markets")

        # Analyze each market
        for market in markets:
            analysis = await self.analyzer.analyze_market(market)
            self._stats["markets_analyzed"] += 1

            if analysis["spread_bps"] > 200:
                logger.info(f"High spread detected: {market.question[:40]}...")

        # Check for arbitrage
        arb_opps = await self.analyzer.detect_arbitrage(markets)
        self._stats["arbitrage_found"] = len(arb_opps)

        for opp in arb_opps:
            logger.info(f"Arbitrage: {opp['question'][:40]}... | Edge: {opp['difference']:.1%}")

        # Generate report
        report = await self.analyzer.generate_market_report(markets)
        print(report)

        logger.info(f"Analysis complete. Stats: {self._stats}")


async def main():
    """Main entry point."""
    config = {
        "track_categories": ["crypto", "macro", "tech"],
        "alert_threshold_spread_bps": 150,
    }

    analytics = PolymarketAnalytics(config)
    await analytics.run_analysis()


if __name__ == "__main__":
    asyncio.run(main())