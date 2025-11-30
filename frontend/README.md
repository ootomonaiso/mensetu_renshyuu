# 面接支援フロントエンド (React + Vite)

FastAPI バックエンドと連携し、音声・映像の録画および Markdown レポート閲覧を行うためのフロントエンドです。Tailwind CSS + shadcn/ui 互換コンポーネント、React Query、Zustand をベースにしています。

## 必要要件

- Node.js 20+
- npm 10+

## セットアップ

```powershell
cd frontend
npm install
npm run dev
```

ブラウザで `http://localhost:5173` を開き、`VITE_API_BASE` が未設定の場合は同じオリジン (例: `http://localhost:8000`) の FastAPI API を呼び出します。別ポートの API を叩く場合は `.env` ファイルに `VITE_API_BASE` を指定してください。

```powershell
# frontend/.env
VITE_API_BASE=http://localhost:8000
```

## 主な機能

- **音声録音 + アップロード**: MediaRecorder API で録音し、`/api/analyze` へ送信して AI 分析結果を表示
- **カメラ録画**: 映像と音声を同時に記録し、将来の動画分析 API に送信 (未実装時はローカル保存を案内)
- **レポート一覧**: `/api/reports` を React Query で取得し、Markdown レポートを即座に開ける
- **リアルタイム練習リンク**: 既存の `backend/static/realtime.html` への導線を提供

## スクリプト

| コマンド | 説明 |
| --- | --- |
| `npm run dev` | 開発サーバー起動 (Vite) |
| `npm run build` | 型チェック + 本番ビルド |
| `npm run preview` | ビルド成果物のプレビュー |
| `npm run lint` | ESLint チェック |

## フォルダ構成 (抜粋)

- `src/components` … UI/機能コンポーネント (録音カード、レポート一覧など)
- `src/hooks` … 共通カスタムフック (`useMediaRecorder`)
- `src/lib` … API クライアントやユーティリティ
- `src/providers` … React Query Provider などのアプリケーションコンテキスト

## 注意

- ブラウザのマイク/カメラ利用許可が必要です。
- 動画アップロード API (`/api/video/analyze`) は Phase 4 向けで、バックエンドが未実装の場合はローカル保存を促すメッセージを表示します。

詳細なアーキテクチャや設計方針はリポジトリ直下の `requirements.md` および `.github/copilot-instructions.md` を参照してください。
