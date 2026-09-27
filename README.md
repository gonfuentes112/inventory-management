# Inventory Management API

A production-oriented inventory management REST API built with FastAPI, PostgreSQL, Redis, Docker, AWS, and GitHub Actions.

**Languages:** [English](#english) | [日本語](#日本語)

---

<a name="english"></a>

# 🇬🇧 English

## Overview

**Inventory Management API** is a backend application designed to manage products, categories, users, and inventory quantities through a RESTful API.

The project was developed with a focus on practical backend engineering, including layered application architecture, authentication and authorization, database migrations, caching, background processing, automated testing, containerization, and cloud deployment.

The application is deployed to **AWS EC2** using Docker and is automatically tested and deployed through **GitHub Actions**.

[⬆ Back to top](#inventory-management-api)

## Features

* User registration and management
* JWT-based authentication
* Password hashing with Argon2
* Role-based access control (RBAC)
* Product management
* Category management
* Inventory quantity management
* PostgreSQL database
* SQLAlchemy ORM
* Alembic database migrations
* Redis caching
* Background tasks
* Pydantic request/response validation
* Repository and service layers
* Automated testing with pytest
* Dockerized development and production environments
* GitHub Actions CI/CD
* AWS ECR container image storage
* AWS EC2 deployment
* AWS Systems Manager for remote deployment
* Application health checks

[⬆ Back to top](#inventory-management-api)

## Tech Stack

| Category           | Technologies              |
| ------------------ | ------------------------- |
| Language           | Python 3.13               |
| Framework          | FastAPI                   |
| Database           | PostgreSQL 16             |
| ORM                | SQLAlchemy                |
| Migrations         | Alembic                   |
| Validation         | Pydantic                  |
| Authentication     | JWT, Argon2               |
| Cache              | Redis 7                   |
| Testing            | pytest                    |
| Package Management | uv                        |
| Containerization   | Docker, Docker Compose    |
| CI/CD              | GitHub Actions            |
| Cloud              | AWS                       |
| Container Registry | Amazon ECR                |
| Compute            | Amazon EC2                |
| Remote Deployment  | AWS Systems Manager (SSM) |

[⬆ Back to top](#inventory-management-api)

## Architecture

The application follows a layered backend architecture:

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
  │
  ├──────────────► PostgreSQL
  │
  └──────────────► Redis
```

The main application layers are separated by responsibility:

* **API layer** handles HTTP requests, responses, and dependency injection.
* **Service layer** contains business logic.
* **Repository layer** handles database operations.
* **Model layer** defines SQLAlchemy database models.
* **Schema layer** defines Pydantic request and response models.
* **Core layer** contains configuration, security, and application roles.
* **Cache layer** provides Redis-based caching.
* **Task layer** contains background processing.

This separation keeps business logic independent from HTTP and database-specific concerns.

[⬆ Back to top](#inventory-management-api)

## Project Structure

```text
inventory-management/
├── app/
│   ├── api/
│   │   ├── category.py
│   │   ├── dependencies.py
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
│   │   ├── product.py
│   │   └── user.py
│   │
│   ├── repositories/
│   │   ├── category.py
│   │   ├── product.py
│   │   └── user.py
│   │
│   ├── schemas/
│   │   ├── category.py
│   │   ├── inventory.py
│   │   ├── product.py
│   │   └── user.py
│   │
│   ├── services/
│   │   ├── category.py
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
│   ├── test_auth.py
│   ├── test_category_api.py
│   ├── test_category_service.py
│   ├── test_product_service.py
│   ├── test_products_api.py
│   ├── test_product_tasks.py
│   ├── test_repositories.py
│   ├── test_schemas.py
│   ├── test_security.py
│   ├── test_user.py
│   ├── test_user_api.py
│   └── test_user_service.py
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── Dockerfile
├── compose.yml
├── alembic.ini
├── pyproject.toml
└── uv.lock
```

Production-only configuration files containing deployment settings and secrets are intentionally excluded from the repository.

[⬆ Back to top](#inventory-management-api)

## Authentication & Authorization

Authentication is implemented using JSON Web Tokens (JWT).

Passwords are securely hashed using **Argon2** before being stored in the database.

The application also implements role-based access control (RBAC), allowing API operations to be restricted according to the authenticated user's role.

The security layer includes:

* Password hashing
* Password verification
* JWT access-token generation
* JWT token validation
* Authentication dependencies
* Role-based authorization

[⬆ Back to top](#inventory-management-api)

## Inventory Management

Products contain inventory quantities that can be created and updated through the API.

The database also enforces a non-negative quantity constraint:

```text
quantity >= 0
```

This constraint is enforced at the PostgreSQL level in addition to application-level validation.

The project uses Alembic to maintain the database schema through versioned migrations.

[⬆ Back to top](#inventory-management-api)

## Caching & Background Tasks

Redis is used as a caching layer for product-related operations.

The project also includes background task processing for operations that do not need to block the main HTTP response.

This demonstrates the use of external infrastructure beyond the primary relational database.

[⬆ Back to top](#inventory-management-api)

## Database & Migrations

The application uses:

* **PostgreSQL 16** for persistent data
* **SQLAlchemy 2** for ORM/database access
* **Alembic** for schema migrations

The migration history is version controlled and supports both upgrades and downgrades.

The migration chain includes changes for:

* Initial database tables
* Product pricing
* User password hashes
* User roles
* Product quantities
* Product quantity constraints

The production deployment automatically runs:

```bash
uv run alembic upgrade head
```

before the final application health verification.

[⬆ Back to top](#inventory-management-api)

## Testing

The project uses **pytest** for automated testing.

Tests cover multiple application layers, including:

* API endpoints
* Services
* Repositories
* Schemas
* Authentication
* Security
* Background tasks

The test environment uses PostgreSQL and Redis services in CI.

Tests are executed automatically for pull requests and pushes to `main`.

[⬆ Back to top](#inventory-management-api)

## Docker

The application can be run using Docker Compose with:

* FastAPI application
* PostgreSQL
* Redis

The API container includes a healthcheck that verifies application availability and database connectivity.

The production deployment uses a separate Compose configuration that pulls the application image from Amazon ECR.

[⬆ Back to top](#inventory-management-api)

## CI/CD

GitHub Actions is used to automate testing and deployment.

The pipeline follows this process:

```text
Push / Pull Request
        │
        ▼
Install dependencies
        │
        ▼
Run tests
        │
        ▼
Build Docker image
        │
        ▼
       main
        │
        ▼
Push image to Amazon ECR
        │
        ▼
Deploy to EC2 through AWS SSM
        │
        ▼
Run Alembic migrations
        │
        ▼
Verify API health
```

Pull requests run the test and Docker build stages.

Pushes to `main` additionally trigger the deployment process.

Docker images are tagged using the Git commit SHA, providing traceability between source code and deployed versions.

[⬆ Back to top](#inventory-management-api)

## AWS Deployment

The application is deployed using the following AWS services:

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

AWS Systems Manager (SSM) is used to execute deployment commands on the EC2 instance.

The deployment process:

1. Builds the Docker image.
2. Pushes the image to Amazon ECR.
3. Connects to the EC2 instance through SSM.
4. Pulls the new image.
5. Starts the application containers.
6. Applies pending Alembic migrations.
7. Checks the application health status.

[⬆ Back to top](#inventory-management-api)

## API Documentation

When the application is running, FastAPI automatically provides interactive API documentation.

### Swagger UI

```text
http://localhost:8000/docs
```

### ReDoc

```text
http://localhost:8000/redoc
```

The API also provides a health endpoint:

```text
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

[⬆ Back to top](#inventory-management-api)

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

Adjust the values for your local environment if necessary.

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

[⬆ Back to top](#inventory-management-api)

## Environment Variables

Create a `.env` file based on `env.example`.

```env
DATABASE_URL=postgresql+psycopg://inventory:inventory@db:5432/inventory
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://redis:6379/0
```

Do not commit `.env` or other files containing real credentials or secrets.

[⬆ Back to top](#inventory-management-api)

## Future Improvements

Potential future improvements include:

* More comprehensive integration tests
* Additional inventory operations
* Monitoring and observability
* More granular authorization policies
* Production database separation from the application host
* Additional automated deployment safeguards

[⬆ Back to top](#inventory-management-api)

---

<a name="日本語"></a>

# 🇯🇵 日本語

## 概要

**Inventory Management API** は、FastAPI、PostgreSQL、Redis、Docker、AWS、GitHub Actionsを使用して開発した、在庫管理用のREST APIです。

商品、カテゴリー、ユーザー、在庫数量などをAPIから管理できます。

実践的なバックエンド開発を意識し、レイヤードアーキテクチャ、認証・認可、データベースマイグレーション、キャッシュ、バックグラウンド処理、自動テスト、コンテナ化、クラウドデプロイなどを実装しています。

アプリケーションは **AWS EC2** 上でDockerを使用して稼働し、**GitHub Actions** によるCI/CDパイプラインを利用して自動テストおよびデプロイを行います。

[⬆ ページ上部へ](#inventory-management-api)

## 主な機能

* ユーザー登録・管理
* JWTによる認証
* Argon2によるパスワードハッシュ化
* ロールベースアクセス制御（RBAC）
* 商品管理
* カテゴリー管理
* 在庫数量管理
* PostgreSQLデータベース
* SQLAlchemy ORM
* Alembicによるデータベースマイグレーション
* Redisによるキャッシュ
* バックグラウンドタスク
* Pydanticによるリクエスト・レスポンスのバリデーション
* Repository / Serviceレイヤー
* pytestによる自動テスト
* Dockerによる開発・本番環境
* GitHub ActionsによるCI/CD
* Amazon ECRへのコンテナイメージ保存
* Amazon EC2へのデプロイ
* AWS Systems Managerによるリモートデプロイ
* アプリケーションのヘルスチェック

[⬆ ページ上部へ](#inventory-management-api)

## 技術スタック

| 分類        | 技術                       |
| --------- | ------------------------ |
| 言語        | Python 3.13              |
| フレームワーク   | FastAPI                  |
| データベース    | PostgreSQL 16            |
| ORM       | SQLAlchemy               |
| マイグレーション  | Alembic                  |
| バリデーション   | Pydantic                 |
| 認証        | JWT、Argon2               |
| キャッシュ     | Redis 7                  |
| テスト       | pytest                   |
| パッケージ管理   | uv                       |
| コンテナ      | Docker、Docker Compose    |
| CI/CD     | GitHub Actions           |
| クラウド      | AWS                      |
| コンテナレジストリ | Amazon ECR               |
| コンピューティング | Amazon EC2               |
| リモートデプロイ  | AWS Systems Manager（SSM） |

[⬆ ページ上部へ](#inventory-management-api)

## アーキテクチャ

アプリケーションは、役割ごとに分離したレイヤードアーキテクチャを採用しています。

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
  │
  ├──────────────► PostgreSQL
  │
  └──────────────► Redis
```

各レイヤーの主な役割は以下のとおりです。

* **API層**：HTTPリクエスト、レスポンス、依存性注入を処理
* **Service層**：ビジネスロジックを処理
* **Repository層**：データベース操作を担当
* **Model層**：SQLAlchemyによるデータベースモデルを定義
* **Schema層**：Pydanticによるリクエスト・レスポンスモデルを定義
* **Core層**：設定、セキュリティ、ロールなどを管理
* **Cache層**：Redisを利用したキャッシュ処理を担当
* **Task層**：バックグラウンド処理を担当

この構成により、HTTP処理とデータベース処理からビジネスロジックを分離しています。

[⬆ ページ上部へ](#inventory-management-api)

## プロジェクト構成

```text
inventory-management/
├── app/
│   ├── api/
│   ├── cache/
│   ├── core/
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
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── Dockerfile
├── compose.yml
├── alembic.ini
├── pyproject.toml
└── uv.lock
```

本番環境専用の設定ファイルや秘密情報を含むファイルは、リポジトリには含めていません。

[⬆ ページ上部へ](#inventory-management-api)

## 認証・認可

認証にはJSON Web Token（JWT）を使用しています。

ユーザーのパスワードは、データベースに保存する前に **Argon2** を使用して安全にハッシュ化しています。

また、ロールベースアクセス制御（RBAC）を実装し、ユーザーのロールに応じてAPI操作へのアクセスを制御しています。

主なセキュリティ機能：

* パスワードのハッシュ化
* パスワードの検証
* JWTアクセストークンの発行
* JWTトークンの検証
* 認証用Dependency
* ロールベースの認可

[⬆ ページ上部へ](#inventory-management-api)

## 在庫管理

商品には在庫数量を持たせ、APIを通して数量の登録・更新を行えるようにしています。

また、アプリケーション側のバリデーションだけではなく、PostgreSQL側でも在庫数量が負数にならないよう制約を設定しています。

```text
quantity >= 0
```

データベーススキーマはAlembicによってバージョン管理され、マイグレーションとして適用されます。

[⬆ ページ上部へ](#inventory-management-api)

## キャッシュ・バックグラウンドタスク

商品関連の処理にはRedisをキャッシュ層として使用しています。

また、HTTPレスポンスを不必要に遅延させない処理については、バックグラウンドタスクを利用して非同期的に処理できる構成にしています。

これにより、主要なリレーショナルデータベース以外のインフラストラクチャも利用したバックエンドシステムを構築しています。

[⬆ ページ上部へ](#inventory-management-api)

## データベース・マイグレーション

データベースには以下を使用しています。

* **PostgreSQL 16**：永続データの保存
* **SQLAlchemy 2**：ORM・データベースアクセス
* **Alembic**：スキーママイグレーション

マイグレーションはバージョン管理され、アップグレード・ダウングレードの両方に対応しています。

主なマイグレーション内容：

* 初期テーブル作成
* 商品価格の追加
* ユーザーパスワードハッシュの追加
* ユーザーロールの追加
* 商品在庫数量の追加
* 商品在庫数量の制約追加

本番デプロイ時には、以下のコマンドで未適用のマイグレーションを自動的に適用します。

```bash
uv run alembic upgrade head
```

その後、アプリケーションのヘルスチェックを行います。

[⬆ ページ上部へ](#inventory-management-api)

## テスト

自動テストには **pytest** を使用しています。

以下の複数のレイヤーをテストしています。

* APIエンドポイント
* Service
* Repository
* Schema
* 認証
* セキュリティ
* バックグラウンドタスク

CI環境ではPostgreSQLとRedisのサービスを起動した状態でテストを実行します。

Pull Requestおよび`main`へのPushをトリガーとして自動テストが実行されます。

[⬆ ページ上部へ](#inventory-management-api)

## Docker

Docker Composeを使用して、以下のサービスを起動できます。

* FastAPIアプリケーション
* PostgreSQL
* Redis

APIコンテナにはヘルスチェックを設定しており、アプリケーションの稼働状態だけでなく、データベースへの接続も確認します。

本番環境では、Amazon ECRからアプリケーションイメージを取得する専用のCompose設定を使用しています。

[⬆ ページ上部へ](#inventory-management-api)

## CI/CD

GitHub Actionsを使用して、自動テストとデプロイを行っています。

パイプラインは以下の流れで実行されます。

```text
Push / Pull Request
        │
        ▼
依存関係のインストール
        │
        ▼
テスト実行
        │
        ▼
Dockerイメージのビルド
        │
        ▼
       main
        │
        ▼
Amazon ECRへイメージをPush
        │
        ▼
AWS SSM経由でEC2へデプロイ
        │
        ▼
Alembicマイグレーション
        │
        ▼
APIヘルスチェック
```

Pull RequestではテストとDockerイメージのビルドまで実行します。

`main`へのPushでは、これらに加えて本番環境へのデプロイを実行します。

DockerイメージにはGitのコミットSHAをタグとして使用しているため、ソースコードとデプロイされたイメージを対応付けることができます。

[⬆ ページ上部へ](#inventory-management-api)

## AWSデプロイ

AWSでは以下のサービスを使用しています。

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

EC2へのリモート操作にはAWS Systems Manager（SSM）を使用しています。

デプロイの流れ：

1. Dockerイメージをビルド
2. Amazon ECRへイメージをPush
3. SSM経由でEC2へ接続
4. 新しいイメージを取得
5. コンテナを起動
6. Alembicマイグレーションを適用
7. アプリケーションのヘルスチェックを実行

[⬆ ページ上部へ](#inventory-management-api)

## APIドキュメント

アプリケーション起動時、FastAPIがインタラクティブなAPIドキュメントを自動生成します。

### Swagger UI

```text
http://localhost:8000/docs
```

### ReDoc

```text
http://localhost:8000/redoc
```

ヘルスチェック用エンドポイント：

```text
GET /health
```

レスポンス例：

```json
{
  "status": "ok"
}
```

[⬆ ページ上部へ](#inventory-management-api)

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

サンプルファイルをコピーします。

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

### 5. データベースマイグレーションを適用

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

[⬆ ページ上部へ](#inventory-management-api)

## 環境変数

`env.example`を参考に`.env`を作成してください。

```env
DATABASE_URL=postgresql+psycopg://inventory:inventory@db:5432/inventory
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://redis:6379/0
```

実際の認証情報や秘密鍵を含む`.env`ファイルは、リポジトリにコミットしないでください。

[⬆ ページ上部へ](#inventory-management-api)

## 今後の改善

今後の改善候補：

* より包括的なIntegration Testの追加
* 在庫管理機能の拡張
* モニタリング・Observabilityの強化
* より細かな認可ポリシー
* アプリケーションと分離した本番用データベース
* デプロイ時の安全対策の追加

[⬆ ページ上部へ](#inventory-management-api)

---

<a name="english"></a>

**Language:** [English](#english) | [日本語](#日本語)
