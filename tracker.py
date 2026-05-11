"""Position tracker for Polymarket."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class Position:
    """Represents a Polymarket position."""
    market_id: str
    market_question: str
    side: str  # YES or NO
    amount: float
    entry_price: float
    current_price: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    opened_at: datetime = field(default_factory=datetime.now)
    closed: bool = False


class PositionTracker:
    """Track Polymarket positions and performance."""

    def __init__(self):
        self.positions: List[Position] = []
        self.closed_positions: List[Position] = []

    def open_position(self, market_id: str, market_question: str, 
                      side: str, amount: float, entry_price: float):
        """Record a new position."""
        pos = Position(
            market_id=market_id,
            market_question=market_question,
            side=side,
            amount=amount,
            entry_price=entry_price
        )
        self.positions.append(pos)
        return pos

    def update_prices(self, prices: Dict[str, float]):
        """Update current prices and calculate PnL."""
        for pos in self.positions:
            if pos.market_id in prices:
                pos.current_price = prices[pos.market_id]
                if pos.side == "YES":
                    pos.pnl = (pos.current_price - pos.entry_price) * pos.amount
                else:
                    pos.pnl = (pos.entry_price - pos.current_price) * pos.amount
                pos.pnl_percent = (pos.pnl / (pos.entry_price * pos.amount)) * 100 if pos.entry_price > 0 else 0

    def get_total_pnl(self) -> float:
        """Calculate total PnL across all open positions."""
        return sum(p.pnl for p in self.positions)

    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary."""
        total_invested = sum(p.entry_price * p.amount for p in self.positions)
        total_pnl = self.get_total_pnl()
        return {
            "open_positions": len(self.positions),
            "total_invested": total_invested,
            "total_pnl": total_pnl,
            "pnl_percent": (total_pnl / total_invested * 100) if total_invested > 0 else 0,
            "best_trade": max((p.pnl_percent for p in self.positions), default=0),
            "worst_trade": min((p.pnl_percent for p in self.positions), default=0)
        }
