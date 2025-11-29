# 技術スタック詳細

**作成日**: 2025年11月29日  
**プロジェクト名**: 圧勝面接

---

## システム構成 (推奨環境)

```
[Webブラウザ]
    ↓ HTTPS
[FastAPI サーバー] ←→ [Supabase]
    ↓                   - PostgreSQL
[Celery Worker]         - Auth
    ↓                   - Storage
[音声処理エンジン]
 - Whisper
 - librosa
 - Gemini API
```

---

## ハードウェア要件

### 開発・小規模校 (推奨)
- **PC**: Windows 10/11 or Mac
- **CPU**: Intel i5 / AMD Ryzen 5 (4コア)
- **RAM**: 8GB
- **ストレージ**: SSD 20GB
- **GPU**: 不要 (あれば高速化)

### 本番環境 (中規模校)
- **サーバー**: Linux (Ubuntu 22.04 LTS) 推奨
- **CPU**: 4コア以上
- **RAM**: 16GB
- **ストレージ**: SSD 50GB
- **GPU**: NVIDIA (CUDA対応) 推奨 (10倍高速化)

---

## バックエンド

### 言語・フレームワーク

#### Python 3.11+
- **選定理由**: 豊富なAI/MLライブラリ、開発速度
- 型ヒントによる保守性向上

#### FastAPI 0.104+
- **選定理由**:
  - 非同期処理対応 (リアルタイム音声処理に必須)
  - WebSocket標準サポート
  - 自動APIドキュメント生成 (Swagger UI)
  - Pydanticによるバリデーション
- **代替案を却下**: Flask (非同期サポートが弱い), Django (過剰機能)

### データベース・バックエンドサービス

#### Supabase
- **PostgreSQL 15+**: マネージドデータベース
  - **選定理由**:
    - インフラ管理不要 (バックアップ、スケーリング自動)
    - 無料枠: 500MB DB + 1GB Storage (小規模校十分)
    - リアルタイム機能 (WebSocket代替可能)
    - Row Level Security (RLS) でセキュリティ強化
    - REST API自動生成

- **Supabase Auth**: 認証・認可
  - JWT自動管理
  - パスワードハッシュ、メール認証
  - 教師・生徒のロールベースアクセス制御

- **Supabase Storage**: ファイルストレージ
  - 音声ファイル保存 (session_id/audio.wav)
  - PDFレポート保存 (session_id/report.pdf)
  - 自動バックアップ
  - CDN配信

#### ORM
- **SQLAlchemy 2.0+** (オプション)
  - Supabase REST APIを直接使用も可能
  - 複雑なクエリ時はORMを併用
  - マイグレーション: Supabase CLI / Alembic

### キャッシュ・タスクキュー

#### Redis 7.0+
- **用途**:
  - セッション管理
  - 音声処理結果の一時キャッシュ
  - Celeryのメッセージブローカー
- **代替案**: なし (標準的選択)

#### Celery 5.3+
- **用途**:
  - 重い音声処理の非同期実行
  - レポートPDF生成
  - バッチ処理 (定期集計など)
- **代替案を却下**: RQ (機能不足), Dramatiq (エコシステムが小さい)

---

## フロントエンド

### フレームワーク・言語

#### React 18.2+
- **選定理由**:
  - コンポーネント再利用性
  - 豊富なライブラリエコシステム
  - 大規模開発の実績
- **代替案を却下**: Vue.js (採用実績重視), Angular (学習コスト高)

#### TypeScript 5.0+
- **選定理由**: 型安全性、保守性向上、IDE支援

### UI・スタイリング

#### shadcn/ui + Tailwind CSS 3.3+
- **選定理由**:
  - モダンなデザイン
  - カスタマイズ容易
  - コピペで使えるコンポーネント集
  - バンドルサイズが小さい
- **代替案を却下**: Material-UI (バンドルサイズ大), Ant Design (デザイン固定的)

### 状態管理

#### Zustand 4.4+
- **選定理由**: シンプル、軽量、学習コスト低
- **用途**: グローバル状態 (ユーザー情報、セッション状態)
- **代替案を却下**: Redux (冗長), Recoil (複雑)

### ビルド・開発ツール

#### Vite 5.0+
- **選定理由**: 高速HMR、モダン、設定シンプル
- **代替案を却下**: Webpack (遅い), Parcel (エコシステム小)

#### React Router 6.x
- SPA ルーティング

---

## 音声処理

### 音声認識

#### faster-whisper (OpenAI Whisper最適化版)
- **モデルサイズ**: `small` (デフォルト)
  - base: 速度優先 (精度約90%)
  - small: バランス (精度約95%) ← 推奨
  - medium: 精度優先 (精度約97%、遅い)
- **GPU対応**: CUDA 11.8+ (オプション、10倍高速化)
- **代替案を却下**: Google Speech-to-Text (クラウド依存), Julius (精度不足)

### 音響分析

#### librosa 0.10+
- **用途**: 音声特徴量抽出 (MFCC, ピッチ, エネルギー)
- 話速、声の大きさ、イントネーション分析

#### pydub 0.25+
- **用途**: 音声ファイル操作 (変換、分割、結合)

#### numpy 1.24+, scipy 1.11+
- 数値計算基盤

### 自然言語処理

#### sudachipy 0.6+ (形態素解析)
- **辞書**: SudachiDict-full
- **選定理由**:
  - GiNZAより軽量・高速
  - 敬語判定に必要な詳細品詞情報
  - 複合語分割が優秀
- **代替案を却下**: MeCab (敬語情報不足), GiNZA (重い)

#### カスタム敬語判定エンジン
- **実装方針**:
  - ルールベース: 品詞パターンマッチング
  - 辞書: 敬語表現データベース
  - Phase 3: 機械学習モデル追加検討

---

## レポート生成

### PDF生成

#### ReportLab 4.0+
- **用途**: 教師向け詳細レポート
- **代替案**: WeasyPrint (HTML→PDF、柔軟性高い)

### グラフ生成

#### Matplotlib 3.7+ / Plotly 5.x
- グラフ生成 (スコア推移、レーダーチャート)

---

## AI/ML (Phase 3以降)

### 基本方針: API費用をかけずローカル実装

#### フィードバック生成エンジン (ルールベース)
- **実装方針**:
  - テンプレートベースの文章生成
  - 評価項目ごとのスコアでフィードバック内容を分岐
  - 具体的な改善例をデータベースから提示

#### 質問生成エンジン
- **実装方針**:
  - 生徒プロフィールからキーワード抽出
  - 質問テンプレートとキーワードを組み合わせ
  - 志望先業界別の頻出質問データベース
  
- **例**:
  ```python
  # 部活: バスケットボール部 + 職種: 営業
  questions = [
      f"{student.club}での経験を、営業職でどう活かせますか？",
      f"チームで目標を達成した経験を教えてください。"
  ]
  ```

#### 感情分析 (軽量モデル)
- **音声からの感情推定**:
  - librosaで音響特徴量抽出
  - ルールベース: ピッチ・エネルギー・話速から推定
  - オプション: 軽量モデル (SVM/Random Forest)
  
- **テキストからの感情推定**:
  - 感情辞書ベース (日本語感情極性辞書など)
  - フィラーワード・否定表現の検出

#### ローカルLLM (完全オプション)
- **使用しない前提で設計**
- **どうしても必要な場合のみ**:
  - Ollama + llama3.1 8B (無料)
  - 用途: 複雑なフィードバック文の洗練のみ
  - 要件: 16GB RAM, GPU推奨
  - **注意**: 基本機能はLLMなしで完結

#### クラウドLLM (API)
- **使用しない**
  - 理由: コストがかかる
  - OpenAI API, Claude API等は使わない
  - 代わりにルールベースで実装

---

## 開発環境・ツール

### パッケージ管理
- **Python**: Poetry 1.7+ または uv 0.1+ (高速)
- **Node.js**: pnpm 8.x (高速、ディスク効率的)

### コード品質

#### Python
- **Linter/Formatter**: Ruff (高速、Flake8/Black/isort統合)
- **型チェック**: mypy --strict
- **セキュリティ**: bandit

#### TypeScript
- **Linter**: ESLint + typescript-eslint
- **Formatter**: Prettier
- **型チェック**: tsc --noEmit

### テスト

#### Backend
- pytest 7.x + pytest-asyncio
- coverage.py (カバレッジ80%目標)
- httpx (FastAPI テストクライアント)

#### Frontend
- Vitest (高速、Vite統合)
- React Testing Library
- MSW (API モック)

#### E2E (Phase 2以降)
- Playwright (クロスブラウザ対応)

### CI/CD
- **GitHub Actions** (推奨)
  - 自動テスト実行
  - コード品質チェック
  - Docker イメージビルド

---

## デプロイ・インフラ

### コンテナ化
- **Docker 24.x + Docker Compose**
  - サービス構成:
    - `api`: FastAPI アプリケーション
    - `redis`: Redis
    - `worker`: Celery ワーカー
    - `nginx`: リバースプロキシ・静的ファイル配信

### 推奨構成 (本番環境)
```yaml
# docker-compose.yml イメージ
services:
  api:
    image: mensetu-api:latest
    environment:
      - SUPABASE_URL=https://xxx.supabase.co
      - SUPABASE_KEY=your-anon-key
      - SUPABASE_SERVICE_KEY=your-service-key
      - REDIS_URL=redis://redis:6379
  
  worker:
    image: mensetu-api:latest
    command: celery -A app.worker worker
    environment:
      - SUPABASE_URL=https://xxx.supabase.co
      - SUPABASE_SERVICE_KEY=your-service-key
  
  redis:
    image: redis:7-alpine
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"

# Supabaseはクラウドでホスティング (db不要)
```

### 最小構成 (開発・小規模)
- Windows/Mac で直接実行
- Supabase無料プラン
- 起動コマンド:
  ```bash
  # .env ファイル設定
  SUPABASE_URL=https://xxx.supabase.co
  SUPABASE_KEY=your-anon-key
  
  # Backend
  poetry run uvicorn app.main:app --reload
  
  # Frontend
  pnpm dev
  ```

---

## セキュリティ

- **認証**: Supabase Auth (JWT自動管理)
  - access token + refresh token
  - セッション管理自動化
- **パスワード**: Supabase Authで自動ハッシュ (bcrypt)
- **アクセス制御**: Row Level Security (RLS)
  - 生徒は自分のデータのみ閲覧可能
  - 教師は担当生徒のデータ閲覧可能
  - 管理者は全データアクセス可能
- **通信**: HTTPS/WSS (Supabase標準対応)
- **データ暗号化**: 
  - DB: Supabase標準 (保管時暗号化)
  - Storage: 自動暗号化
  - 転送時: TLS 1.3
- **CORS**: オリジン制限 (Supabase設定)
- **Rate Limiting**: 
  - Supabase標準 (無料: 60 req/min)
  - FastAPI側でも追加制限 (slowapi)

---

### スケーラビリティ
- **小規模校 (同時5-10人)**: Supabase無料プラン + 音声処理PC 1台
- **中規模校 (同時20-50人)**: Supabase Proプラン + 専用サーバー
- **複数校展開**: Supabase Proプラン + 音声処理サーバー複数台

---

## 次のステップ

1. **Supabaseプロジェクト作成**
2. **データベーススキーマ設計**
3. **APIエンドポイント設計**
4. **バックエンドロジック設計**
   - 評価アルゴリズム
   - フィードバック生成ルール
   - 質問生成ロジック
5. **FastAPI + Supabase 連携検証**
6. **Whisper音声認識精度テスト**
7. **プロトタイプ開発開始**

---

## 重要な設計方針

### コスト効率的なAI活用
1. **音響分析は完全ローカル** (librosa)
   - 話速、声量、ピッチ → 数値でレポート表示
2. **キーワード抽出はGemini API** (無料枠)
   - 精度高く、コスト¥0
3. **敬語判定はPythonローカル** (sudachipy + ルール)
4. **感情分析はローカルライブラリ** (transformers軽量モデル)
5. **フィードバックはテンプレート** (Gemini補助はオプション)

### Pythonで使えるAIライブラリを活用
- **transformers**: 日本語BERT (感情分析)
- **scikit-learn**: 軽量ML (分類・回帰)
- **librosa**: 音響分析
- **pyAudioAnalysis**: 音声感情分析
- すべてCPUで動作、FastAPIサーバーに統合可能

### レポート設計
- **数値データを明確に表示**:
  - 話速: 180 wpm (推奨: 150-180)
  - 声量: 65 dB (推奨: 60-70)
  - フィラー: 12回 (前回: 18回)
- **グラフ・可視化**:
  - 時系列グラフ (話速の変化)
  - レーダーチャート (総合評価)
  - 過去との比較グラフ

### 品質を保つための工夫
1. **詳細なフィードバックテンプレート** (評価項目×スコア帯)
2. **具体例データベース** (良い例/改善例)
3. **質問バンクの充実** (業界別・パターン別)
4. **Gemini APIで柔軟性向上** (キーワード・要約)
5. **ルールの継続的改善** (フィードバックループ)
