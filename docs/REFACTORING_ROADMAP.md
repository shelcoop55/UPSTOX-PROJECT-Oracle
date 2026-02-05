# 🗺️ Step-by-Step Refactoring Roadmap

**Project:** UPSTOX Trading Platform  
**Document Version:** 1.0  
**Last Updated:** February 5, 2026  
**Timeline:** 16 Weeks (4 Months)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Phase 1: Foundation (Weeks 1-2)](#phase-1-foundation-weeks-1-2)
3. [Phase 2: Security Hardening (Weeks 3-4)](#phase-2-security-hardening-weeks-3-4)
4. [Phase 3: Performance (Weeks 5-6)](#phase-3-performance-weeks-5-6)
5. [Phase 4: Testing (Weeks 7-10)](#phase-4-testing-weeks-7-10)
6. [Phase 5: Documentation (Weeks 11-12)](#phase-5-documentation-weeks-11-12)
7. [Phase 6: Scalability (Weeks 13-16)](#phase-6-scalability-weeks-13-16)
8. [Success Metrics](#success-metrics)
9. [Risk Management](#risk-management)

---

## Overview

### Goals

1. **Improve Code Quality:** From 75/100 to 92/100
2. **Enhance Security:** From 70/100 to 95/100
3. **Increase Test Coverage:** From 15% to 85%
4. **Boost Performance:** Reduce p95 latency from 250ms to 100ms
5. **Enable Scalability:** Support 1,000+ concurrent users

### Principles

- **Incremental changes:** Small, testable improvements
- **No breaking changes:** Maintain backward compatibility
- **Test everything:** Comprehensive test coverage
- **Document as you go:** Keep docs updated
- **Feature flags:** Roll out gradually

---

## Phase 1: Foundation (Weeks 1-2)

### Goal
Refactor monolithic Flask app into modular blueprints

### Success Criteria
- ✅ 52 routes split into 8 blueprints
- ✅ All tests passing
- ✅ No functionality broken
- ✅ Response times unchanged

---

### Week 1: Blueprint Setup & Portfolio Routes

#### Day 1-2: Setup Blueprint Structure

**Tasks:**
```bash
# 1. Create directory structure
mkdir -p backend/api/routes
touch backend/api/routes/__init__.py
touch backend/api/routes/{portfolio,orders,market_data,alerts,strategies,backtest,analytics,admin}.py

# 2. Create blueprint templates
```

**Files to create:**

```python
# backend/api/routes/portfolio.py
"""Portfolio management routes"""

from flask import Blueprint, jsonify, request, g
from backend.services.upstox.portfolio import PortfolioServicesV3
from backend.utils.auth.decorators import require_auth
from backend.utils.logging.config import get_logger

logger = get_logger(__name__)
portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api/portfolio')

@portfolio_bp.route('/', methods=['GET'])
@require_auth
def get_portfolio():
    """
    Get user portfolio holdings
    
    Returns:
        200: Portfolio data
        401: Unauthorized
        500: Server error
    """
    try:
        user_id = g.user_id
        logger.info(f"Fetching portfolio for user: {user_id}")
        
        portfolio_service = PortfolioServicesV3()
        data = portfolio_service.get_portfolio()
        
        return jsonify({
            'status': 'success',
            'data': data
        }), 200
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@portfolio_bp.route('/positions', methods=['GET'])
@require_auth
def get_positions():
    """Get open positions"""
    # Implementation
    pass

@portfolio_bp.route('/holdings', methods=['GET'])
@require_auth
def get_holdings():
    """Get holdings"""
    # Implementation
    pass
```

**Checklist:**
- [ ] Create `backend/api/routes/__init__.py`
- [ ] Create 8 blueprint files
- [ ] Add basic structure to each blueprint

---

#### Day 3-4: Migrate Portfolio Routes

**Tasks:**
1. Move portfolio routes from `api_server.py` to `portfolio.py`
2. Update imports
3. Test each endpoint

**Routes to migrate:**
- `GET /api/portfolio` → `portfolio_bp.route('/')`
- `GET /api/positions` → `portfolio_bp.route('/positions')`
- `GET /api/holdings` → `portfolio_bp.route('/holdings')`

**Testing:**
```python
# tests/api/test_portfolio_routes.py (NEW)
import pytest
from backend.api.servers.api_server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_portfolio_authenticated(client, mock_auth):
    """Test portfolio endpoint with valid auth"""
    response = client.get(
        '/api/portfolio/',
        headers={'Authorization': 'Bearer valid_token'}
    )
    assert response.status_code == 200
    assert 'data' in response.json

def test_get_portfolio_unauthorized(client):
    """Test portfolio endpoint without auth"""
    response = client.get('/api/portfolio/')
    assert response.status_code == 401
```

**Checklist:**
- [ ] Move 3 portfolio routes
- [ ] Update imports in `api_server.py`
- [ ] Write tests for each route
- [ ] Run tests: `pytest tests/api/test_portfolio_routes.py`
- [ ] Manual test with Postman/curl

---

#### Day 5-6: Migrate Order Routes

**Routes to migrate:**
- `GET /api/orders` → `orders_bp.route('/')`
- `POST /api/orders` → `orders_bp.route('/', methods=['POST'])`
- `PUT /api/orders/<order_id>` → `orders_bp.route('/<order_id>', methods=['PUT'])`
- `DELETE /api/orders/<order_id>` → `orders_bp.route('/<order_id>', methods=['DELETE'])`

**Example:**
```python
# backend/api/routes/orders.py
from flask import Blueprint, request, jsonify, g
from backend.utils.auth.decorators import require_auth
from backend.api.schemas.order_schema import OrderSchema
from marshmallow import ValidationError

orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')

@orders_bp.route('/', methods=['POST'])
@require_auth
def place_order():
    """
    Place a new order
    
    Request Body:
        {
            "symbol": "RELIANCE",
            "quantity": 10,
            "order_type": "MARKET",
            "product_type": "INTRADAY"
        }
    
    Returns:
        201: Order placed successfully
        400: Validation error
        401: Unauthorized
        500: Server error
    """
    try:
        # Validate input
        schema = OrderSchema()
        data = schema.load(request.get_json())
        
        # Place order
        user_id = g.user_id
        order_result = place_order_logic(user_id, data)
        
        return jsonify({
            'status': 'success',
            'order_id': order_result['order_id']
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'errors': e.messages
        }), 400
    except Exception as e:
        logger.error(f"Error placing order: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500
```

**Checklist:**
- [ ] Move 4 order routes
- [ ] Add input validation
- [ ] Write tests
- [ ] Manual testing

---

#### Day 7-10: Remaining Routes & Integration

**Routes to migrate:**

**Market Data (8 routes):**
- `GET /api/quotes/<symbol>`
- `GET /api/ohlc/<symbol>`
- `GET /api/option-chain/<symbol>`
- ...

**Alerts (5 routes):**
- `GET /api/alerts`
- `POST /api/alerts`
- `DELETE /api/alerts/<alert_id>`
- ...

**Strategies (6 routes):**
- `POST /api/strategies/calendar-spread`
- `POST /api/strategies/diagonal-spread`
- ...

**Backtest (4 routes):**
- `POST /api/backtest/run`
- `GET /api/backtest/results`
- ...

**Analytics (3 routes):**
- `GET /api/analytics/performance`
- `GET /api/analytics/equity-curve`
- ...

**Admin (3 routes):**
- `GET /api/health`
- `GET /api/logs`
- `GET /api/metrics`

**Integration Steps:**
1. Register all blueprints in `api_server.py`:

```python
# backend/api/servers/api_server.py
from backend.api.routes.portfolio import portfolio_bp
from backend.api.routes.orders import orders_bp
from backend.api.routes.market_data import market_data_bp
from backend.api.routes.alerts import alerts_bp
from backend.api.routes.strategies import strategies_bp
from backend.api.routes.backtest import backtest_bp
from backend.api.routes.analytics import analytics_bp
from backend.api.routes.admin import admin_bp

# Register blueprints
app.register_blueprint(portfolio_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(market_data_bp)
app.register_blueprint(alerts_bp)
app.register_blueprint(strategies_bp)
app.register_blueprint(backtest_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(admin_bp)
```

2. Remove old route definitions from `api_server.py`
3. Run full test suite
4. Manual API testing

**Checklist:**
- [ ] All 52 routes migrated
- [ ] Blueprints registered
- [ ] Old code removed from `api_server.py`
- [ ] All tests passing
- [ ] API documentation updated

---

### Week 2: Input Validation & Authentication

#### Day 1-3: Add Marshmallow Schemas

**Create schema files:**

```python
# backend/api/schemas/order_schema.py
from marshmallow import Schema, fields, validate, validates_schema, ValidationError

class OrderSchema(Schema):
    """Order placement/modification schema"""
    
    symbol = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=20),
        error_messages={'required': 'Symbol is required'}
    )
    
    quantity = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=100000),
        error_messages={'required': 'Quantity is required'}
    )
    
    order_type = fields.Str(
        required=True,
        validate=validate.OneOf(['MARKET', 'LIMIT', 'STOP_LOSS', 'STOP_LOSS_MARKET']),
        error_messages={'required': 'Order type is required'}
    )
    
    price = fields.Float(
        allow_none=True,
        validate=validate.Range(min=0.01)
    )
    
    trigger_price = fields.Float(
        allow_none=True,
        validate=validate.Range(min=0.01)
    )
    
    product_type = fields.Str(
        required=True,
        validate=validate.OneOf(['INTRADAY', 'DELIVERY', 'CO', 'OCO']),
        error_messages={'required': 'Product type is required'}
    )
    
    exchange = fields.Str(
        required=True,
        validate=validate.OneOf(['NSE', 'BSE', 'NFO', 'MCX']),
        error_messages={'required': 'Exchange is required'}
    )
    
    @validates_schema
    def validate_price_for_limit_order(self, data, **kwargs):
        """Ensure price is provided for LIMIT orders"""
        if data.get('order_type') == 'LIMIT' and not data.get('price'):
            raise ValidationError('Price is required for LIMIT orders', 'price')
    
    @validates_schema
    def validate_trigger_price(self, data, **kwargs):
        """Ensure trigger_price is provided for stop-loss orders"""
        if data.get('order_type') in ['STOP_LOSS', 'STOP_LOSS_MARKET']:
            if not data.get('trigger_price'):
                raise ValidationError('Trigger price required for stop-loss orders', 'trigger_price')
```

**Create more schemas:**

```python
# backend/api/schemas/alert_schema.py
class AlertSchema(Schema):
    symbol = fields.Str(required=True)
    condition = fields.Str(validate=validate.OneOf(['ABOVE', 'BELOW']))
    target_price = fields.Float(required=True, validate=validate.Range(min=0))
    notification_method = fields.Str(validate=validate.OneOf(['EMAIL', 'SMS', 'TELEGRAM']))

# backend/api/schemas/strategy_schema.py
class CalendarSpreadSchema(Schema):
    symbol = fields.Str(required=True)
    strike_price = fields.Float(required=True)
    near_expiry = fields.Date(required=True)
    far_expiry = fields.Date(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1))
```

**Apply schemas to routes:**

```python
# backend/api/routes/orders.py
from backend.api.schemas.order_schema import OrderSchema
from marshmallow import ValidationError

@orders_bp.route('/', methods=['POST'])
@require_auth
def place_order():
    schema = OrderSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    # Proceed with validated data
    ...
```

**Checklist:**
- [ ] Create schemas for all input types (orders, alerts, strategies)
- [ ] Apply schemas to all POST/PUT routes
- [ ] Write validation tests
- [ ] Test error messages

---

#### Day 4-5: Authentication Decorators

**Create authentication decorators:**

```python
# backend/utils/auth/decorators.py
from functools import wraps
from flask import request, jsonify, g
import jwt
from typing import List
import os

SECRET_KEY = os.getenv('JWT_SECRET_KEY')

def require_auth(f):
    """
    Require valid JWT authentication
    
    Usage:
        @app.route('/api/orders')
        @require_auth
        def get_orders():
            user_id = g.user_id
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.replace('Bearer ', '')
        
        try:
            # Verify JWT
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            
            # Inject user context
            g.user_id = payload['user_id']
            g.roles = payload.get('roles', ['user'])
            g.email = payload.get('email')
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_role(*required_roles: str):
    """
    Require specific role(s)
    
    Usage:
        @app.route('/api/admin/users')
        @require_role('admin')
        def get_all_users():
            ...
    """
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user_roles = g.roles
            
            # Check if user has any of the required roles
            if not any(role in user_roles for role in required_roles):
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_roles': list(required_roles),
                    'user_roles': user_roles
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def optional_auth(f):
    """
    Optional authentication (sets g.user_id if authenticated)
    
    Usage:
        @app.route('/api/quotes/<symbol>')
        @optional_auth
        def get_quote(symbol):
            user_id = g.get('user_id')  # May be None
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                g.user_id = payload['user_id']
                g.roles = payload.get('roles', ['user'])
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                pass  # Continue without auth
        
        return f(*args, **kwargs)
    
    return decorated_function
```

**Apply decorators to routes:**

```python
# backend/api/routes/orders.py
from backend.utils.auth.decorators import require_auth, require_role

@orders_bp.route('/', methods=['GET'])
@require_auth
def get_orders():
    user_id = g.user_id  # Injected by decorator
    # Fetch orders for user_id
    ...

@orders_bp.route('/', methods=['POST'])
@require_auth
def place_order():
    # Only authenticated users can place orders
    ...

# backend/api/routes/admin.py
@admin_bp.route('/users')
@require_role('admin')
def get_all_users():
    # Only admins can access this
    ...
```

**Checklist:**
- [ ] Create authentication decorators
- [ ] Apply to all protected routes
- [ ] Write tests for auth flows
- [ ] Test unauthorized access

---

#### Day 6-7: Security Headers & Configuration

**Add security middleware:**

```python
# backend/api/middleware/security.py
from flask import request, redirect, Response

def add_security_headers(app):
    """Add security headers to all responses"""
    
    @app.after_request
    def set_security_headers(response: Response) -> Response:
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HSTS (force HTTPS)
        if not app.debug:
            response.headers['Strict-Transport-Security'] = \
                'max-age=31536000; includeSubDomains; preload'
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = \
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'no-referrer-when-downgrade'
        
        return response
    
    @app.before_request
    def enforce_https():
        """Redirect HTTP to HTTPS in production"""
        if not app.debug and not request.is_secure:
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)
    
    return app
```

**Fix hardcoded secret key:**

```python
# backend/api/servers/api_server.py
import secrets
import os

# BEFORE (INSECURE)
app.config["SECRET_KEY"] = "upstox-trading-platform-secret"

# AFTER (SECURE)
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    if app.debug:
        # Generate temporary key for development
        secret_key = secrets.token_hex(32)
        logger.warning("⚠️ Using temporary SECRET_KEY in development mode")
    else:
        # Fail fast in production
        raise ValueError("SECRET_KEY environment variable not set")

app.config["SECRET_KEY"] = secret_key
```

**Update .env.example:**

```bash
# .env.example
UPSTOX_CLIENT_ID=your_client_id
UPSTOX_CLIENT_SECRET=your_client_secret
UPSTOX_REDIRECT_URI=http://localhost:5050/auth/callback

# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your_64_character_hex_string
JWT_SECRET_KEY=your_64_character_hex_string

# Encryption key for token storage
# Generate with: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
ENCRYPTION_KEY=your_fernet_key
```

**Checklist:**
- [ ] Add security headers middleware
- [ ] Fix hardcoded secret key
- [ ] Update .env.example
- [ ] Generate production keys
- [ ] Test HTTPS redirect (in production)

---

## Phase 2: Security Hardening (Weeks 3-4)

### Goal
Implement JWT authentication and rate limiting

### Week 3: JWT Authentication

#### Day 1-2: JWT Manager Implementation

**Create JWT manager:**

```python
# backend/utils/auth/jwt_manager.py
import jwt
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

class JWTManager:
    """Manage JWT token generation and validation"""
    
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY')
        self.algorithm = 'HS256'
        self.access_token_expiry = timedelta(hours=24)
        self.refresh_token_expiry = timedelta(days=30)
    
    def generate_access_token(self, user_id: str, email: str, roles: list) -> str:
        """Generate access token"""
        payload = {
            'user_id': user_id,
            'email': email,
            'roles': roles,
            'exp': datetime.utcnow() + self.access_token_expiry,
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def generate_refresh_token(self, user_id: str) -> str:
        """Generate refresh token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + self.refresh_token_expiry,
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = 'access') -> Optional[Dict]:
        """Verify and decode token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get('type') != token_type:
                raise jwt.InvalidTokenError(f"Invalid token type: expected {token_type}")
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token"""
        payload = self.verify_token(refresh_token, token_type='refresh')
        if not payload:
            return None
        
        # Fetch user details from database
        user = get_user_by_id(payload['user_id'])
        if not user:
            return None
        
        return self.generate_access_token(
            user_id=user['user_id'],
            email=user['email'],
            roles=user['roles']
        )
```

**Create authentication endpoints:**

```python
# backend/api/routes/auth.py
from flask import Blueprint, request, jsonify
from backend.utils.auth.jwt_manager import JWTManager
from backend.api.schemas.auth_schema import LoginSchema, RegisterSchema
from marshmallow import ValidationError
import bcrypt

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
jwt_manager = JWTManager()

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login
    
    Request:
        {
            "email": "user@example.com",
            "password": "password123"
        }
    
    Response:
        {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "expires_in": 86400
        }
    """
    schema = LoginSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    # Verify credentials
    user = get_user_by_email(data['email'])
    if not user or not bcrypt.checkpw(data['password'].encode(), user['password_hash']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Generate tokens
    access_token = jwt_manager.generate_access_token(
        user_id=user['user_id'],
        email=user['email'],
        roles=user['roles']
    )
    refresh_token = jwt_manager.generate_refresh_token(user_id=user['user_id'])
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': 86400  # 24 hours
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh access token using refresh token"""
    refresh_token = request.json.get('refresh_token')
    if not refresh_token:
        return jsonify({'error': 'Refresh token required'}), 400
    
    new_access_token = jwt_manager.refresh_access_token(refresh_token)
    if not new_access_token:
        return jsonify({'error': 'Invalid or expired refresh token'}), 401
    
    return jsonify({'access_token': new_access_token}), 200
```

**Checklist:**
- [ ] Implement JWT manager
- [ ] Create auth endpoints (login, refresh)
- [ ] Write tests for JWT flows
- [ ] Update frontend to use JWT

---

#### Day 3-5: Redis Token Storage

**Setup Redis:**

```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Test connection
redis-cli ping  # Should return "PONG"
```

**Create Redis token store:**

```python
# backend/utils/auth/redis_token_store.py
import redis
import json
from typing import Optional
from cryptography.fernet import Fernet
import os

class RedisTokenStore:
    """Redis-based token storage with encryption"""
    
    def __init__(self):
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.redis = redis.from_url(redis_url, decode_responses=False)
        
        encryption_key = os.getenv('ENCRYPTION_KEY')
        self.cipher = Fernet(encryption_key.encode())
    
    def save_access_token(self, user_id: str, token: str, expires_in: int):
        """Save access token with TTL"""
        key = f"access_token:{user_id}"
        encrypted_token = self.cipher.encrypt(token.encode())
        self.redis.setex(key, expires_in, encrypted_token)
    
    def save_refresh_token(self, user_id: str, token: str, expires_in: int):
        """Save refresh token with TTL"""
        key = f"refresh_token:{user_id}"
        encrypted_token = self.cipher.encrypt(token.encode())
        self.redis.setex(key, expires_in, encrypted_token)
    
    def get_access_token(self, user_id: str) -> Optional[str]:
        """Retrieve access token"""
        key = f"access_token:{user_id}"
        encrypted_token = self.redis.get(key)
        if not encrypted_token:
            return None
        return self.cipher.decrypt(encrypted_token).decode()
    
    def revoke_tokens(self, user_id: str):
        """Revoke all tokens for user (logout)"""
        self.redis.delete(f"access_token:{user_id}")
        self.redis.delete(f"refresh_token:{user_id}")
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        key = f"blacklist:{token}"
        return self.redis.exists(key) > 0
    
    def blacklist_token(self, token: str, expires_in: int):
        """Blacklist token (for logout before expiry)"""
        key = f"blacklist:{token}"
        self.redis.setex(key, expires_in, '1')
```

**Integrate with auth flow:**

```python
# backend/api/routes/auth.py
from backend.utils.auth.redis_token_store import RedisTokenStore

token_store = RedisTokenStore()

@auth_bp.route('/login', methods=['POST'])
def login():
    # ... (authentication logic)
    
    # Save tokens to Redis
    token_store.save_access_token(user['user_id'], access_token, 86400)
    token_store.save_refresh_token(user['user_id'], refresh_token, 2592000)
    
    return jsonify({...})

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout (revoke tokens)"""
    user_id = g.user_id
    token_store.revoke_tokens(user_id)
    
    # Also blacklist current token
    token = request.headers.get('Authorization').replace('Bearer ', '')
    token_store.blacklist_token(token, 86400)
    
    return jsonify({'message': 'Logged out successfully'}), 200
```

**Checklist:**
- [ ] Install and configure Redis
- [ ] Create Redis token store
- [ ] Migrate from SQLite to Redis for tokens
- [ ] Test token storage and retrieval
- [ ] Test logout flow

---

### Week 4: Rate Limiting & RBAC

#### Day 1-3: Rate Limiting

**Install Flask-Limiter:**

```bash
pip install Flask-Limiter
```

**Configure rate limiting:**

```python
# backend/api/middleware/rate_limiter.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import g
import redis

# Redis storage for rate limiting
redis_client = redis.from_url('redis://localhost:6379/1')

def get_user_id():
    """Key function: use user_id if authenticated, else IP"""
    return g.get('user_id', get_remote_address())

limiter = Limiter(
    key_func=get_user_id,
    storage_uri="redis://localhost:6379/1",
    default_limits=["200 per day", "50 per hour"],
    headers_enabled=True,  # Add X-RateLimit-* headers
)
```

**Apply to Flask app:**

```python
# backend/api/servers/api_server.py
from backend.api.middleware.rate_limiter import limiter

# Initialize limiter
limiter.init_app(app)
```

**Apply custom limits to routes:**

```python
# backend/api/routes/orders.py
from backend.api.middleware.rate_limiter import limiter

@orders_bp.route('/', methods=['POST'])
@limiter.limit("10 per minute")  # Strict limit for order placement
@require_auth
def place_order():
    ...

@orders_bp.route('/', methods=['GET'])
@limiter.limit("100 per minute")  # More lenient for reads
@require_auth
def get_orders():
    ...
```

**Rate limit tiers by user role:**

```python
# backend/api/middleware/rate_limiter.py

def get_rate_limit():
    """Dynamic rate limits based on user role"""
    if 'admin' in g.get('roles', []):
        return "1000 per minute"
    elif 'premium' in g.get('roles', []):
        return "500 per minute"
    else:
        return "100 per minute"

@orders_bp.route('/', methods=['GET'])
@limiter.limit(get_rate_limit)
@require_auth
def get_orders():
    ...
```

**Checklist:**
- [ ] Install Flask-Limiter
- [ ] Configure Redis storage
- [ ] Apply default limits
- [ ] Add custom limits to critical endpoints
- [ ] Test rate limiting (exceed limit)
- [ ] Verify X-RateLimit headers

---

#### Day 4-5: Role-Based Access Control (RBAC)

**Database schema for users and roles:**

```sql
-- PostgreSQL schema
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    roles JSONB NOT NULL DEFAULT '["trader"]',  -- JSON array
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sample users
INSERT INTO users (email, password_hash, roles) VALUES
    ('admin@example.com', '<hashed>', '["admin", "trader"]'),
    ('trader@example.com', '<hashed>', '["trader"]'),
    ('viewer@example.com', '<hashed>', '["viewer"]');
```

**Create RBAC decorator:**

```python
# backend/utils/auth/rbac.py
from functools import wraps
from flask import g, jsonify

ROLE_PERMISSIONS = {
    'admin': ['*'],  # All permissions
    'trader': [
        'orders:read', 'orders:write', 'orders:delete',
        'positions:read',
        'portfolio:read',
        'analytics:read'
    ],
    'viewer': [
        'positions:read',
        'portfolio:read',
        'analytics:read'
    ]
}

def has_permission(user_roles: list, required_permission: str) -> bool:
    """Check if user has required permission"""
    for role in user_roles:
        permissions = ROLE_PERMISSIONS.get(role, [])
        if '*' in permissions or required_permission in permissions:
            return True
    return False

def require_permission(permission: str):
    """Require specific permission"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user_roles = g.roles
            
            if not has_permission(user_roles, permission):
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required': permission,
                    'user_roles': user_roles
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

**Apply RBAC to routes:**

```python
# backend/api/routes/orders.py
from backend.utils.auth.rbac import require_permission

@orders_bp.route('/', methods=['POST'])
@require_permission('orders:write')
def place_order():
    # Only users with 'orders:write' permission
    ...

@orders_bp.route('/<order_id>', methods=['DELETE'])
@require_permission('orders:delete')
def cancel_order(order_id):
    # Only users with 'orders:delete' permission
    ...

# backend/api/routes/admin.py
@admin_bp.route('/users')
@require_role('admin')
def get_all_users():
    # Only admins
    ...
```

**Checklist:**
- [ ] Create users table with roles
- [ ] Implement RBAC decorator
- [ ] Define role permissions
- [ ] Apply to all protected routes
- [ ] Write RBAC tests
- [ ] Test permission denials

---

## Phase 3: Performance (Weeks 5-6)

### Goal
Add Redis caching and optimize queries

### Week 5: Redis Caching Layer

#### Day 1-2: Setup Redis Caching

**Install dependencies:**

```bash
pip install flask-caching
```

**Configure Flask-Caching:**

```python
# backend/utils/caching/cache_config.py
from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/2',
    'CACHE_DEFAULT_TIMEOUT': 300,  # 5 minutes
    'CACHE_KEY_PREFIX': 'upstox:'
})

def init_cache(app):
    """Initialize cache with Flask app"""
    cache.init_app(app)
    return cache
```

**Apply caching to expensive operations:**

```python
# backend/api/routes/market_data.py
from backend.utils.caching.cache_config import cache

@market_data_bp.route('/quotes/<symbol>')
@cache.cached(timeout=5, query_string=True)  # Cache for 5 seconds
def get_quote(symbol):
    """Get market quote (cached)"""
    quote = fetch_quote_from_upstox(symbol)
    return jsonify(quote)

@market_data_bp.route('/ohlc/<symbol>')
@cache.cached(timeout=60)  # Cache for 1 minute
def get_ohlc(symbol):
    """Get OHLC data (cached)"""
    ohlc = fetch_ohlc_from_upstox(symbol)
    return jsonify(ohlc)
```

**Cache invalidation:**

```python
# backend/services/market_data/quotes.py
from backend.utils.caching.cache_config import cache

def update_quote(symbol: str, quote_data: dict):
    """Update quote and invalidate cache"""
    # Save to database
    save_quote_to_db(symbol, quote_data)
    
    # Invalidate cache
    cache.delete(f'view//api/quotes/{symbol}')
```

**Checklist:**
- [ ] Configure Flask-Caching
- [ ] Add caching to quote endpoints
- [ ] Add caching to OHLC endpoints
- [ ] Implement cache invalidation
- [ ] Test cache hit/miss
- [ ] Monitor cache hit rate

---

#### Day 3-5: Optimize Database Queries

**Fix N+1 query problem:**

```python
# BEFORE (N+1 queries)
@app.route('/api/positions')
def get_positions():
    positions = fetch_all_positions()  # 1 query
    for position in positions:
        # N queries (one per position)
        position['current_price'] = fetch_price(position['symbol'])
    return jsonify(positions)

# AFTER (2 queries)
@app.route('/api/positions')
def get_positions():
    positions = fetch_all_positions()  # 1 query
    symbols = [p['symbol'] for p in positions]
    prices = fetch_prices_batch(symbols)  # 1 batch query
    
    for position in positions:
        position['current_price'] = prices.get(position['symbol'])
    return jsonify(positions)
```

**Add database indexes:**

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);

CREATE INDEX idx_positions_user_id ON positions(user_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);

CREATE INDEX idx_ohlc_symbol_timestamp ON ohlc_data(symbol, timestamp);
CREATE INDEX idx_option_chain_symbol_expiry ON option_chain(symbol, expiry_date);
```

**Use connection pooling:**

```python
# backend/data/database/pool.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'postgresql://user:pass@localhost:5432/upstox',
    poolclass=QueuePool,
    pool_size=10,  # Max 10 connections
    max_overflow=20,  # Allow 20 overflow connections
    pool_timeout=30,  # Wait 30s for connection
    pool_recycle=3600  # Recycle connections after 1 hour
)
```

**Checklist:**
- [ ] Identify N+1 queries
- [ ] Implement batch fetching
- [ ] Add database indexes
- [ ] Configure connection pooling
- [ ] Benchmark query performance
- [ ] Monitor slow queries

---

### Week 6: Circuit Breaker & Async Database

#### Day 1-3: Implement Circuit Breaker

**Create circuit breaker:**

```python
# backend/utils/resilience/circuit_breaker.py
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failures detected, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures
    
    Usage:
        breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        
        @breaker.call
        def fetch_data():
            return api_call()
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exceptions: tuple = (Exception,)
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exceptions = expected_exceptions
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise CircuitBreakerError(
                    f"Circuit breaker is OPEN (will retry after {self.timeout}s)"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exceptions as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return False
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout)
    
    def _on_success(self):
        """Reset failure count on success"""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker reset to CLOSED")
    
    def _on_failure(self):
        """Increment failure count and open circuit if threshold reached"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker OPENED after {self.failure_count} failures"
            )
```

**Apply to Upstox API calls:**

```python
# backend/services/upstox/client.py
from backend.utils.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerError

class UpstoxClient:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60,
            expected_exceptions=(requests.RequestException,)
        )
    
    def get_portfolio(self):
        """Get portfolio with circuit breaker protection"""
        try:
            return self.circuit_breaker.call(self._get_portfolio_impl)
        except CircuitBreakerError:
            # Return cached data or error
            logger.warning("Circuit breaker open, returning cached data")
            return get_cached_portfolio()
    
    def _get_portfolio_impl(self):
        """Actual API call implementation"""
        response = requests.get(
            f"{self.base_url}/portfolio",
            headers=self._get_headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()
```

**Checklist:**
- [ ] Implement circuit breaker
- [ ] Apply to Upstox API calls
- [ ] Test circuit breaker (simulate failures)
- [ ] Monitor circuit breaker state
- [ ] Add circuit breaker metrics

---

## Phase 4-6: Testing, Documentation & Scalability

[Continue with remaining phases following same pattern]

---

## Success Metrics

### Before Refactoring

| Metric | Value |
|--------|-------|
| Code Quality | 75/100 |
| Security | 70/100 |
| Test Coverage | 15% |
| API Latency (p95) | 250ms |

### After Refactoring (Target)

| Metric | Target | Status |
|--------|--------|--------|
| Code Quality | 92/100 | In Progress |
| Security | 95/100 | In Progress |
| Test Coverage | 85% | Not Started |
| API Latency (p95) | <100ms | Not Started |

---

## Risk Management

### High-Risk Changes

1. **Database Migration (SQLite → PostgreSQL)**
   - **Mitigation:** Test on staging, backup data, have rollback plan
   
2. **Authentication Overhaul (Single user → JWT)**
   - **Mitigation:** Maintain backward compatibility for 2 weeks

### Rollback Strategy

Each phase should be independently rollback-able:

```bash
# Rollback example
git checkout <previous-commit>
systemctl restart upstox-api
```

---

**Document Maintained By:** Development Team  
**Last Updated:** February 5, 2026  
**Next Review:** Weekly during implementation
