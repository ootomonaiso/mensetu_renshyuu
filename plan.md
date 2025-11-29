# 開発計画 (Phase 1: 簡易版 MVP)

## 1. 方針転換
- **DB/Auth 不要**: ログイン機能・Supabase は使わない
- **ローカル完結**: 音声ファイルをアップロード → 分析 → Markdown レポート出力
- **シンプル構成**: FastAPI + faster-whisper + librosa + Gemini API のみ

## 2. 実装タスク一覧
| 優先 | タスク | 内容 | 実装方針 |
| ---- | ------ | ---- | -------- |
| P0 | プロジェクト構造作成 | `backend/`, `output/reports/`, `output/audio/` ディレクトリ作成 | 手動 or スクリプト |
| P0 | 音声アップロード API | `/api/upload` POST: 音声ファイルを受け取り、`output/audio/` に保存 | FastAPI `UploadFile` |
| P1 | 文字起こし処理 | faster-whisper で音声→テキスト変換。タイムスタンプ付き | `WhisperModel.transcribe()` |
| P1 | 音響分析 | librosa で話速・音量・ポーズ検出 | `librosa.load()`, `librosa.effects.split()` |
| P2 | Gemini AI 分析 | キーワード抽出、敬語チェック、感情分析 | `google.generativeai` SDK |
| P2 | Markdown レポート生成 | テンプレート (Jinja2) でレポート生成、`output/reports/{timestamp}.md` に保存 | Jinja2 + ファイル書き込み |
| P3 | 簡易 Web UI | HTML フォームで音声アップロード、レポートダウンロードリンク表示 | FastAPI `HTMLResponse` + `<form>` |
| P3 | エラーハンドリング | ファイル形式チェック、API エラー時のフォールバック | try-except + ログ |

## 3. 必要な準備
1. **Python 環境**: Python 3.11+ + `pip` または `poetry`
2. **Gemini API Key**: Google AI Studio で取得し、`.env` に `GEMINI_API_KEY=xxx` を設定
3. **音声ファイル**: テスト用の音声ファイル (mp3/wav/m4a) を用意
4. **依存パッケージ**:
   ```
   fastapi
   uvicorn
   faster-whisper
   librosa
   google-generativeai
   jinja2
   python-multipart
   python-dotenv
   ```

## 4. 次のアクション
1. プロジェクト構造を作成 (`backend/`, `output/`, `.env`)
2. FastAPI の最小サーバーを立ち上げ (`main.py`)
3. 音声アップロード API を実装
4. faster-whisper で文字起こし処理を追加
5. librosa で音響分析を追加
6. Gemini API 連携 (キーワード/敬語/感情)
7. Markdown レポートテンプレートを作成
8. レポート生成処理を実装
9. 簡易 Web UI でアップロード→レポート表示

## 5. ディレクトリ構造 (予定)
```
mensetu_renshyuu/
├── backend/
│   ├── main.py              # FastAPI サーバー
│   ├── services/
│   │   ├── transcription.py # faster-whisper
│   │   ├── audio_analysis.py # librosa
│   │   ├── ai_analysis.py   # Gemini API
│   │   └── report.py        # Markdown 生成
│   └── templates/
│       └── report.md.j2     # レポートテンプレート
├── output/
│   ├── audio/               # アップロードした音声
│   └── reports/             # 生成した Markdown
├── .env                     # API キー
├── requirements.txt         # 依存パッケージ
└── README.md
```

シンプルな構成なので、数時間で動作する MVP を作れます!