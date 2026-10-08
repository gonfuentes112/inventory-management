# Inventory Management API

A production-oriented inventory management REST API built with **FastAPI, PostgreSQL, Redis, Docker, and GitHub Actions**.

The project focuses on practical backend engineering: layered architecture, authentication and authorization, transactional database operations, concurrency control, caching, API pagination/filtering, automated testing, database migrations, containerization, CI/CD, and production-oriented error handling.

**Languages:** [English](#english) | [日本語](#日本語)

---

<a name="english"></a>

# 🇬🇧 English

## Overview

**Inventory Management API** is a backend application for managing users, categories, products, inventory quantities, and orders through a RESTful API.

The project was built to demonstrate backend engineering beyond basic CRUD operations, with particular focus on:

* Secure authentication and authorization
* Object-level ownership checks
* Transactional order processing
* PostgreSQL concurrency control
* Database constraints and indexes
* Redis caching with graceful failure handling
* Pagination, filtering, and sorting
* Automated testing
* Containerized development
* CI/CD and production deployment
* Health checks and error handling

---

## Key Features

### Authentication & Authorization

* JWT-based authentication
* Argon2 password hashing
* Role-based access control (RBAC)
* Authentication dependencies
* Admin-only operations
* Object-level authorization for user-owned products
* Protection against cross-user access / IDOR

### Product & Inventory Management

* Product CRUD
* Category management
* Product ownership
* Inventory quantity management
* Stock addition and removal
* PostgreSQL `CHECK` constraint preventing negative inventory
* Product pagination
* Category and price filtering
* Sorting by product attributes

### Orders

* Order and OrderItem models
* Server-side price calculation
* Transactional order creation
* Automatic inventory deduction
* Order ownership protection
* Order pagination
* Atomic rollback on failure
* PostgreSQL row-level locking with `SELECT ... FOR UPDATE`
* Protection against concurrent overselling

### Database

* PostgreSQL 16
* SQLAlchemy 2
* Alembic migrations
* Decimal monetary values
* Foreign-key relationships
* Database-level inventory constraints
* Query-oriented indexes

### Caching

* Redis product caching
* Cache expiration with TTL
* Cache invalidation after product mutations
* Cache invalidation after order-based stock changes
* Graceful fallback when Redis is unavailable
* Invalid cache data treated as a cache miss
* Database remains the source of truth

### Testing

* pytest
* API tests
* Service tests
* Repository tests
* Schema validation tests
* Authentication and security tests
* Redis failure tests
* Transaction rollback tests
* Health-check tests
* PostgreSQL concurrency testing
* **143 collected tests**

### Infrastructure

* Docker
* Docker Compose
* GitHub Actions
* AWS ECR
* AWS EC2
* AWS Systems Manager
* Application health checks
* Environment-based configuration

---

## Technical Highlights

The main goal of this project was not simply to connect FastAPI to PostgreSQL.

Several features were specifically implemented to address realistic backend problems.

### 1. Transactional Order Creation

Creating an order modifies several pieces of data:

```text
Product stock
      │
      ▼
Create Order
      │
      ▼
Create OrderItems
      │
      ▼
Commit transaction
```

All of these operations occur within the same database transaction.

If an error occurs during the operation, the transaction is rolled back so that inventory cannot be reduced while the corresponding order fails to be created.

---

### 2. Concurrency Control

Inventory updates can become incorrect when multiple requests attempt to purchase the same product simultaneously.

For order creation, product rows are locked using PostgreSQL row-level locking:

```sql
SELECT ...
FROM products
WHERE id = ...
FOR UPDATE;
```

The application locks products in a consistent order before modifying their quantities.

Conceptually:

```text
Request A                    Request B
    │                            │
    ▼                            ▼
Lock product                 Wait for lock
    │                            │
    ▼                            │
Check stock                     │
    │                            │
    ▼                            │
Decrease stock                  │
    │                            │
    ▼                            │
Commit                          │
                                 ▼
                            Read current stock
                                 │
                                 ▼
                           Check stock again
                                 │
                                 ▼
                         Reject if insufficient
```

A PostgreSQL concurrency test verifies that two simultaneous orders cannot oversell the final unit of inventory.

---

### 3. Database-Level Integrity

Application validation is not the only line of defense.

The `products` table also enforces:

```text
quantity >= 0
```

at the PostgreSQL level.

This protects the database even if an application-level validation path is accidentally bypassed.

---

### 4. Query-Oriented Indexes

Indexes were added based on actual query patterns rather than indexing every column.

Current indexes include:

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

The `order_items(order_id)` index supports loading order items efficiently.

The project deliberately avoids unnecessary indexes where the current workload does not justify them.

---

### 5. Redis as an Optimization, Not the Source of Truth

Redis is used to accelerate product reads, but PostgreSQL remains authoritative.

The cache flow is:

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
        Cache result
```

Redis failures do not make the API unavailable.

For example:

```text
Redis GET fails
      │
      ▼
Treat as cache miss
      │
      ▼
Read PostgreSQL
      │
      ▼
Return product
```

Cache writes and invalidation failures are also treated as non-fatal because Redis is an optimization rather than the system of record.

---

### 6. Cache Invalidation

Product mutations invalidate the corresponding cached product.

This includes:

* Product updates
* Product deletion
* Stock additions
* Stock removals
* Order-based inventory reductions

Order processing therefore follows:

```text
Create order
     │
     ▼
Decrease stock
     │
     ▼
Commit PostgreSQL transaction
     │
     ▼
Invalidate affected product cache
```

The database transaction is completed before cache invalidation.

---

### 7. Object-Level Authorization

Authentication alone is not sufficient.

A user may be authenticated but still must not be able to modify another user's product.

Product operations therefore verify ownership:

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

This prevents IDOR-style access where a user attempts to manipulate another user's resource simply by changing an object ID.

---

## Architecture

The application uses a layered backend architecture:

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

### API Layer

Responsible for:

* HTTP requests and responses
* Request validation
* HTTP status codes
* Dependency injection
* Authentication/authorization boundaries

### Service Layer

Responsible for:

* Business rules
* Transactions
* Authorization checks
* Inventory operations
* Order processing
* Cache coordination

### Repository Layer

Responsible for:

* Database queries
* Persistence
* PostgreSQL-specific operations

### Model Layer

Defines SQLAlchemy database models and relationships.

### Schema Layer

Defines Pydantic request and response models.

### Core Layer

Contains:

* Application configuration
* Security utilities
* Roles
* Authentication-related functionality

### Cache Layer

Contains Redis caching and cache invalidation logic.

### Task Layer

Contains background processing for operations that do not need to block the main HTTP response.

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
│   │   ├── roles.py
│   │   └── security.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── redis.py
│   │
│   ├── models/
│   │   ├── category.py
│   │   ├── order.py
│   │   ├── product.py
│   │   └── user.py
│   │
│   ├── repositories/
│   │   ├── category.py
│   │   ├── order.py
│   │   ├── product.py
│   │   └── user.py
│   │
│   ├── schemas/
│   │   ├── category.py
│   │   ├── inventory.py
│   │   ├── order.py
│   │   ├── pagination.py
│   │   ├── product.py
│   │   └── user.py
│   │
│   ├── services/
│   │   ├── category.py
│   │   ├── order.py
│   │   ├── product.py
│   │   └── user.py
│   │
│   ├── tasks/
│   │   └── product.py
│   │
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
│   ├── test_order_concurrency.py
│   ├── test_product_tasks.py
│   ├── test_repositories.py
│   ├── test_schemas.py
│   ├── test_security.py
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

## Authentication & Authorization

Authentication uses JSON Web Tokens (JWT).

Passwords are hashed with **Argon2** before being stored in PostgreSQL.

Authorization includes both role-level and object-level controls.

Security-related functionality includes:

* Password hashing
* Password verification
* JWT access-token generation
* JWT validation
* Authentication dependencies
* Role-based authorization
* Product ownership checks
* Cross-user resource protection
* Request validation
* Database integrity constraints

Login failures intentionally return the same message for an invalid username or password rather than revealing whether a particular account exists.

---

## API Design

The API supports operations for:

```text
/users
/users/login

/categories
/categories/{category_id}

/products
/products/{product_id}
/products/{product_id}/stock/add
/products/{product_id}/stock/remove

/orders
/orders/{order_id}
```

Product and order collection endpoints support pagination.

Product listing additionally supports:

* Category filtering
* Minimum price
* Maximum price
* Sorting
* Sort direction

Pagination responses include:

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

## Error Handling

Expected business errors are converted into appropriate HTTP responses at the API boundary.

Examples include:

```text
400 Bad Request
403 Forbidden
404 Not Found
409 Conflict
503 Service Unavailable
```

Unexpected exceptions are not returned directly to clients.

The health endpoint specifically reports database unavailability as:

```text
503 Service Unavailable
```

while the server records the underlying exception for troubleshooting.

---

## Database & Migrations

The project uses:

* **PostgreSQL 16** for persistent data
* **SQLAlchemy 2** for database access
* **Alembic** for schema migrations

Database migrations are version controlled and support upgrades and downgrades.

The schema includes:

* Users
* Categories
* Products
* Orders
* Order items
* Foreign-key relationships
* Unique constraints
* Inventory constraints
* Query-oriented indexes

Monetary values are represented using decimal database types rather than floating-point values.

---

## Testing

The project uses **pytest** with tests covering multiple layers of the application.

The current suite contains **143 collected tests**.

Coverage includes:

* API endpoints
* Authentication
* Authorization
* IDOR protection
* Services
* Repositories
* Schemas
* Security utilities
* Redis cache behavior
* Redis failure handling
* Cache invalidation
* Transaction rollback
* Order processing
* Pagination
* Filtering and sorting
* Database constraints
* Health checks
* PostgreSQL concurrency

A particularly important test verifies that concurrent order requests cannot oversell inventory.

The test suite uses SQLite for many fast unit/service tests and PostgreSQL for PostgreSQL-specific behavior such as concurrency testing.

CI also runs the application against PostgreSQL and Redis services.

Run the complete test suite with:

```bash
uv run pytest
```

---

## Health Checks & Observability

The application provides:

```text
GET /health
```

The health check verifies that the application can successfully communicate with PostgreSQL.

Successful response:

```json
{
  "status": "ok"
}
```

If PostgreSQL is unavailable, the endpoint returns:

```text
503 Service Unavailable
```

Unexpected health-check failures are logged server-side with their exception traceback while exposing only a safe error message to the client.

---

## Docker

Docker Compose can be used to run the application infrastructure locally.

The development environment includes:

* FastAPI
* PostgreSQL
* Redis

For local development, PostgreSQL and Redis can also be started independently:

```bash
docker compose up -d db redis
```

The API can then be run directly with Python and `uv`.

---

## CI/CD

GitHub Actions is used to automate testing and Docker image builds.

The CI workflow verifies the application before changes are merged.

The deployment configuration also supports publishing Docker images to Amazon ECR and deploying to Amazon EC2 through AWS Systems Manager.

Docker images can be tagged using the Git commit SHA, providing traceability between source code and built images.

---

## AWS Deployment

AWS deployment was implemented as part of the project to gain practical experience with container deployment and remote infrastructure management.

The deployment architecture uses:

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

AWS Systems Manager (SSM) is used for remote deployment operations.

The deployment process includes:

1. Build the Docker image
2. Push the image to Amazon ECR
3. Deploy the image to EC2
4. Start the application containers
5. Apply pending Alembic migrations
6. Verify application health

AWS deployment is intentionally treated as an infrastructure component of the project rather than a requirement for local development.

---

## API Documentation

FastAPI automatically provides interactive API documentation.

### Swagger UI

```text
http://localhost:8000/docs
```

### ReDoc

```text
http://localhost:8000/redoc
```

### Health Check

```text
GET /health
```

---

## Local Development

### Requirements

* Python 3.13+
* Docker
* Docker Compose
* uv

### 1. Clone the repository

```bash
git clone https://github.com/gonfuentes112/inventory-management.git
cd inventory-management
```

### 2. Create the environment file

Copy the example environment file:

```bash
cp env.example .env
```

Adjust the values for the local environment if necessary.

### 3. Start PostgreSQL and Redis

```bash
docker compose up -d db redis
```

### 4. Install Python dependencies

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

The API will be available at:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

---

## Environment Variables

Create a `.env` file based on `env.example`.

Example:

```env
DATABASE_URL=postgresql+psycopg://inventory:inventory@db:5432/inventory
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://redis:6379/0
```

Never commit real credentials, JWT secrets, or other sensitive configuration to the repository.

---

## Engineering Decisions

Some of the main design decisions in this project are intentional tradeoffs.

### PostgreSQL is the source of truth

Redis improves read performance but is not required for correctness.

### Transactions protect multi-step operations

Order creation and inventory changes must succeed or fail together.

### Row locking protects shared inventory

`SELECT ... FOR UPDATE` prevents concurrent requests from making decisions based on stale stock values.

### Database constraints provide a second line of defense

The application validates inventory quantities, while PostgreSQL independently enforces `quantity >= 0`.

### Indexes are based on query patterns

Indexes were added for known filtering, pagination, and relationship-loading queries rather than indiscriminately indexing columns.

### Business logic belongs in services

The API layer translates business results into HTTP responses while the service layer owns application rules and transaction boundaries.

### Unexpected errors are not exposed

Clients receive safe error messages while server-side logs retain diagnostic information.

---

## Project Status

This project is considered the completed backend project in my portfolio roadmap.

The next portfolio project is a separate **React + TypeScript inventory administration frontend** that consumes this API.

---

<a name="日本語"></a>

# 🇯🇵 日本語

## 概要

**Inventory Management API** は、**FastAPI、PostgreSQL、Redis、Docker、GitHub Actions** を使用して開発した在庫管理用のREST APIです。

ユーザー、カテゴリー、商品、在庫数量、注文などをAPIから管理できます。

単純なCRUDだけではなく、実践的なバックエンド開発を意識し、以下のような機能を実装しています。

* 認証・認可
* オブジェクト単位のアクセス制御
* トランザクション処理
* 同時実行制御
* PostgreSQLの制約・インデックス
* Redisキャッシュ
* キャッシュ障害時のフォールバック
* ページネーション
* フィルタリング・ソート
* 自動テスト
* データベースマイグレーション
* Docker
* CI/CD
* ヘルスチェック
* 本番環境を意識したエラーハンドリング

---

## 主な機能

### 認証・認可

* JWTによる認証
* Argon2によるパスワードハッシュ化
* ロールベースアクセス制御（RBAC）
* Authentication Dependency
* 管理者専用操作
* 商品所有者によるオブジェクト単位の認可
* ユーザー間の不正アクセス（IDOR）対策

### 商品・在庫管理

* 商品CRUD
* カテゴリー管理
* 商品所有権
* 在庫数量管理
* 入庫・出庫処理
* PostgreSQLによる負の在庫数量の防止
* 商品一覧のページネーション
* カテゴリー・価格によるフィルタリング
* 商品属性によるソート

### 注文

* Order / OrderItemモデル
* サーバー側での商品価格計算
* トランザクションによる注文作成
* 注文作成時の在庫自動減少
* 注文所有者によるアクセス制御
* 注文一覧のページネーション
* エラー発生時のロールバック
* PostgreSQLの`SELECT ... FOR UPDATE`
* 同時注文による在庫の過剰販売防止

### データベース

* PostgreSQL 16
* SQLAlchemy 2
* Alembic
* Decimal型による金額管理
* 外部キー
* データベース制約
* クエリパターンに基づくインデックス

### キャッシュ

* Redisによる商品キャッシュ
* TTLによるキャッシュ有効期限
* 商品更新時のキャッシュ無効化
* 注文による在庫変更時のキャッシュ無効化
* Redis障害時のPostgreSQLフォールバック
* 不正なキャッシュデータをキャッシュミスとして処理
* PostgreSQLを唯一の正しいデータソースとして利用

### テスト

* pytest
* APIテスト
* Serviceテスト
* Repositoryテスト
* Schemaテスト
* 認証・セキュリティテスト
* Redis障害テスト
* トランザクション・ロールバックテスト
* ヘルスチェックテスト
* PostgreSQL同時実行テスト
* **143テスト**

---

## 技術的なポイント

### 1. トランザクションによる注文処理

注文作成では、複数のデータベース操作を1つのトランザクションとして処理します。

```text
在庫確認・ロック
      ↓
在庫数量変更
      ↓
Order作成
      ↓
OrderItem作成
      ↓
COMMIT
```

途中でエラーが発生した場合はロールバックされ、在庫だけが減少したり、Orderだけが作成されたりする状態を防ぎます。

---

### 2. 同時実行制御

同じ商品を複数のユーザーが同時に注文する場合、在庫数を正しく管理する必要があります。

そのため、注文作成時にはPostgreSQLの行ロックを使用しています。

```sql
SELECT ...
FROM products
WHERE id = ...
FOR UPDATE;
```

これにより、同じ商品を同時に更新しようとするトランザクション間で競合を制御します。

PostgreSQLを使用した同時実行テストによって、最後の1個を複数の注文が同時に購入して在庫がマイナスになるケースを防止できることを確認しています。

---

### 3. データベースレベルの整合性

アプリケーション側だけでなく、PostgreSQL側でも在庫数量を制約しています。

```text
quantity >= 0
```

これにより、アプリケーション側のチェックを誤って通過した場合でも、データベースに不正な在庫数量が保存されることを防ぎます。

---

### 4. クエリパターンに基づくインデックス

現在のアクセスパターンを考慮して、以下のインデックスを設定しています。

```text
products(category_id)

orders(user_id, created_at, id)

order_items(order_id)
```

例えば注文一覧では、

```sql
WHERE user_id = ?
ORDER BY created_at DESC, id DESC
```

というクエリを使用するため、それに対応した複合インデックスを設定しています。

不要なインデックスをすべてのカラムに追加するのではなく、実際のクエリパターンに基づいて設計しています。

---

### 5. Redisを最適化として利用

Redisは読み取り性能を向上させるために使用していますが、データの正しい状態はPostgreSQLが保持します。

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
  キャッシュ保存
```

Redisに接続できない場合でも、PostgreSQLから取得することでAPI自体は継続して動作できます。

---

### 6. キャッシュ無効化

以下の操作では対象商品のRedisキャッシュを無効化します。

* 商品更新
* 商品削除
* 在庫追加
* 在庫減少
* 注文による在庫減少

注文処理では、データベースのCOMMIT後にキャッシュを無効化します。

---

### 7. オブジェクト単位の認可

ログイン済みであるだけでは、他のユーザーの商品を変更できないようにしています。

```text
ログインユーザー
      ↓
商品所有者か？
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

これにより、URL内の商品IDを変更するだけで他ユーザーの商品を操作できるIDOR型の問題を防止しています。

---

## アーキテクチャ

アプリケーションはレイヤードアーキテクチャを採用しています。

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

### API層

HTTPリクエスト、レスポンス、バリデーション、Dependency Injection、認証・認可の境界を担当します。

### Service層

ビジネスロジック、トランザクション、認可、在庫処理、注文処理などを担当します。

### Repository層

データベースへのアクセスを担当します。

### Model層

SQLAlchemyのデータベースモデルとリレーションを定義します。

### Schema層

Pydanticによるリクエスト・レスポンスモデルを定義します。

### Core層

設定、セキュリティ、ロールなどを管理します。

### Cache層

Redisによるキャッシュとキャッシュ無効化を担当します。

### Task層

HTTPレスポンスを不必要に遅延させないバックグラウンド処理を担当します。

---

## 認証・認可

認証にはJWTを使用しています。

パスワードはデータベースへ保存する前に**Argon2**でハッシュ化します。

また、RBACだけではなく、商品所有者かどうかを確認するオブジェクト単位の認可も実装しています。

主なセキュリティ機能：

* パスワードハッシュ化
* パスワード検証
* JWTアクセストークン発行
* JWT検証
* Authentication Dependency
* RBAC
* 商品所有権チェック
* クロスユーザーアクセス防止
* Pydanticによる入力バリデーション
* PostgreSQLによるデータ整合性制約

ログイン時には、ユーザー名が存在しない場合とパスワードが間違っている場合で同じエラーメッセージを返すことで、アカウントの存在を推測しにくい設計にしています。

---

## テスト

自動テストには**pytest**を使用しています。

現在、**143テスト**を収集・実行できる状態です。

テスト対象：

* API
* 認証
* 認可
* IDOR対策
* Service
* Repository
* Schema
* セキュリティ
* Redis
* Redis障害時のフォールバック
* キャッシュ無効化
* トランザクション・ロールバック
* 注文処理
* ページネーション
* フィルタリング・ソート
* ヘルスチェック
* PostgreSQL同時実行制御

特にPostgreSQLを使用した同時実行テストでは、同じ在庫に対する同時注文による過剰販売を防止できることを確認しています。

全テストの実行：

```bash
uv run pytest
```

---

## ヘルスチェック

以下のエンドポイントを提供しています。

```text
GET /health
```

PostgreSQLへの接続を確認し、正常な場合は：

```json
{
  "status": "ok"
}
```

を返します。

PostgreSQLが利用できない場合は、

```text
503 Service Unavailable
```

を返します。

内部エラーの詳細はクライアントへ公開せず、サーバー側のログに記録します。

---

## Docker

Docker Composeを使用して以下の環境を起動できます。

* FastAPI
* PostgreSQL
* Redis

ローカル開発では、PostgreSQLとRedisだけをDockerで起動し、FastAPIを`uvicorn`から直接起動する構成も利用できます。

---

## CI/CD

GitHub Actionsを使用して自動テストとDockerイメージのビルドを行います。

また、AWS ECRへのイメージ登録、EC2へのデプロイ、Alembicによるマイグレーション、ヘルスチェックまで含むデプロイ構成も実装しています。

DockerイメージにはGitのコミットSHAを利用することで、ソースコードとビルド済みイメージを対応付けられるようにしています。

---

## AWSデプロイ

AWSを使用したコンテナデプロイも実装しています。

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

AWS Systems Manager（SSM）を利用してEC2上のデプロイ処理を実行します。

主な流れ：

1. Dockerイメージをビルド
2. Amazon ECRへPush
3. EC2へデプロイ
4. コンテナを起動
5. Alembicマイグレーションを適用
6. ヘルスチェックを実行

AWS環境はローカル開発には必須ではなく、コンテナデプロイやインフラ運用を学ぶための構成として実装しています。

---

## APIドキュメント

FastAPIによって以下のドキュメントが自動生成されます。

### Swagger UI

```text
http://localhost:8000/docs
```

### ReDoc

```text
http://localhost:8000/redoc
```

---

## ローカル環境での実行

### 必要な環境

* Python 3.13+
* Docker
* Docker Compose
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

必要に応じてローカル環境用に値を変更してください。

### 3. PostgreSQLとRedisを起動

```bash
docker compose up -d db redis
```

### 4. Python依存関係をインストール

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

API：

```text
http://localhost:8000
```

Swagger UI：

```text
http://localhost:8000/docs
```

---

## 環境変数

`env.example`を参考に`.env`を作成してください。

```env
DATABASE_URL=postgresql+psycopg://inventory:inventory@db:5432/inventory
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://redis:6379/0
```

実際の認証情報、JWT秘密鍵、その他の秘密情報をリポジトリへコミットしないでください。

---

## 設計上のポイント

### PostgreSQLを正しいデータソースとして使用

Redisは性能向上のためのキャッシュであり、データの正しい状態はPostgreSQLが保持します。

### トランザクションで複数操作を保護

注文作成と在庫変更を同一トランザクションとして処理します。

### 行ロックによる同時実行制御

`SELECT ... FOR UPDATE`を使用して、共有される在庫データに対する競合を制御します。

### データベース制約による二重の保護

アプリケーション側のバリデーションに加えて、PostgreSQL側でも`quantity >= 0`を保証します。

### クエリに基づいたインデックス設計

すべてのカラムにインデックスを追加するのではなく、実際の検索・ページネーション・リレーション読み込みに必要なインデックスだけを追加しています。

### Service層へのビジネスロジック分離

API層はHTTP処理を担当し、Service層がビジネスルールとトランザクションを担当します。

### 内部エラーをクライアントへ公開しない

クライアントには安全なエラーメッセージを返し、詳細な例外情報はサーバーログで確認できるようにしています。

---

## プロジェクトの現在の状態

このプロジェクトは、ポートフォリオにおけるバックエンドプロジェクトとして完成しています。

次のプロジェクトでは、**React + TypeScript**を使用した独立したInventory管理画面を開発し、このREST APIを利用する予定です。

---

**Repository:** https://github.com/gonfuentes112/inventory-management
