"""
Flask Blueprint routes package
Modular API endpoints organized by domain
"""

# Import blueprints (conditional imports to avoid errors)
try:
    from backend.api.routes.portfolio import portfolio_bp
except ImportError:
    portfolio_bp = None

try:
    from backend.api.routes.orders import orders_bp
except ImportError:
    orders_bp = None

try:
    from backend.api.routes.market_data import market_data_bp
except ImportError:
    market_data_bp = None

try:
    from backend.api.routes.alerts import alerts_bp
except ImportError:
    alerts_bp = None

try:
    from backend.api.routes.strategies import strategies_bp
except ImportError:
    strategies_bp = None

try:
    from backend.api.routes.backtest import backtest_bp
except ImportError:
    backtest_bp = None

try:
    from backend.api.routes.analytics import analytics_bp
except ImportError:
    analytics_bp = None

try:
    from backend.api.routes.admin import admin_bp
except ImportError:
    admin_bp = None

# List of all blueprints to register (filter out None values)
ALL_BLUEPRINTS = [
    bp for bp in [
        portfolio_bp,
        orders_bp,
        market_data_bp,
        alerts_bp,
        strategies_bp,
        backtest_bp,
        analytics_bp,
        admin_bp,
    ] if bp is not None
]

__all__ = [
    'ALL_BLUEPRINTS',
    'portfolio_bp',
    'orders_bp',
    'market_data_bp',
    'alerts_bp',
    'strategies_bp',
    'backtest_bp',
    'analytics_bp',
    'admin_bp',
]
