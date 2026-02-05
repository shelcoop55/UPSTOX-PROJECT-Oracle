# 🏛️ Proposed Improved Architecture

**Document Version:** 1.0  
**Last Updated:** February 5, 2026  
**Status:** Proposal for 6-Month Roadmap

---

## 📋 Table of Contents

1. [Current vs Proposed Architecture](#current-vs-proposed-architecture)
2. [Component Breakdown](#component-breakdown)
3. [Data Flow Diagrams](#data-flow-diagrams)
4. [Technology Stack Changes](#technology-stack-changes)
5. [Migration Strategy](#migration-strategy)
6. [Scalability Considerations](#scalability-considerations)

---

## 1. Current vs Proposed Architecture

### Current Architecture (As-Is)

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                          │
│  ┌──────────────┐                    ┌──────────────┐       │
│  │   Browser    │                    │  REST Client │       │
│  │  (NiceGUI)   │                    │   (Python)   │       │
│  └──────┬───────┘                    └──────┬───────┘       │
└─────────┼────────────────────────────────────┼──────────────┘
          │                                    │
          │        HTTP/WebSocket              │
          │                                    │
┌─────────┴────────────────────────────────────┴──────────────┐
│               MONOLITHIC FLASK APPLICATION                   │
│  ┌───────────────────────────────────────────────────┐      │
│  │         api_server.py (1,755 lines)               │      │
│  │  • 52 routes in single file                       │      │
│  │  • No authentication middleware                   │      │
│  │  • No rate limiting                               │      │
│  │  • Basic error handling                           │      │
│  └────────────────────┬──────────────────────────────┘      │
└────────────────────────┼─────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
┌─────────▼──────────┐    ┌─────────────▼──────────┐
│   Services Layer    │    │     Core Layer         │
│  • Upstox Client    │    │  • Trading Logic       │
│  • Market Data      │    │  • Risk Manager        │
│  • WebSocket        │    │  • Analytics           │
│  • AI Services      │    │  • Paper Trading       │
└─────────┬───────────┘    └─────────────┬──────────┘
          │                              │
          └──────────────┬───────────────┘
                         │
               ┌─────────▼────────┐
               │  SQLite Database │
               │  • 78+ tables    │
               │  • No replication│
               │  • Single file   │
               └──────────────────┘

ISSUES:
❌ Single monolithic Flask file (hard to maintain)
❌ No API gateway (rate limiting, auth)
❌ SQLite (not scalable for production)
❌ No caching layer (Redis)
❌ No message queue (background jobs)
❌ No service discovery
❌ No horizontal scaling support
```

---

### Proposed Architecture (To-Be)

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Browser    │  │    Mobile    │  │  Desktop App │      │
│  │  (NiceGUI)   │  │ (React Native│  │   (Electron) │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          │              HTTPS (TLS 1.3)        │
          │                  │                  │
┌─────────┴──────────────────┴──────────────────┴─────────────┐
│                     API GATEWAY (NEW)                        │
│  ┌────────────────────────────────────────────────┐         │
│  │  NGINX / Kong / AWS API Gateway                │         │
│  │  ┌──────────────────────────────────────────┐ │         │
│  │  │  • Rate Limiting (sliding window)        │ │         │
│  │  │  • JWT Authentication & Authorization    │ │         │
│  │  │  • Request Validation (JSON Schema)      │ │         │
│  │  │  • Circuit Breaker (Hystrix-style)       │ │         │
│  │  │  • Load Balancing (round-robin/least-conn│ │         │
│  │  │  • API Versioning (/v1, /v2)             │ │         │
│  │  │  • CORS Management                       │ │         │
│  │  │  • DDoS Protection (rate limiting)       │ │         │
│  │  │  • SSL/TLS Termination                   │ │         │
│  │  │  • Request/Response Logging              │ │         │
│  │  └──────────────────────────────────────────┘ │         │
│  └─────────────────┬──────────────────────────────┘         │
└────────────────────┼────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐       ┌────────▼────────┐
│  Web Service   │       │ WebSocket Service│
│  (Flask REST)  │       │  (Real-time)     │
│  Port 8000     │       │  Port 8001       │
│  ┌──────────┐  │       │  ┌────────────┐ │
│  │Blueprints│  │       │  │Market Feed │ │
│  │ Portfolio│  │       │  │Order Update│ │
│  │ Orders   │  │       │  │Alert Notif │ │
│  │ Analytics│  │       │  └────────────┘ │
│  │ Backtest │  │       └─────────────────┘
│  │ Admin    │  │
│  └──────────┘  │
└───────┬────────┘
        │
        │   RPC (gRPC) / REST
        │
┌───────┴─────────────────────────────────────────────────────┐
│              APPLICATION SERVICES LAYER                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Trading     │  │  Analytics   │  │   Risk Mgmt  │     │
│  │  Service     │  │  Service     │  │   Service    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                  │              │
│  ┌──────┴────────┐  ┌─────┴────────┐  ┌────┴────────┐     │
│  │  Market Data  │  │  Paper Trade │  │  Backtest   │     │
│  │  Service      │  │  Service     │  │  Service    │     │
│  └───────────────┘  └──────────────┘  └─────────────┘     │
└────────────┬────────────────────────────────────────────────┘
             │
             │   Message Queue (RabbitMQ / Kafka)
             │
┌────────────┴─────────────────────────────────────────────────┐
│                   DATA & CACHE LAYER                          │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   PostgreSQL     │  │    Redis     │  │   Elasticsearch│ │
│  │   (Primary DB)   │  │   (Cache)    │  │   (Search)    │  │
│  │                  │  │              │  │               │  │
│  │  • ACID          │  │  • Sessions  │  │  • Logs       │  │
│  │  • Replication   │  │  • Tokens    │  │  • Metrics    │  │
│  │  • Sharding      │  │  • Rate Lmt  │  │  • Full-text  │  │
│  │  • Backups       │  │  • Pub/Sub   │  │               │  │
│  └─────────┬────────┘  └──────┬───────┘  └───────┬───────┘  │
└────────────┼────────────────────┼──────────────────┼──────────┘
             │                   │                  │
┌────────────┴───────────────────┴──────────────────┴──────────┐
│                  MONITORING & OBSERVABILITY                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Prometheus  │  │   Grafana    │  │    Jaeger    │       │
│  │  (Metrics)   │  │ (Dashboards) │  │  (Tracing)   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└───────────────────────────────────────────────────────────────┘

BENEFITS:
✅ Modular services (easy to scale independently)
✅ API Gateway (security, rate limiting, versioning)
✅ PostgreSQL (production-grade, ACID, replication)
✅ Redis (fast caching, session management)
✅ Message Queue (async processing, decoupling)
✅ Horizontal scaling (load balancer)
✅ Monitoring (Prometheus, Grafana, Jaeger)
✅ High availability (replication, failover)
```

---

## 2. Component Breakdown

### 2.1 API Gateway

**Responsibilities:**
- Request authentication & authorization
- Rate limiting (per user, per IP, per endpoint)
- Input validation (JSON schema)
- Circuit breaker (prevent cascading failures)
- Load balancing
- SSL/TLS termination
- API versioning
- Request/response logging

**Technology Options:**

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **NGINX** | Fast, lightweight, proven | Manual config | ✅ **Best for small-medium** |
| **Kong** | Feature-rich, plugin system | Heavier | Good for complex needs |
| **AWS API Gateway** | Managed, scalable | Vendor lock-in | Good for AWS deployments |
| **Traefik** | Docker-native, auto-discovery | Learning curve | Good for containers |

**Implementation:**

```nginx
# /etc/nginx/sites-available/upstox-api

# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $http_authorization zone=user_limit:10m rate=100r/m;

upstream backend_servers {
    least_conn;  # Load balancing algorithm
    server 127.0.0.1:8000 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 weight=1 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name api.upstox-trading.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/upstox-trading.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/upstox-trading.com/privkey.pem;
    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # Rate Limiting
    location /api/orders {
        limit_req zone=api_limit burst=5 nodelay;
        limit_req zone=user_limit burst=10;
        proxy_pass http://backend_servers;
    }

    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        
        # Authentication check (via auth service)
        auth_request /auth/validate;
        
        proxy_pass http://backend_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Trace-ID $request_id;
    }

    location = /auth/validate {
        internal;
        proxy_pass http://127.0.0.1:9000/auth/validate;
        proxy_set_header Authorization $http_authorization;
    }
}
```

---

### 2.2 Service Layer

#### Trading Service

**Responsibilities:**
- Order placement, modification, cancellation
- Position management
- Stop-loss/take-profit execution
- GTT (Good Till Triggered) orders

**API Endpoints:**
```
POST   /api/v1/orders              # Place order
GET    /api/v1/orders              # List orders
PUT    /api/v1/orders/{id}         # Modify order
DELETE /api/v1/orders/{id}         # Cancel order
GET    /api/v1/positions           # List positions
POST   /api/v1/positions/{id}/close # Close position
```

**Database Tables:**
- `orders` (id, user_id, symbol, quantity, price, status, created_at)
- `positions` (id, user_id, symbol, quantity, avg_price, current_price, pnl)
- `trade_history` (id, order_id, executed_price, executed_qty, timestamp)

---

#### Analytics Service

**Responsibilities:**
- Performance metrics (Sharpe, Sortino, win rate)
- Equity curve generation
- P&L analysis
- Risk metrics (VAR, max drawdown)

**API Endpoints:**
```
GET /api/v1/analytics/performance      # 30-day performance
GET /api/v1/analytics/equity-curve     # Historical equity
GET /api/v1/analytics/risk-metrics     # VAR, Sharpe, drawdown
GET /api/v1/analytics/pnl-breakdown    # By symbol, strategy
```

**Database Tables:**
- `performance_metrics` (date, win_rate, sharpe, sortino, total_pnl)
- `daily_snapshots` (date, equity, drawdown, num_trades)

---

#### Risk Management Service

**Responsibilities:**
- Position sizing
- Stop-loss management
- Circuit breaker
- Daily loss limits

**API Endpoints:**
```
GET  /api/v1/risk/limits           # User risk limits
POST /api/v1/risk/validate-order   # Pre-trade risk check
GET  /api/v1/risk/circuit-breaker  # Circuit breaker status
```

**Database Tables:**
- `risk_limits` (user_id, max_position_size, max_daily_loss)
- `circuit_breaker_state` (user_id, is_open, failure_count, last_failure)

---

### 2.3 Data Layer

#### PostgreSQL (Primary Database)

**Why PostgreSQL over SQLite?**

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| **Concurrency** | Limited (write locks) | Excellent (MVCC) |
| **Max DB Size** | 281 TB (theoretical) | Unlimited |
| **Replication** | None | Native (streaming) |
| **Transactions** | Limited isolation levels | Full ACID |
| **Users** | Single file | Multi-user with RBAC |
| **Performance** | Fast for < 100K rows | Scales to billions |
| **Backup** | File copy | pg_dump, PITR |
| **Extensions** | None | 100+ (PostGIS, pgvector) |

**Schema Migration:**

```sql
-- PostgreSQL version of key tables

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    roles JSONB NOT NULL DEFAULT '["trader"]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    INDEX idx_users_email ON users(email)
);

CREATE TABLE auth_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_tokens_user_id ON auth_tokens(user_id),
    INDEX idx_tokens_expires_at ON auth_tokens(expires_at)
);

CREATE TABLE orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    price NUMERIC(10, 2),
    order_type VARCHAR(20) NOT NULL,
    product_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_orders_user_id ON orders(user_id),
    INDEX idx_orders_symbol ON orders(symbol),
    INDEX idx_orders_status ON orders(status)
);

-- Partitioning for large tables
CREATE TABLE ohlc_data (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    open NUMERIC(10, 2) NOT NULL,
    high NUMERIC(10, 2) NOT NULL,
    low NUMERIC(10, 2) NOT NULL,
    close NUMERIC(10, 2) NOT NULL,
    volume BIGINT NOT NULL,
    PRIMARY KEY (timestamp, symbol)
) PARTITION BY RANGE (timestamp);

-- Create partitions for each month
CREATE TABLE ohlc_data_2026_02 PARTITION OF ohlc_data
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
```

**Migration Script:**

```python
# backend/data/database/migrate_sqlite_to_postgres.py

import sqlite3
import psycopg2
from tqdm import tqdm

def migrate_table(sqlite_conn, pg_conn, table_name, batch_size=1000):
    """Migrate single table from SQLite to PostgreSQL"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Get column names
    sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in sqlite_cursor.fetchall()]
    
    # Count total rows
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_rows = sqlite_cursor.fetchone()[0]
    
    # Migrate in batches
    for offset in tqdm(range(0, total_rows, batch_size), desc=f"Migrating {table_name}"):
        sqlite_cursor.execute(f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}")
        rows = sqlite_cursor.fetchall()
        
        # Insert into PostgreSQL
        placeholders = ','.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
        pg_cursor.executemany(insert_query, rows)
        pg_conn.commit()
    
    print(f"✅ Migrated {total_rows:,} rows from {table_name}")

# Usage
sqlite_conn = sqlite3.connect('market_data.db')
pg_conn = psycopg2.connect(
    host='localhost',
    database='upstox_trading',
    user='upstox_user',
    password='secure_password'
)

tables = ['users', 'auth_tokens', 'orders', 'positions', 'ohlc_data']
for table in tables:
    migrate_table(sqlite_conn, pg_conn, table)
```

---

#### Redis (Cache & Session Store)

**Use Cases:**

1. **Session Management**
   ```python
   # Store user session
   redis_client.setex(f"session:{session_id}", 3600, json.dumps(session_data))
   
   # Retrieve session
   session_data = json.loads(redis_client.get(f"session:{session_id}"))
   ```

2. **Token Storage**
   ```python
   # Store access token with auto-expiry
   redis_client.setex(f"token:{user_id}", 3600, encrypted_token)
   ```

3. **Rate Limiting**
   ```python
   # Sliding window rate limiter
   key = f"rate_limit:{user_id}:{endpoint}"
   current = redis_client.incr(key)
   if current == 1:
       redis_client.expire(key, 60)  # 60 second window
   
   if current > 100:  # 100 requests per minute
       raise RateLimitExceeded()
   ```

4. **Market Data Caching**
   ```python
   # Cache market quote
   redis_client.setex(f"quote:{symbol}", 5, json.dumps(quote_data))
   ```

5. **Pub/Sub for Real-time Updates**
   ```python
   # Publisher (price update)
   redis_client.publish('price_updates', json.dumps({
       'symbol': 'RELIANCE',
       'price': 2500.50
   }))
   
   # Subscriber (WebSocket server)
   pubsub = redis_client.pubsub()
   pubsub.subscribe('price_updates')
   for message in pubsub.listen():
       websocket.send(message['data'])
   ```

---

## 3. Data Flow Diagrams

### 3.1 Order Placement Flow

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ 1. POST /api/v1/orders
     │    {"symbol": "RELIANCE", "quantity": 10}
     ▼
┌────────────────┐
│  API Gateway   │ 2. Authenticate (JWT)
│                │ 3. Rate limit check (Redis)
│                │ 4. Input validation
└───────┬────────┘
        │ 5. Forward to Trading Service
        ▼
┌────────────────┐
│ Trading Service│ 6. Pre-trade risk check
│                │    (Risk Service via RPC)
└───────┬────────┘
        │ 7. Risk approved
        ▼
┌────────────────┐
│  Risk Service  │ 8. Check position limits
│                │ 9. Check daily loss limit
│                │ 10. Check circuit breaker
└───────┬────────┘
        │ 11. ✅ Risk OK
        ▼
┌────────────────┐
│ Trading Service│ 12. Place order with Upstox
│                │ 13. Save to DB (PostgreSQL)
│                │ 14. Publish event (RabbitMQ)
└───────┬────────┘
        │ 15. Order response
        ▼
┌────────────────┐
│  API Gateway   │ 16. Return response
└───────┬────────┘
        │ 17. HTTP 201 Created
        ▼
┌──────────┐
│  Client  │ ✅ Order placed successfully
└──────────┘

        │
        │ (Async processing)
        ▼
┌────────────────┐
│  RabbitMQ      │ 18. Order event consumed
└───────┬────────┘
        │
        ├─────────────────┐
        ▼                 ▼
┌────────────────┐  ┌────────────────┐
│ Analytics Svc  │  │  Notification  │
│ (Update P&L)   │  │     Service    │
└────────────────┘  └────────────────┘
```

---

### 3.2 Authentication Flow (JWT)

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ 1. POST /auth/login
     │    {"email": "user@example.com", "password": "***"}
     ▼
┌────────────────┐
│  API Gateway   │ 2. Forward to Auth Service
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Auth Service  │ 3. Verify credentials (PostgreSQL)
│                │ 4. Generate JWT with claims:
│                │    - user_id
│                │    - roles (["trader", "admin"])
│                │    - exp (24h from now)
└───────┬────────┘
        │ 5. Store session in Redis
        │    Key: session:{session_id}
        │    TTL: 24 hours
        ▼
┌────────────────┐
│     Redis      │ 6. Session stored
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Auth Service  │ 7. Return JWT + refresh token
└───────┬────────┘
        │ 8. HTTP 200 OK
        │    {"access_token": "eyJ...", "refresh_token": "..."}
        ▼
┌──────────┐
│  Client  │ ✅ Authenticated
└────┬─────┘
     │
     │ 9. Subsequent requests
     │    Header: Authorization: Bearer eyJ...
     ▼
┌────────────────┐
│  API Gateway   │ 10. Validate JWT
│                │ 11. Check Redis session
│                │ 12. Inject user context (g.user_id)
└───────┬────────┘
        │ 13. Forward to service
        ▼
┌────────────────┐
│   Any Service  │ 14. Access g.user_id
└────────────────┘
```

---

### 3.3 Real-time Market Data Flow

```
┌────────────────┐
│  Upstox API    │ 1. WebSocket connection
│  (Market Feed) │    (RELIANCE, TCS, INFY)
└───────┬────────┘
        │ 2. Price updates (streaming)
        ▼
┌────────────────┐
│  Market Data   │ 3. Parse & validate
│    Service     │ 4. Update Redis cache
└───────┬────────┘
        │ 5. Publish to Redis Pub/Sub
        │    Channel: price_updates
        ▼
┌────────────────┐
│     Redis      │ 6. Pub/Sub broadcast
│   Pub/Sub      │    to all subscribers
└───────┬────────┘
        │
        ├─────────────────┬─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌────────────────┐  ┌────────────┐  ┌────────────┐
│  WebSocket Svc │  │Alert Engine│  │ Risk Engine│
│  (Port 8001)   │  │            │  │            │
└───────┬────────┘  └────┬───────┘  └────┬───────┘
        │                │                │
        │ 7. Push to    │ 8. Check       │ 9. Check
        │    connected  │    alert       │    stop-loss
        │    clients    │    rules       │    triggers
        ▼                ▼                ▼
┌──────────┐      ┌────────────┐  ┌────────────┐
│  Client  │      │Send email/ │  │Execute SL  │
│ (Browser)│      │Telegram    │  │ order      │
└──────────┘      └────────────┘  └────────────┘
```

---

## 4. Technology Stack Changes

### Current Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Backend | Flask | 3.0.0 |
| Database | SQLite | 3.x |
| Cache | None | - |
| Queue | None | - |
| WebSocket | Flask-SocketIO | 5.3.6 |
| Frontend | NiceGUI | 1.4.0 |

---

### Proposed Stack

| Component | Technology | Version | Reason |
|-----------|------------|---------|--------|
| API Gateway | NGINX | 1.25+ | High performance, proven |
| Backend | Flask | 3.0.0 | ✅ Keep (mature ecosystem) |
| Database | PostgreSQL | 15+ | Production-grade, scalable |
| Cache | Redis | 7.0+ | Fast, versatile |
| Queue | RabbitMQ | 3.12+ | Reliable message broker |
| Search | Elasticsearch | 8.0+ | Log aggregation, full-text |
| Metrics | Prometheus | 2.45+ | Time-series metrics |
| Dashboards | Grafana | 10.0+ | Visualization |
| Tracing | Jaeger | 1.47+ | Distributed tracing |
| WebSocket | Flask-SocketIO | 5.3.6 | ✅ Keep (works well) |
| Frontend | NiceGUI | 1.4.0 | ✅ Keep (rapid development) |

---

### New Dependencies

```txt
# requirements.txt (ADD)

# PostgreSQL
psycopg2-binary>=2.9.9
SQLAlchemy>=2.0.23

# Redis
redis>=5.0.0
flask-caching>=2.1.0

# Message Queue
pika>=1.3.2  # RabbitMQ client
celery>=5.3.0  # Task queue

# Monitoring
prometheus-client>=0.19.0

# API Gateway (if using Kong)
# kong-python>=0.1.0

# Distributed Tracing
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-instrumentation-flask>=0.41b0
```

---

## 5. Migration Strategy

### Phase 1: Foundation (Weeks 1-2)
**Goal:** Refactor monolithic Flask app

**Tasks:**
- [x] Split `api_server.py` into blueprints
- [x] Add input validation (Marshmallow)
- [x] Add authentication decorators
- [x] Add security headers

**Risk:** Medium (regression testing required)

---

### Phase 2: Database Migration (Weeks 3-4)
**Goal:** Migrate from SQLite to PostgreSQL

**Tasks:**
- [ ] Setup PostgreSQL server
- [ ] Create schema in PostgreSQL
- [ ] Write migration script
- [ ] Test data integrity
- [ ] Switch connection strings
- [ ] Deprecate SQLite

**Risk:** High (data loss potential)

**Mitigation:**
- Backup SQLite database
- Test migration on staging environment
- Run migration during maintenance window
- Keep SQLite as fallback for 1 week

---

### Phase 3: Caching Layer (Weeks 5-6)
**Goal:** Add Redis for caching and sessions

**Tasks:**
- [ ] Setup Redis server
- [ ] Migrate tokens to Redis
- [ ] Add market data caching
- [ ] Implement rate limiting
- [ ] Add session management

**Risk:** Low

---

### Phase 4: API Gateway (Weeks 7-8)
**Goal:** Add NGINX as API gateway

**Tasks:**
- [ ] Install NGINX
- [ ] Configure rate limiting
- [ ] Setup load balancing
- [ ] Add SSL/TLS
- [ ] Configure circuit breaker

**Risk:** Medium (networking complexity)

---

### Phase 5: Message Queue (Weeks 9-10)
**Goal:** Add RabbitMQ for async processing

**Tasks:**
- [ ] Setup RabbitMQ server
- [ ] Create worker processes
- [ ] Migrate background jobs to Celery
- [ ] Implement order event publishing
- [ ] Add retry mechanisms

**Risk:** Medium

---

### Phase 6: Monitoring (Weeks 11-12)
**Goal:** Add comprehensive monitoring

**Tasks:**
- [ ] Setup Prometheus
- [ ] Add metrics collection
- [ ] Create Grafana dashboards
- [ ] Setup Jaeger tracing
- [ ] Configure alerting

**Risk:** Low

---

## 6. Scalability Considerations

### Horizontal Scaling

**Current:** Single Flask process

**Proposed:** Multiple Flask workers behind load balancer

```bash
# /etc/systemd/system/upstox-api@.service (systemd template)
[Unit]
Description=UPSTOX Trading API - Instance %i
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=upstox
WorkingDirectory=/opt/upstox-trading
ExecStart=/opt/upstox-trading/.venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:%i \
    --timeout 60 \
    backend.api.servers.api_server:app

Restart=always

[Install]
WantedBy=multi-user.target
```

**Start multiple instances:**
```bash
systemctl start upstox-api@8000.service
systemctl start upstox-api@8001.service
systemctl start upstox-api@8002.service
```

**NGINX load balancing:**
```nginx
upstream backend_servers {
    least_conn;
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}
```

---

### Database Scaling

#### Read Replicas

```
┌────────────┐
│  Primary   │ ← All writes
│  (Master)  │
└─────┬──────┘
      │ Replication (streaming)
      ├──────────────┬──────────────┐
      ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌────────────┐
│  Replica 1 │ │  Replica 2 │ │  Replica 3 │
│  (Slave)   │ │  (Slave)   │ │  (Slave)   │
└────────────┘ └────────────┘ └────────────┘
      ▲              ▲              ▲
      └──────────────┴──────────────┘
            All reads (load balanced)
```

**Configuration:**
```python
# backend/data/database/connection_pool.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Write connection (master)
write_engine = create_engine('postgresql://user:pass@master:5432/upstox')

# Read connections (replicas)
read_engines = [
    create_engine('postgresql://user:pass@replica1:5432/upstox'),
    create_engine('postgresql://user:pass@replica2:5432/upstox'),
    create_engine('postgresql://user:pass@replica3:5432/upstox'),
]

def get_read_engine():
    """Round-robin read replica selection"""
    import random
    return random.choice(read_engines)

# Usage
@app.route('/api/positions')
def get_positions():
    engine = get_read_engine()  # Read from replica
    # ... query logic
```

---

### Cache Scaling

#### Redis Cluster

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Redis Master │  │ Redis Master │  │ Redis Master │
│   Node 1     │  │   Node 2     │  │   Node 3     │
│  (Shard A)   │  │  (Shard B)   │  │  (Shard C)   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│Redis Replica │  │Redis Replica │  │Redis Replica │
│   (Shard A)  │  │   (Shard B)  │  │   (Shard C)  │
└──────────────┘  └──────────────┘  └──────────────┘
```

**Configuration:**
```python
from redis.cluster import RedisCluster

redis_cluster = RedisCluster(
    startup_nodes=[
        {"host": "127.0.0.1", "port": "7000"},
        {"host": "127.0.0.1", "port": "7001"},
        {"host": "127.0.0.1", "port": "7002"},
    ],
    decode_responses=True
)
```

---

## 7. Cost Estimation

### Current Infrastructure (Single Server)

| Component | Specs | Cost/Month |
|-----------|-------|------------|
| VM (Oracle Cloud) | 4 vCPU, 24GB RAM | $0 (free tier) |
| Storage | 200GB | $0 (included) |
| Bandwidth | 10TB | $0 (included) |
| **Total** | | **$0/month** |

---

### Proposed Infrastructure (Production)

| Component | Specs | Quantity | Cost/Month |
|-----------|-------|----------|------------|
| Load Balancer | 1GB RAM | 1 | $10 |
| API Servers | 2 vCPU, 4GB RAM | 3 | $30 × 3 = $90 |
| PostgreSQL (Primary) | 4 vCPU, 8GB RAM | 1 | $40 |
| PostgreSQL (Replica) | 4 vCPU, 8GB RAM | 2 | $40 × 2 = $80 |
| Redis Cluster | 2GB RAM | 3 | $15 × 3 = $45 |
| RabbitMQ | 2 vCPU, 4GB RAM | 1 | $30 |
| Elasticsearch | 4 vCPU, 8GB RAM | 1 | $50 |
| Monitoring (Prometheus) | 2 vCPU, 4GB RAM | 1 | $30 |
| Storage (SSD) | 500GB | - | $50 |
| Backups | 1TB | - | $25 |
| Bandwidth | 20TB | - | $40 |
| **Total** | | | **$490/month** |

**Cheaper Alternative (AWS/Oracle Cloud):**
- Use managed services (RDS, ElastiCache, MQ)
- Estimated: $250-300/month with free tier credits

---

## 8. Summary

### Benefits of Proposed Architecture

| Metric | Current | Proposed | Improvement |
|--------|---------|----------|-------------|
| **Scalability** | Single server | Horizontal | 10x |
| **Availability** | 95% (single point) | 99.9% (HA) | +5% uptime |
| **Performance** | 250ms p95 | 100ms p95 | -60% latency |
| **Concurrent Users** | 10-50 | 1,000+ | 20x |
| **API Throughput** | 100 req/s | 10,000 req/s | 100x |
| **Database Writes** | 100/s (lock wait) | 10,000/s | 100x |
| **Monitoring** | Basic logs | Full observability | +++ |

---

### Migration Timeline

**Total Duration:** 12-16 weeks

- **Weeks 1-2:** Blueprint refactoring
- **Weeks 3-4:** PostgreSQL migration
- **Weeks 5-6:** Redis caching
- **Weeks 7-8:** API Gateway
- **Weeks 9-10:** Message Queue
- **Weeks 11-12:** Monitoring
- **Weeks 13-14:** Load testing
- **Weeks 15-16:** Production rollout

---

### Next Steps

1. **Get stakeholder approval** for architecture changes
2. **Setup staging environment** to test migrations
3. **Start with Phase 1** (blueprint refactoring - low risk)
4. **Incremental rollout** - each phase tested before next
5. **Monitor metrics** - track improvements at each stage

---

**Document Prepared By:** Senior Software Architect  
**Date:** February 5, 2026  
**Status:** Proposal (awaiting approval)
