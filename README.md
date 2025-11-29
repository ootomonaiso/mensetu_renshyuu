# 圧勝面接練習システム

高校生向けの面接練習支援システム。AI分析により面接のフィードバックを自動生成し、教師が最終的な指導を行う。

## 特徴

- 🎤 **音声分析**: faster-whisper + librosa で文字起こしと音響特徴分析
- 🤖 **AI評価**: Gemini API でキーワード抽出、敬語チェック、感情分析
- 📝 **Markdownレポート**: 教師がコメントを追加できる形式で出力
- 🔒 **プライバシー重視**: 音声/動画ファイルは保存せず、分析結果のみ保持
- 🏫 **ローカル完結**: 学校ネットワーク内で完結（Gemini API以外の外部通信なし）

## 技術スタック

### Backend
- **FastAPI** (Python 3.11+)
- **Supabase** (PostgreSQL + Auth + Storage)
- **Celery + Redis** (非同期処理)
- **faster-whisper** (音声文字起こし)
- **librosa** (音響特徴抽出)
- **Gemini API** (自然言語処理)
- **WeasyPrint** (PDF生成)

### Frontend
- **React 18** + **TypeScript**
- **Vite**
- **Zustand** (状態管理)
- **shadcn/ui** + **Tailwind CSS**
- **React Router**

## 開発環境セットアップ

### 前提条件
- Python 3.11+
- Node.js 18+
- pnpm
- Supabase アカウント

### 1. リポジトリクローン

\`\`\`bash
git clone https://github.com/ootomonaiso/mensetu_renshyuu.git
cd mensetu_renshyuu
\`\`\`

### 2. バックエンドセットアップ

\`\`\`bash
# 仮想環境作成
python -m venv .venv

# 仮想環境有効化 (Windows)
.\.venv\Scripts\Activate.ps1

# 依存関係インストール
pip install -e backend

# 環境変数設定
cp backend/.env.example backend/.env
# backend/.env を編集してSupabase認証情報を設定
\`\`\`

### 3. Supabaseデータベース初期化

1. [Supabase Dashboard](https://supabase.com/dashboard) にログイン
2. SQL Editor を開く
3. `backend/init_supabase.sql` の内容を実行

### 4. フロントエンドセットアップ

\`\`\`bash
cd frontend
pnpm install

# 環境変数設定
cp .env.example .env.local
# .env.local を編集してSupabase URL/Keyを設定
\`\`\`

## 起動方法

### バックエンド起動

\`\`\`bash
# ルートディレクトリで
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
\`\`\`

起動後、以下のURLでアクセス可能:
- API: http://127.0.0.1:8000
- ドキュメント: http://127.0.0.1:8000/docs

### フロントエンド起動

\`\`\`bash
cd frontend
pnpm run dev
\`\`\`

起動後、http://localhost:5173 でアクセス可能

### Celeryワーカー起動 (任意)

非同期処理を使う場合:

\`\`\`bash
# Redis起動が必要 (Docker or WSL)
docker run -d -p 6379:6379 redis:latest

# Celeryワーカー起動
.\.venv\Scripts\python.exe -m celery -A backend.app.celery_app worker --loglevel=info
\`\`\`

## テスト

### バックエンドテスト

\`\`\`bash
cd backend
pytest -v
\`\`\`

### フロントエンドビルド

\`\`\`bash
cd frontend
pnpm run build
\`\`\`

## 実装状況

### Phase 1 (MVP) - 進行中

#### 完了
- ✅ FastAPI バックエンド基盤
- ✅ Supabase Auth 連携
- ✅ ユーザープロフィール管理 (Profiles API)
- ✅ セッション管理 (Sessions CRUD)
- ✅ Celery + Redis 非同期処理基盤
- ✅ Markdown ログ生成機能
- ✅ React フロントエンド
  - ログイン/認証
  - ダッシュボード
  - セッション一覧/詳細/作成
- ✅ API クライアント共通化

#### 進行中
- 🔄 音声分析 (faster-whisper / librosa)
- 🔄 Gemini API 連携
- 🔄 レポートPDF生成

#### 未着手
- ⏳ ビデオ分析 (Phase 4)
- ⏳ E2Eテスト

## プロジェクト構造

\`\`\`
mensetu_renshyuu/
├── backend/                    # FastAPI バックエンド
│   ├── app/
│   │   ├── api/routes/        # APIエンドポイント
│   │   ├── services/          # ビジネスロジック
│   │   ├── tasks/             # Celeryタスク
│   │   ├── clients/           # 外部API連携
│   │   └── schemas/           # Pydanticスキーマ
│   ├── tests/                 # テスト
│   ├── init_supabase.sql      # DB初期化SQL
│   └── pyproject.toml
├── frontend/                   # React フロントエンド
│   ├── src/
│   │   ├── api/               # APIクライアント
│   │   ├── pages/             # ページコンポーネント
│   │   ├── stores/            # Zustand状態管理
│   │   └── lib/               # ユーティリティ
│   └── package.json
├── .github/                    # 設計ドキュメント
│   ├── DESIGN.md              # 総合設計書
│   ├── api-design.md          # API設計
│   ├── database-design.md     # DB設計
│   └── ai-implementation.md   # AI実装詳細
└── docs/                       # 追加ドキュメント
\`\`\`

## 関連ドキュメント

- [総合設計書](.github/DESIGN.md)
- [API設計](.github/api-design.md)
- [データベース設計](.github/database-design.md)
- [AI実装詳細](.github/ai-implementation.md)
- [開発計画](plan.md)

## ライセンス

MIT License

## 貢献

Pull Request歓迎！詳細は [CONTRIBUTING.md](CONTRIBUTING.md) を参照。
