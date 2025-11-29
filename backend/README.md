# 圧勝面接 Backend

FastAPI + Supabase ベースの API サーバーです。AI 面接支援システムのサーバーサイド処理（認証、面接セッション管理、音声/ビデオ解析ジョブの起動、Markdown/PDF レポート生成など）を担当します。

## 必要条件

- Python 3.11+
- Poetry 1.7+
- Supabase プロジェクト (Auth + Postgres + Storage)

## セットアップ

```bash
cd backend
poetry install
```

環境変数は `.env` に記述します。テンプレートは `.env.example` を参照してください。

```bash
cp .env.example .env
```

## 開発サーバー起動

```bash
poetry run uvicorn app.main:app --reload
```

API ドキュメント: `http://localhost:8000/docs`

### Celery ワーカー

Markdown ログ生成などの分析タスクは Celery で処理します。Redis を起動した上で、別ターミナルで以下を実行してください。

```bash
poetry run celery -A app.celery_app.celery_app worker --loglevel=info
```

ヘルスチェック用に `ping` タスクを公開しているので、`celery -A app.celery_app.celery_app call ping` で動作確認できます。

## テスト

```bash
poetry run pytest
```

## ディレクトリ構成

```
backend/
├── app/
│   ├── api/            # FastAPI ルーター
│   ├── clients/        # Supabase / Gemini などのクライアント
│   ├── core/           # 設定、ロギング、アプリ初期化
│   ├── models/         # Pydantic Schemas
│   ├── services/       # ビジネスロジック
│   └── main.py         # エントリーポイント
├── tests/
├── pyproject.toml
└── README.md
```

## ドキュメント参照

- `.github/DESIGN.md` — 全体設計
- `.github/api-design.md` — エンドポイント仕様
- `.github/database-design.md` — DB/RLS 設計
- `.github/ai-implementation.md` — Gemini / 分析ガイド
- `.github/copilot-instructions.md` — コーディングルール
