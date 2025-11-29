# 開発計画 (Phase 1: MVP)

## 1. 現状整理
- **Backend**: FastAPI 基盤 + `/auth` + `/profiles` まで実装済み。Sessions/Analysis 系は未着手。
- **Frontend**: 認証＋ダッシュボードの骨組みあり。プロフィール情報/セッション一覧などは未実装。
- **Supabase**: `.github/database-design.md` に記載の 11 テーブル + RLS はまだ未作成。将来的にも音声/画像などの大容量ファイルは扱わず、メタデータのみ保存する方針。
- **分析系**: 音声/画像ファイルは受け取らず、処理結果を Markdown ログとして生成・保存する動線が未実装。

## 2. 実装タスク一覧
| 優先 | タスク | 内容 | 参照ドキュメント |
| ---- | ------ | ---- | --------------- |
| P0 | Supabase DB/Storage 準備 | `user_profiles` から `ai_analysis_cache` まで 11 テーブルの作成、RLS/ポリシー適用。Storage は Markdown ログ保存用 (`reports` など) のみに利用 | `.github/database-design.md` |
| P0 | Backend 認証/共通 | Supabase Auth JWT 検証ミドルウェア、`get_current_user` 依存関数、例外ハンドラ | `.github/api-design.md` |
| P1 | Profiles API | `/profiles/me` GET/PUT、`/students/{id}` GET (教師のみ) | `.github/api-design.md` |
| P1 | Sessions API | CRUD + 「セッション処理ログ作成」エンドポイント。アップロードは受け付けず、処理メタ情報をトリガーにジョブ投入 | `.github/api-design.md`, `.github/database-design.md` |
| P1 | 分析タスク基盤 | Celery + Redis、faster-whisper / librosa などで処理を実施（必要なら入力はダウンロード URL を参照）。全ステップを Markdown タイムラインとして出力 | `.github/DESIGN.md` §4.1, `.github/ai-implementation.md` |
| P2 | AI 連携 | Gemini API (keywords/keigo/sentiment) 呼び出し、結果も Markdown ログへ結合。`ai_analysis_cache` でキャッシュ | `.github/ai-implementation.md` |
| P2 | レポート生成 | Markdown + WeasyPrint PDF。音声/画像を含めず、生成したログ＋メトリクスを `reports/{student}/{session}` に保存 | `.github/DESIGN.md` 6A.1 |
| P2 | Frontend 主要画面 | プロフィール編集、セッション一覧/詳細、アップロード UI、分析結果/レポート閲覧 | `.github/DESIGN.md`, `.github/api-design.md` |
| P3 | テスト/CI | pytest で API テスト、Vitest/Playwright は後続 | `.github/DESIGN.md` §8 |

## 3. 依存と必要な準備
1. **Supabase SQL 実行権限**: SQL Editor または `supabase db push` が使える状態が必要です。こちらで SQL を流す環境が無い場合、ユーザー側で実行お願いします。
2. **Redis/Celery**: ローカルまたは学校ネットワーク内で Redis を起動できる環境情報 (ホスト/ポート)。未整備なら後で案内します。
3. **Gemini API Key**: `.env` の `GEMINI_API_KEY` に実際のキーを設定してください (未設定なら仮値のまま)。
4. **Supabase Storage**: Markdown ログとレポート出力を保存する private バケット (`reports`) のみ必要。音声ファイル用バケットは不要。
5. **処理メタ情報サンプル** (任意): 文字起こしの結果や話速など、Markdown に載せたい項目の例があると出力レイアウトを合わせやすいです。

## 4. 次のアクション
1. Supabase にテーブル/ポリシーを適用 (ユーザー側で SQL 実行が必要なら SQL を共有します)。
2. Backend に認可ミドルウェア + Profiles API を実装。
3. Sessions API と Storage アップロードを追加し、フロントから操作できるようにする。
4. Celery ワーカー + 音声分析 (faster-whisper, librosa) を組み込み、セッション完了時にジョブ投入し、Markdown ログを生成。
5. Gemini 連携・評価スコア計算・レポート生成を順次追加（ログへの追記 + PDF 変換）。

ご要望や優先順位変更があれば教えてください。また、上記「必要な準備」で不足している項目があれば共有いただけると助かります。