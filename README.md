# Inventory Management API

A production-oriented inventory management REST API built with **FastAPI, PostgreSQL, Redis, Docker, AWS, and GitHub Actions**.

**Languages:** [English](#english) | [日本語](#日本語)

---

<a name="english"></a>

# 🇬🇧 English

## Live Demo

Interactive API documentation (Swagger UI):

**http://3.27.38.78:8000/docs**

The demo runs on a single AWS free-tier EC2 instance, so it may occasionally be offline. It is served over plain HTTP, so **do not use a real password**: register a throwaway account to try it.

<!-- Add screenshots here once they exist:
![Swagger UI overview](docs/images/swagger-overview.png)
-->

---

## Overview

**Inventory Management API** is a backend application for managing users, categories, products, inventory quantities, and orders through a RESTful API.

The project was built to demonstrate backend engineering beyond basic CRUD operations, with particular focus on:

* Secure authentication and authorization (role-level and object-level)
* Transactional order processing, including cancellation
* PostgreSQL concurrency control with row-level locking
* Database constraints and query-oriented indexes
* Redis caching with graceful failure handling
* Pagination, filtering, and sorting
* Login rate limiting and fail-fast configuration
* Automated testing, including real concurrency tests
* Containerized development, CI/CD, and cloud deployment

---

## Key Features

### Authentication & Authorization

* JWT-based authentication
* Argon2 password hashing
* Role-based access control (RBAC) with `user` and `admin` roles
* Object-level authorization: users can only change their own products and see their own orders
* Admin-only operations (user list, product deletion, category management)
* Protection against cross-user access (IDOR)
* Login rate limiting per client IP (Redis)
* The application refuses to start with a weak or placeholder JWT secret

### Product & Inventory Management

* Product CRUD and category management
* Product ownership
* Stock addition and removal, serialized with row locks
* PostgreSQL `CHECK` constraint preventing negative inventory
* Pagination, category and price filtering, sorting
* Deleting a product that appears in an order is rejected with `409 Conflict`

### Orders

* Order and OrderItem models with server-side price calculation
* Transactional order creation with automatic inventory deduction
* Order cancellation that returns stock to inventory (pending orders only)
* Order ownership protection and pagination
* Atomic rollback on failure
* `SELECT ... FOR UPDATE` row locking in a consistent order, so concurrent orders can neither oversell stock nor deadlock

### Database

* PostgreSQL 16, SQLAlchemy 2, Alembic migrations
* Decimal monetary values
* Foreign keys, unique constraints, and database-level inventory constraints
* Query-oriented indexes

### Caching

* Redis product caching with TTL
* Cache invalidation after product mutations, stock changes, and order changes
* Graceful fallback to PostgreSQL when Redis is unavailable
* Invalid cache data is treated as a cache miss
* PostgreSQL remains the source of truth

### Testing

* pytest with API, service, repository, schema, security, and cache tests
* Redis failure tests and transaction rollback tests
* PostgreSQL concurrency tests (overselling, double cancellation, opposite lock order, concurrent stock updates)
* **140+ automated tests**

### Infrastructure

* Docker and Docker Compose, running as an unprivileged user
* GitHub Actions CI/CD
* AWS ECR, EC2, and Systems Manager
* Application health checks
* Environment-based configuration, including CORS

---

## Technical Highlights

The main goal of this project was not simply to connect FastAPI to PostgreSQL. Several features address realistic backend problems.

### 1. Transactional Order Creation and Cancellation

Creating an order changes several pieces of data in one database transaction:

```text
Lock products (ascending id)
        │
        ▼
Check stock
        │
        ▼
Decrease stock
        │
        ▼
Create Order + OrderItems
        │
        ▼
Commit
```

If anything fails, the transaction is rolled back, so inventory can never drop without a matching order.

Cancelling a pending order locks the order row, then the affected products (again in ascending id order), returns the stock, and marks the order `cancelled`. Because the order row is locked, two simultaneous cancel requests cannot both restore the stock: the second one waits, sees the `cancelled` status, and is rejected.

---

### 2. Concurrency Control

Inventory becomes wrong when several requests change the same product at the same time. Every code path that changes a product's quantity (order creation, order cancellation, stock add/remove, product update) locks the product row first:

```sql
SELECT ...
FROM products
WHERE id = ...
FOR UPDATE;
```

```text
Request A                    Request B
    │                            │
    ▼                            ▼
Lock product                 Wait for lock
    │                            │
    ▼                            │
Check stock                      │
    │                            │
    ▼                            │
Decrease stock                   │
    │                            │
    ▼                            │
Commit                           │
                                 ▼
                            Read current stock
                                 │
                                 ▼
                           Check stock again
                                 │
                                 ▼
                         Reject if insufficient
```

Orders lock products in ascending id order, so two orders that list the same products in opposite order cannot deadlock. Rows are re-read after locking (`populate_existing`), so a stale copy in the SQLAlchemy session is never used for the stock check.

The test suite proves this with real PostgreSQL transactions and a barrier that releases all workers at once:

* ten buyers competing for three units produce exactly three orders
* two orders listing the same products in opposite order never deadlock
* ten concurrent stock removals never push quantity below zero
* ten concurrent stock additions never lose an update
* two simultaneous cancellations restore stock only once

---

### 3. Database-Level Integrity

Application validation is not the only line of defense. The `products` table also enforces

```text
quantity >= 0
```

at the PostgreSQL level, which protects the data even if an application-level check is bypassed.

---

### 4. Query-Oriented Indexes

Indexes were added for actual query patterns instead of indexing every column:

```text
products(category_id)
orders(user_id, created_at, id)
order_items(order_id)
```

The order index supports the user's paginated order query:

```sql
WHERE user_id = ?
ORDER BY created_at DESC, id DESC
```

---

### 5. Redis as an Optimization, Not the Source of Truth

```text
GET product
     │
     ▼
Redis
 ┌───┴────┐
Hit      Miss
 │         │
 ▼         ▼
Return   PostgreSQL
           │
           ▼
        Cache result (TTL 60 s)
```

Redis failures never make the API unavailable. A failed read is treated as a cache miss, and failed writes or invalidations are non-fatal. After a change, the database transaction is committed first and the cache entry is invalidated afterwards. A read that races with a write can briefly repopulate an old value, but the 60-second TTL bounds that window.

---

### 6. Object-Level Authorization

Being logged in is not enough: a user must not be able to change another user's product or read another user's order just by changing an ID.

```text
Authenticated user
       │
       ▼
Is owner?
   ┌───┴───┐
  Yes      No
   │        │
   ▼        ▼
Allow    Is admin?
             │
          ┌──┴──┐
         Yes    No
          │      │
          ▼      ▼
        Allow   403
```

Users can read only their own profile (admins can read any), and the user list is admin-only. Orders are always looked up by both order id and the authenticated user's id.

---

### 7. Meaningful Error Responses

Expected business errors are separate exception types, translated to HTTP status codes at the API boundary:

| Situation | Status |
| --- | --- |
| Invalid request, duplicate product in one order | `400 Bad Request` |
| Missing or invalid credentials | `401 Unauthorized` |
| Not allowed to modify this resource | `403 Forbidden` |
| Order, product, or user not found | `404 Not Found` |
| Insufficient stock, order not cancellable, product still referenced by orders | `409 Conflict` |
| Too many login attempts | `429 Too Many Requests` |
| Database unavailable (health check) | `503 Service Unavailable` |

Unexpected exceptions are logged on the server and never returned to the client.

---

### 8. Login Rate Limiting and Fail-Fast Configuration

* Login requests are limited per client IP with a Redis fixed-window counter (10 requests per 5 minutes by default). The counter and its expiry are set in a single Redis transaction, so a crash cannot leave an IP locked out forever. If Redis is down, the limiter fails open and logs a warning.
* The application refuses to start if `JWT_SECRET_KEY` is shorter than 32 characters or looks like a placeholder, so a weak secret cannot reach production by accident.

---

## Architecture

```text
                    Client
                      │
                      ▼
                FastAPI API
                      │
                      ▼
              API / Dependencies
                      │
                      ▼
                  Services
                      │
                      ▼
                Repositories
                  │       │
                  ▼       ▼
             PostgreSQL  Redis
```

| Layer | Responsibility |
| --- | --- |
| API | HTTP requests and responses, validation, status codes, dependency injection, authentication boundary |
| Service | Business rules, transactions, authorization checks, inventory and order processing, cache coordination |
| Repository | Database queries and persistence, including row-locking queries |
| Model | SQLAlchemy models and relationships |
| Schema | Pydantic request and response models |
| Core | Configuration, security, roles, domain exceptions, rate limiting |
| Cache | Redis caching and invalidation |
| Tasks | Lightweight in-process background work (FastAPI `BackgroundTasks`), currently a log entry when a product is created. Not a durable job queue |

---

## API Overview

| Method | Path | Access |
| --- | --- | --- |
| POST | `/users` | Public (registration) |
| POST | `/users/login` | Public, rate limited |
| GET | `/users` | Admin |
| GET | `/users/{user_id}` | The user themselves, or an admin |
| GET | `/categories`, `/categories/{id}` | Public |
| POST, DELETE | `/categories`, `/categories/{id}` | Admin |
| GET | `/products`, `/products/{id}` | Public |
| POST | `/products` | Authenticated |
| PATCH | `/products/{id}` | Owner or admin |
| POST | `/products/{id}/stock/add`, `/stock/remove` | Owner or admin |
| DELETE | `/products/{id}` | Admin (409 if referenced by orders) |
| POST | `/orders` | Authenticated |
| GET | `/orders`, `/orders/{id}` | Own orders only |
| POST | `/orders/{id}/cancel` | Own pending orders only |
| GET | `/health` | Public |

Product listing supports category filtering, minimum and maximum price, sorting, and pagination. Paginated responses look like this:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "pages": 0
}
```

---

## Project Structure

```text
inventory-management/
├── app/
│   ├── api/
│   │   ├── category.py
│   │   ├── dependencies.py
│   │   ├── orders.py
│   │   ├── products.py
│   │   └── users.py
│   │
│   ├── cache/
│   │   └── product.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── rate_limit.py
│   │   ├── roles.py
│   │   └── security.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── redis.py
│   │
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── tasks/
│   └── main.py
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── api/
│   ├── cache/
│   ├── service/
│   ├── test_auth.py
│   ├── test_health.py
│   ├── test_order_cancel.py
│   ├── test_order_concurrency.py
│   ├── test_rate_limit.py
│   ├── test_stock_concurrency.py
│   └── ...
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── Dockerfile
├── compose.yml
├── alembic.ini
├── env.example
├── pyproject.toml
└── uv.lock
```

Production-only configuration and secrets are intentionally excluded from the repository.

---

## Configuration

Create a `.env` file from `env.example`:

| Variable | Description | Default |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection URL | required |
| `JWT_SECRET_KEY` | Token signing secret, at least 32 characters | required |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REDIS_URL` | Redis connection URL | required |
| `CORS_ORIGINS` | Comma-separated browser origins allowed to call the API | `http://localhost:3000` |
| `LOGIN_RATE_LIMIT_ATTEMPTS` | Login requests allowed per IP per window (`0` disables) | `10` |
| `LOGIN_RATE_LIMIT_WINDOW_SECONDS` | Length of the rate limit window | `300` |

Generate a secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Never commit real credentials, JWT secrets, or other sensitive configuration.

---

## Testing

```bash
uv run pytest
```

The suite contains 140+ tests covering API endpoints, authentication, authorization and IDOR protection, services, repositories, schemas, security utilities, Redis behavior and failure handling, cache invalidation, transaction rollback, pagination, filtering and sorting, database constraints, health checks, rate limiting, and order cancellation.

Most unit and service tests run on SQLite for speed. Tests that depend on PostgreSQL behavior (row locks and concurrency) are marked `postgres` and run against a real PostgreSQL instance. CI runs everything against PostgreSQL and Redis service containers with throwaway credentials.

---

## Health Checks

```text
GET /health
```

The health check verifies that the application can reach PostgreSQL and returns `{"status": "ok"}`. If the database is unavailable it returns `503 Service Unavailable`, while the underlying exception is logged on the server and never exposed to the client.

---

## Docker

Docker Compose runs the local infrastructure: FastAPI, PostgreSQL, and Redis. The application image runs as an unprivileged user, starts `uvicorn` directly from the virtual environment, and installs only production dependencies. The API container has a health check that verifies the application and database connectivity.

For local development, PostgreSQL and Redis can be started on their own:

```bash
docker compose up -d db redis
```

---

## CI/CD

GitHub Actions runs on every push and pull request to `main`:

1. Install dependencies and apply migrations
2. Run the tests against PostgreSQL and Redis service containers
3. Build the Docker image

Pushes to `main` additionally publish the image (tagged with the Git commit SHA) to Amazon ECR and deploy it to EC2 through AWS Systems Manager, run the Alembic migrations, and wait for the API health check to pass.

---

## AWS Deployment

```text
GitHub Actions
      │
      ▼
 Amazon ECR
      │
      ▼
 Amazon EC2
      │
      ├── FastAPI
      ├── PostgreSQL
      └── Redis
```

AWS Systems Manager (SSM) runs the deployment commands on the instance, so no inbound SSH access is needed for deployments.

### Deployment trade-offs

The deployment is deliberately minimal because it has to fit an AWS free-tier budget:

* One `t3.micro` instance hosts the API, PostgreSQL, and Redis. A production setup would use managed services (RDS, ElastiCache) and more than one instance.
* The region is `ap-southeast-2` because that is the region available on the free plan.
* The demo is served over HTTP without TLS. A production setup would put a load balancer or reverse proxy with HTTPS in front.

---

## Local Development

### Requirements

* Python 3.13+
* Docker and Docker Compose
* uv

### 1. Clone the repository

```bash
git clone https://github.com/gonfuentes112/inventory-management.git
cd inventory-management
```

### 2. Create the environment file

```bash
cp env.example .env
```

Then set `JWT_SECRET_KEY` in `.env` (see [Configuration](#configuration)). The application will not start without a strong secret.

### 3. Start PostgreSQL and Redis

```bash
docker compose up -d db redis
```

### 4. Install dependencies

```bash
uv sync
```

### 5. Apply database migrations

```bash
uv run alembic upgrade head
```

### 6. Start the API

```bash
uv run uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`, with Swagger UI at `http://localhost:8000/docs` and ReDoc at `http://localhost:8000/redoc`.

---

## Engineering Decisions

### PostgreSQL is the source of truth
Redis improves read performance but is never required for correctness.

### Transactions protect multi-step operations
Order creation, cancellation, and the inventory changes that go with them must succeed or fail together.

### Row locking protects shared inventory
`SELECT ... FOR UPDATE` stops concurrent requests from deciding on stale stock values. Locks are always taken in ascending id order to rule out deadlocks. I chose pessimistic locking over optimistic retries because orders touch several products at once and contention on popular products is expected.

### Database constraints are a second line of defense
The application validates quantities, and PostgreSQL independently enforces `quantity >= 0`.

### Indexes follow query patterns
Indexes exist for known filtering, pagination, and relationship-loading queries rather than for every column.

### Business logic belongs in services
The API layer translates results into HTTP responses; the service layer owns the rules and the transaction boundaries.

### Business errors are typed
Specific exception types (all subclasses of `ValueError`) let the API return 404 for missing resources and 409 for conflicts instead of a generic 400.

### Fail fast on bad configuration
A weak JWT secret stops the application at startup instead of failing silently in production.

### Unexpected errors are not exposed
Clients receive safe messages while the server logs keep the diagnostic detail.

---

## Known Limitations and Future Improvements

* Refresh tokens and token revocation (access tokens currently live 30 minutes)
* Managed database and cache (RDS, ElastiCache), HTTPS, and multiple instances
* Metrics, structured logging, and alerting
* Idempotency keys for order creation
* Soft deletion of products and a richer order lifecycle (for example paid and shipped states)
* Per-account login throttling in addition to the per-IP limit
* A durable job queue for background work that must not be lost

---

## Project Status

The backend is complete. A separate **React + TypeScript** admin frontend that consumes this API is in development.

---

<a name="日本語"></a>

# 🇯🇵 日本語

## ライブデモ

インタラクティブなAPIドキュメント（Swagger UI）：

**http://3.27.38.78:8000/docs**

デモはAWS無料枠のEC2インスタンス1台で稼働しているため、停止している場合があります。通信はHTTP（暗号化なし）なので、**実際のパスワードは使用せず**、お試し用のアカウントを登録してください。

<!-- スクリーンショットを用意したらここに追加：
![Swagger UI overview](docs/images/swagger-overview.png)
-->

---

## 概要

**Inventory Management API** は、**FastAPI、PostgreSQL、Redis、Docker、AWS、GitHub Actions** を使用して開発した在庫管理用のREST APIです。

ユーザー、カテゴリー、商品、在庫数量、注文などをAPIから管理できます。

単純なCRUDにとどまらない実践的なバックエンド開発を意識し、特に以下に取り組みました。

* 認証・認可（ロール単位とオブジェクト単位）
* 注文のトランザクション処理（キャンセルを含む）
* PostgreSQLの行ロックによる同時実行制御
* データベース制約とクエリに基づくインデックス
* 障害に強いRedisキャッシュ
* ページネーション・フィルタリング・ソート
* ログインのレート制限と、不正な設定での起動拒否
* 実際の同時実行テストを含む自動テスト
* コンテナ化、CI/CD、クラウドデプロイ

---

## 主な機能

### 認証・認可

* JWTによる認証
* Argon2によるパスワードハッシュ化
* `user` / `admin` ロールによるロールベースアクセス制御（RBAC）
* オブジェクト単位の認可：自分の商品のみ変更でき、自分の注文のみ参照できる
* 管理者専用操作（ユーザー一覧、商品削除、カテゴリー管理）
* ユーザー間の不正アクセス（IDOR）対策
* クライアントIPごとのログインレート制限（Redis）
* 弱い、またはプレースホルダーのJWTシークレットではアプリケーションが起動しない

### 商品・在庫管理

* 商品CRUD、カテゴリー管理
* 商品の所有権
* 行ロックで直列化された入庫・出庫処理
* PostgreSQLの`CHECK`制約による負の在庫の防止
* ページネーション、カテゴリー・価格フィルタ、ソート
* 注文に含まれる商品の削除は`409 Conflict`で拒否

### 注文

* Order / OrderItemモデルとサーバー側での価格計算
* トランザクションによる注文作成と在庫の自動減少
* 在庫を戻す注文キャンセル（保留中の注文のみ）
* 注文所有者によるアクセス制御とページネーション
* エラー発生時のアトミックなロールバック
* 一貫した順序での`SELECT ... FOR UPDATE`行ロックにより、同時注文による過剰販売もデッドロックも防止

### データベース

* PostgreSQL 16、SQLAlchemy 2、Alembicマイグレーション
* Decimal型による金額管理
* 外部キー、一意制約、データベースレベルの在庫制約
* クエリパターンに基づくインデックス

### キャッシュ

* TTL付きのRedis商品キャッシュ
* 商品更新・在庫変更・注文変更時のキャッシュ無効化
* Redis障害時のPostgreSQLへのフォールバック
* 不正なキャッシュデータはキャッシュミスとして処理
* PostgreSQLが唯一の正しいデータソース

### テスト

* API、Service、Repository、Schema、セキュリティ、キャッシュのpytest
* Redis障害テスト、トランザクション・ロールバックテスト
* PostgreSQLの同時実行テスト（過剰販売、二重キャンセル、逆順ロック、在庫の同時更新）
* **140件以上の自動テスト**

### インフラ

* Docker / Docker Compose（非rootユーザーで実行）
* GitHub ActionsによるCI/CD
* AWS ECR、EC2、Systems Manager
* ヘルスチェック
* CORSを含む環境変数ベースの設定

---

## 技術的なポイント

FastAPIをPostgreSQLにつなぐだけでなく、現実的なバックエンドの課題に対応する機能を実装しています。

### 1. トランザクションによる注文作成とキャンセル

注文作成では、複数の更新を1つのトランザクションで処理します。

```text
商品をロック（id昇順）
        ↓
在庫確認
        ↓
在庫数量を減少
        ↓
Order / OrderItem作成
        ↓
COMMIT
```

途中でエラーが発生した場合はロールバックされ、注文が作られないまま在庫だけが減ることはありません。

保留中の注文のキャンセルでは、注文の行をロックし、続けて対象商品を（同じくid昇順で）ロックして在庫を戻し、注文を`cancelled`にします。注文行をロックしているため、同時に2つのキャンセルが届いても在庫が二重に戻ることはありません。後続のリクエストは待機し、`cancelled`状態を確認して拒否されます。

---

### 2. 同時実行制御

同じ商品を複数のリクエストが同時に更新すると、在庫数が不正になります。商品の数量を変更するすべての処理（注文作成、注文キャンセル、入庫・出庫、商品更新）は、最初に商品の行をロックします。

```sql
SELECT ...
FROM products
WHERE id = ...
FOR UPDATE;
```

```text
リクエストA                  リクエストB
    │                            │
    ▼                            ▼
商品をロック                 ロック待ち
    │                            │
    ▼                            │
在庫確認                         │
    │                            │
    ▼                            │
在庫を減少                       │
    │                            │
    ▼                            │
COMMIT                           │
                                 ▼
                            最新の在庫を取得
                                 │
                                 ▼
                            在庫を再確認
                                 │
                                 ▼
                           不足なら拒否
```

注文では商品をid昇順にロックするため、同じ商品を逆の順序で含む2つの注文でもデッドロックは発生しません。ロック後は行を再読み込み（`populate_existing`）するため、SQLAlchemyセッション内の古い値で在庫確認を行うことはありません。

テストでは、実際のPostgreSQLトランザクションと、全ワーカーを同時に開始させるバリアを使って次を検証しています。

* 3個の在庫に10人が同時に注文しても、成立する注文はちょうど3件
* 同じ商品を逆順で含む2つの注文がデッドロックしない
* 10件の同時出庫でも在庫が0未満にならない
* 10件の同時入庫でも更新が失われない
* 2件の同時キャンセルでも在庫が戻るのは1回だけ

---

### 3. データベースレベルの整合性

アプリケーション側の検証だけに頼らず、PostgreSQL側でも在庫数量を制約しています。

```text
quantity >= 0
```

アプリケーション側のチェックを誤って通過した場合でも、不正な在庫数量が保存されることを防ぎます。

---

### 4. クエリパターンに基づくインデックス

すべてのカラムにインデックスを付けるのではなく、実際のクエリに基づいて設定しています。

```text
products(category_id)
orders(user_id, created_at, id)
order_items(order_id)
```

注文一覧の次のクエリには、複合インデックスが対応します。

```sql
WHERE user_id = ?
ORDER BY created_at DESC, id DESC
```

---

### 5. 最適化としてのRedis（正しいデータはPostgreSQL）

```text
商品取得
  ↓
Redis
 ├─ Hit → キャッシュを返す
 │
 └─ Miss
      ↓
  PostgreSQL
      ↓
  キャッシュ保存（TTL 60秒）
```

Redisに障害があってもAPIは停止しません。読み取りの失敗はキャッシュミスとして扱い、書き込みや無効化の失敗も致命的エラーにはしません。更新時は、データベースのCOMMITを先に行い、その後でキャッシュを無効化します。更新と競合した読み取りが古い値を一時的に再保存する可能性はありますが、TTL（60秒）がその期間の上限になります。

---

### 6. オブジェクト単位の認可

ログイン済みであるだけでは不十分です。IDを書き換えるだけで、他のユーザーの商品を変更したり、他のユーザーの注文を参照したりできてはいけません。

```text
ログインユーザー
      ↓
所有者か？
   ┌──┴──┐
  Yes    No
   ↓      ↓
 許可   管理者か？
          │
        ┌─┴─┐
       Yes  No
        ↓    ↓
       許可 403
```

ユーザー情報は本人のみ参照でき（管理者は全員分を参照可能）、ユーザー一覧は管理者専用です。注文は常に、注文IDとログインユーザーIDの両方で検索します。

---

### 7. 意味のあるエラーレスポンス

想定されるビジネスエラーは専用の例外型として定義し、API層でHTTPステータスコードに変換します。

| 状況 | ステータス |
| --- | --- |
| 不正なリクエスト、同一注文内の重複商品 | `400 Bad Request` |
| 認証情報がない、または不正 | `401 Unauthorized` |
| このリソースを変更する権限がない | `403 Forbidden` |
| 注文・商品・ユーザーが存在しない | `404 Not Found` |
| 在庫不足、キャンセル不可の注文、注文で参照されている商品の削除 | `409 Conflict` |
| ログイン試行回数の超過 | `429 Too Many Requests` |
| データベース接続不可（ヘルスチェック） | `503 Service Unavailable` |

想定外の例外はサーバー側でログに記録し、クライアントには返しません。

---

### 8. ログインのレート制限と、設定の早期検証

* ログインは、クライアントIPごとにRedisの固定ウィンドウカウンターで制限しています（デフォルトは5分間に10回）。カウンターの加算と有効期限の設定を1つのRedisトランザクションで行うため、障害でIPが永久にロックされることはありません。Redisが停止している場合は、制限を行わずに警告をログに残します（fail-open）。
* `JWT_SECRET_KEY`が32文字未満、またはプレースホルダーのような値の場合、アプリケーションは起動しません。弱いシークレットが誤って本番に出ることを防ぎます。

---

## アーキテクチャ

```text
                    Client
                      │
                      ▼
                FastAPI API
                      │
                      ▼
              API / Dependencies
                      │
                      ▼
                  Services
                      │
                      ▼
                Repositories
                  │       │
                  ▼       ▼
             PostgreSQL  Redis
```

| レイヤー | 役割 |
| --- | --- |
| API | HTTPリクエスト・レスポンス、バリデーション、ステータスコード、依存性注入、認証の境界 |
| Service | ビジネスルール、トランザクション、認可、在庫・注文処理、キャッシュ連携 |
| Repository | データベースアクセス（行ロック付きクエリを含む） |
| Model | SQLAlchemyのモデルとリレーション |
| Schema | Pydanticのリクエスト・レスポンスモデル |
| Core | 設定、セキュリティ、ロール、ドメイン例外、レート制限 |
| Cache | Redisキャッシュと無効化 |
| Tasks | プロセス内の軽量なバックグラウンド処理（FastAPIの`BackgroundTasks`）。現在は商品作成時にログを出力するのみで、耐久性のあるジョブキューではありません |

---

## API一覧

| メソッド | パス | アクセス権 |
| --- | --- | --- |
| POST | `/users` | 誰でも（ユーザー登録） |
| POST | `/users/login` | 誰でも（レート制限あり） |
| GET | `/users` | 管理者 |
| GET | `/users/{user_id}` | 本人または管理者 |
| GET | `/categories`、`/categories/{id}` | 誰でも |
| POST、DELETE | `/categories`、`/categories/{id}` | 管理者 |
| GET | `/products`、`/products/{id}` | 誰でも |
| POST | `/products` | ログインユーザー |
| PATCH | `/products/{id}` | 所有者または管理者 |
| POST | `/products/{id}/stock/add`、`/stock/remove` | 所有者または管理者 |
| DELETE | `/products/{id}` | 管理者（注文で参照されている場合は409） |
| POST | `/orders` | ログインユーザー |
| GET | `/orders`、`/orders/{id}` | 自分の注文のみ |
| POST | `/orders/{id}/cancel` | 自分の保留中の注文のみ |
| GET | `/health` | 誰でも |

商品一覧は、カテゴリー、最低・最高価格によるフィルタ、ソート、ページネーションに対応しています。ページネーションのレスポンスは次の形式です。

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "pages": 0
}
```

---

## プロジェクト構成

```text
inventory-management/
├── app/
│   ├── api/
│   ├── cache/
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── rate_limit.py
│   │   ├── roles.py
│   │   └── security.py
│   ├── db/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── tasks/
│   └── main.py
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── api/
│   ├── cache/
│   ├── service/
│   ├── test_order_cancel.py
│   ├── test_order_concurrency.py
│   ├── test_rate_limit.py
│   ├── test_stock_concurrency.py
│   └── ...
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── Dockerfile
├── compose.yml
├── alembic.ini
├── env.example
├── pyproject.toml
└── uv.lock
```

本番環境専用の設定ファイルや秘密情報は、リポジトリには含めていません。

---

## 設定

`env.example`から`.env`を作成してください。

| 変数 | 説明 | デフォルト |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL接続URL | 必須 |
| `JWT_SECRET_KEY` | トークン署名用シークレット（32文字以上） | 必須 |
| `JWT_ALGORITHM` | JWTの署名アルゴリズム | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | アクセストークンの有効期間（分） | `30` |
| `REDIS_URL` | Redis接続URL | 必須 |
| `CORS_ORIGINS` | APIの呼び出しを許可するブラウザのオリジン（カンマ区切り） | `http://localhost:3000` |
| `LOGIN_RATE_LIMIT_ATTEMPTS` | 1ウィンドウあたりのIPごとのログイン回数上限（`0`で無効） | `10` |
| `LOGIN_RATE_LIMIT_WINDOW_SECONDS` | レート制限のウィンドウ（秒） | `300` |

シークレットは次のコマンドで生成できます。

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

実際の認証情報、JWTシークレット、その他の機密情報はリポジトリにコミットしないでください。

---

## テスト

```bash
uv run pytest
```

140件以上のテストで、APIエンドポイント、認証、認可とIDOR対策、Service、Repository、Schema、セキュリティ機能、Redisの動作と障害時の挙動、キャッシュ無効化、トランザクションのロールバック、ページネーション、フィルタ・ソート、データベース制約、ヘルスチェック、レート制限、注文キャンセルを検証しています。

多くの単体・Serviceテストは高速化のためSQLiteで実行します。行ロックや同時実行など、PostgreSQL固有の動作に依存するテストには`postgres`マーカーを付け、実際のPostgreSQLに対して実行します。CIでは、使い捨ての認証情報を持つPostgreSQLとRedisのサービスコンテナに対してすべてのテストを実行します。

---

## ヘルスチェック

```text
GET /health
```

アプリケーションがPostgreSQLに接続できることを確認し、`{"status": "ok"}`を返します。データベースが利用できない場合は`503 Service Unavailable`を返し、内部の例外はサーバー側のログに記録してクライアントには公開しません。

---

## Docker

Docker Composeで、FastAPI、PostgreSQL、Redisのローカル環境を起動できます。アプリケーションのイメージは非rootユーザーで実行され、仮想環境から直接`uvicorn`を起動し、本番用の依存関係のみをインストールします。APIコンテナにはヘルスチェックを設定しており、アプリケーションの稼働状態とデータベースへの接続を確認します。

ローカル開発では、PostgreSQLとRedisだけを起動することもできます。

```bash
docker compose up -d db redis
```

---

## CI/CD

GitHub Actionsは、`main`へのPushとPull Requestごとに次を実行します。

1. 依存関係のインストールとマイグレーションの適用
2. PostgreSQLとRedisのサービスコンテナに対するテスト実行
3. Dockerイメージのビルド

`main`へのPushでは、これに加えてコミットSHAをタグにしたイメージをAmazon ECRへPushし、AWS Systems Manager経由でEC2へデプロイし、Alembicマイグレーションを適用して、APIのヘルスチェックが通るまで待機します。

---

## AWSデプロイ

```text
GitHub Actions
      │
      ▼
 Amazon ECR
      │
      ▼
 Amazon EC2
      │
      ├── FastAPI
      ├── PostgreSQL
      └── Redis
```

インスタンス上のデプロイ処理はAWS Systems Manager（SSM）で実行するため、デプロイのために外部からのSSH接続を開放する必要はありません。

### デプロイ構成のトレードオフ

AWS無料枠の予算内に収めるため、意図的に最小構成にしています。

* `t3.micro`のインスタンス1台でAPI、PostgreSQL、Redisを動かしています。本番運用ではマネージドサービス（RDS、ElastiCache）と複数インスタンスを使用します。
* リージョンは、無料プランで利用できる`ap-southeast-2`です。
* デモはTLSなしのHTTPで公開しています。本番運用ではロードバランサーまたはリバースプロキシを置き、HTTPSにします。

---

## ローカル環境での実行

### 必要な環境

* Python 3.13+
* DockerとDocker Compose
* uv

### 1. リポジトリをクローン

```bash
git clone https://github.com/gonfuentes112/inventory-management.git
cd inventory-management
```

### 2. 環境変数ファイルを作成

```bash
cp env.example .env
```

続いて`.env`の`JWT_SECRET_KEY`を設定します（[設定](#設定)を参照）。強いシークレットがないとアプリケーションは起動しません。

### 3. PostgreSQLとRedisを起動

```bash
docker compose up -d db redis
```

### 4. 依存関係をインストール

```bash
uv sync
```

### 5. マイグレーションを適用

```bash
uv run alembic upgrade head
```

### 6. APIを起動

```bash
uv run uvicorn app.main:app --reload
```

APIは`http://localhost:8000`、Swagger UIは`http://localhost:8000/docs`、ReDocは`http://localhost:8000/redoc`で利用できます。

---

## 設計上のポイント

### PostgreSQLを正しいデータソースとして使用
Redisは読み取り性能を向上させますが、正しさのために必須ではありません。

### トランザクションで複数操作を保護
注文の作成・キャンセルと、それに伴う在庫変更は、すべて成功するか、すべて失敗します。

### 行ロックによる在庫の保護
`SELECT ... FOR UPDATE`により、古い在庫値に基づく判断を防ぎます。デッドロックを避けるため、ロックは常にid昇順で取得します。注文は複数の商品を同時に扱い、人気商品への競合が想定されるため、楽観的なリトライではなく悲観的ロックを選びました。

### データベース制約による二重の保護
アプリケーションが数量を検証するのに加えて、PostgreSQLが`quantity >= 0`を保証します。

### クエリに基づいたインデックス設計
すべてのカラムではなく、実際の検索、ページネーション、リレーション読み込みに必要なインデックスのみを追加しています。

### ビジネスロジックのService層への分離
API層はHTTPレスポンスへの変換を担当し、Service層がビジネスルールとトランザクションの境界を担当します。

### ビジネスエラーを型で区別
専用の例外型（すべて`ValueError`のサブクラス）により、汎用的な400ではなく、存在しない場合は404、競合の場合は409を返せます。

### 不正な設定は起動時に失敗させる
弱いJWTシークレットは、本番環境で気づかれずに動き続けるのではなく、起動時に停止させます。

### 内部エラーをクライアントへ公開しない
クライアントには安全なメッセージを返し、詳細な診断情報はサーバーログに残します。

---

## 既知の制限と今後の改善

* リフレッシュトークンとトークンの失効（現在のアクセストークンの有効期間は30分）
* マネージドなデータベース・キャッシュ（RDS、ElastiCache）、HTTPS、複数インスタンス化
* メトリクス、構造化ログ、アラート
* 注文作成のIdempotency Key
* 商品の論理削除と、より詳細な注文のライフサイクル（支払済み、発送済みなど）
* IPごとの制限に加えた、アカウント単位のログイン制限
* 失ってはいけないバックグラウンド処理のための、耐久性のあるジョブキュー

---

## プロジェクトの現在の状態

バックエンドは完成しています。このAPIを利用する、独立した**React + TypeScript**の管理画面を開発中です。

---

**Repository:** https://github.com/gonfuentes112/inventory-management