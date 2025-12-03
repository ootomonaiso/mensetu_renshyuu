# 圧勝面接練習システム (簡易版 MVP)

音声ファイルをアップロードして、AI 分析結果を Markdown レポートで出力するシンプルな面接練習支援ツール。

## 特徴

- 🎤 **音声分析**: faster-whisper で文字起こし + librosa で音響分析
- 🧠 **音声感情分析**: 声の震え・トーン変動から緊張度・自信度を検出
- 🤖 **AI 評価**: Gemini API でキーワード抽出、敬語チェック、感情分析
- 📝 **Markdown レポート**: 教師がコメントを追加できる形式で出力
- 🔒 **ローカル完結**: DB/認証不要、音声ファイルと分析結果のみ保存
- 🚀 **シンプル構成**: FastAPI のみ、数分でセットアップ完了
- 📹 **ビデオ分析 (Phase 4)**: カメラ映像から表情・視線・姿勢を分析 (将来実装)

## 技術スタック

- **FastAPI** (Python 3.11+) - Web API
- **faster-whisper** - 音声文字起こし
- **librosa** - 音響特徴抽出
- **Gemini API** - AI 分析 (キーワード/敬語/感情)
- **Jinja2** - Markdown レポート生成

## セットアップ (5 分)

### 1. リポジトリクローン

```bash
git clone https://github.com/ootomonaiso/mensetu_renshyuu.git
cd mensetu_renshyuu
```

### 2. 依存パッケージインストール

```bash
# 仮想環境作成 (Windows)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 仮想環境作成 (Mac/Linux)
python -m venv .venv
source .venv/bin/activate

# パッケージインストール
pip install fastapi uvicorn python-multipart python-dotenv jinja2 faster-whisper librosa google-generativeai soundfile
```

### 3. 環境変数設定

```bash
# プロジェクトルートに .env ファイル作成 (Windows PowerShell)
echo "GEMINI_API_KEY=your_api_key_here" > .env

# Mac/Linux
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

Gemini API Key は [Google AI Studio](https://aistudio.google.com/app/apikey) で取得してください (無料枠あり)。

### 4. ディレクトリ作成

```bash
# Windows PowerShell
New-Item -ItemType Directory -Force -Path backend\services, backend\templates, output\audio, output\reports

# Mac/Linux
mkdir -p backend/services backend/templates output/audio output/reports
```

## 使い方

### 1. サーバー起動

```bash
# backend/main.py を実装後
uvicorn backend.main:app --reload
```

起動後、http://127.0.0.1:8000/docs で API ドキュメントが閲覧できます。

### 2. 音声ファイルアップロード

ブラウザで http://127.0.0.1:8000 にアクセスし、音声ファイル (mp3/wav/m4a) をアップロード。

### 3. リアルタイム面接練習

http://127.0.0.1:8000/static/realtime.html でリアルタイム録音・分析が可能。

### 4. レポート確認

`output/reports/` ディレクトリに Markdown レポートが生成されます。
フロントエンド (http://localhost:5173) でダウンロード可能。

## 実装状況

### Phase 1 (簡易版 MVP) - ✅ 実装完了

- ✅ FastAPI サーバー (`backend/main.py`)
- ✅ 音声アップロード API (`POST /api/analyze`)
- ✅ faster-whisper 文字起こし
- ✅ librosa 音響分析 (話速、音量、ポーズ)
- ✅ **音声感情分析 (声の震え・緊張度検出)**
- ✅ Gemini API 連携 (キーワード・敬語・感情)
- ✅ Markdown レポート生成 (教師コメント欄付き)
- ✅ 簡易 Web UI (HTML フォーム)

### Phase 2 (リアルタイム機能) - ✅ 実装完了

- ✅ WebSocket によるリアルタイム音声ストリーミング
- ✅ リアルタイム文字起こし表示
- ✅ リアルタイム音響・感情分析
- ✅ セッション録音・録画機能
- ✅ ポストセッション分析パイプライン

### Phase 3 (ビデオ分析基盤) - ✅ 実装完了

- ✅ ビデオ録画・保存機能
- ✅ OpenCV + MediaPipe 基盤実装
- ✅ 骨格検出・視線分析の基礎

### Phase 4 (高度なビデオ分析) - ✅ 実装完了 🎥

- ✅ **表情分析**: 笑顔・緊張・困惑の検出 (MediaPipe Face Mesh)
- ✅ **視線追跡**: アイコンタクトの頻度・方向 (MediaPipe Face Detection)
- ✅ **姿勢分析**: 猫背・前傾・手の動き (MediaPipe Pose)
- ✅ **ジェスチャー検出**: 髪を触る・手を組むなどの癖 (MediaPipe Hands)
- ✅ **統合レポート**: 音声+映像+感情の総合評価

### 追加機能 - ✅ 実装完了

- ✅ **レポートダウンロード機能**: ダウンロード後自動削除
- ✅ **レポート管理 API**: 一覧取得・削除
- ✅ **React フロントエンド**: レポート一覧・ダウンロード UI

## プロジェクト構造

```
mensetu_renshyuu/
├── backend/
│   ├── main.py              # ✅ FastAPI サーバー (881 lines)
│   ├── services/
│   │   ├── transcription.py        # ✅ faster-whisper
│   │   ├── audio_analysis.py       # ✅ librosa
│   │   ├── voice_emotion.py        # ✅ 音声感情分析
│   │   ├── ai_analysis.py          # ✅ Gemini API
│   │   ├── report.py               # ✅ Markdown 生成
│   │   ├── video_analysis.py       # ✅ MediaPipe 分析 (Phase 4)
│   │   ├── video_processors.py     # ✅ 動画処理
│   │   ├── realtime_transcription.py # ✅ リアルタイム文字起こし
│   │   ├── realtime_analyzer.py    # ✅ リアルタイム分析
│   │   ├── session_recorder.py     # ✅ セッション記録
│   │   └── post_session_pipeline.py # ✅ セッション後分析
│   ├── static/
│   │   └── realtime.html    # ✅ リアルタイム面接 UI
│   └── templates/
│       └── report.md.j2     # ✅ レポートテンプレート
├── frontend/                # ✅ React + TypeScript + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── audio-recorder-card.tsx    # ✅ 音声録音
│   │   │   ├── video-recorder-card.tsx    # ✅ 動画録画
│   │   │   ├── live-analysis-card.tsx     # ✅ リアルタイム分析表示
│   │   │   └── report-list.tsx            # ✅ レポート一覧・ダウンロード
│   │   └── lib/
│   │       └── api.ts       # ✅ API クライアント
├── output/
│   ├── audio/               # 音声ファイル保存先
│   ├── reports/             # ✅ 生成された Markdown レポート
│   ├── videos/              # 動画ファイル保存先
│   └── sessions/            # ✅ セッションデータ
├── .env                     # API キー
├── requirements.txt         # ✅ 依存パッケージ (MediaPipe 追加)
└── README.md
```

## 技術詳細

### faster-whisper
- OpenAI Whisper の高速版 (CTranslate2)
- CPU でも動作、GPU があれば 10 倍高速
- 日本語の認識精度が高い

### librosa
- 音響特徴抽出ライブラリ
- 話速、音量、ポーズ検出などに使用
- NumPy/SciPy ベース

### Gemini API
- Google の大規模言語モデル
- 無料枠: 1,500 リクエスト/日
- キーワード抽出、敬語判定、感情分析に使用

## 次のステップ

`plan.md` を参照し、以下の順で実装を進めます:

1. FastAPI 最小サーバー作成
2. 音声アップロード API 実装
3. faster-whisper 連携
4. librosa 音響分析追加
5. Gemini API 連携
6. Markdown レポート生成
7. 簡易 Web UI 追加

## ライセンス

MIT License

## 関連ドキュメント

- [要件定義書](./requirements.md)
- [開発計画](./plan.md)
- [技術スタック詳細](./docs/tech-stack.md)

