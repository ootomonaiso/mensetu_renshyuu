# Copilot Instructions

> この文書は AI コーディング支援（GitHub Copilot Chat / CLI / PR Review など）向けの共通ルールです。  
> 人間の教師が最終判断を下す“サポート用ソフトウェア”であることを常に意識してください。

関連ドキュメント: `requirements.md`, `.github/DESIGN.md`, `.github/api-design.md`, `.github/database-design.md`, `.github/ai-implementation.md`, `docs/tech-stack-simple.md`

---

## 1. 開発全体方針

1. **サポート特化**: AIの出力は参考情報。教師が編集・承認できる形で成果物（コード/Markdown/PDF）を生成する。
2. **段階的実装**: Phase 1 (MVP) を最優先し、上位フェーズの仕様を先走らない。Phase 境界は `.github/DESIGN.md` の該当節を参照。
3. **ローカル完結志向**: 音声処理・データ保存は極力ローカル/学校ネットワーク内で完結。外部 API は Gemini のみ。
4. **コスト最小化**: Gemini API 呼び出しは `.github/ai-implementation.md` のキャッシュ戦略・レート制限を厳守する。
5. **日本語 UI / 出力**: 生徒・教師向けの文言は基本的に日本語。変数名・コメントは英語可。

---

## 2. アーキテクチャ要約

| 層 | 技術 | 備考 |
|----|------|------|
| フロント | React 18 + TypeScript + Vite + shadcn/ui + Tailwind | 状態管理は Zustand。UI 文言は日本語。 |
| API | FastAPI (Python 3.11+) | Supabase Auth JWT の検証を必須。|
| DB/Storage | Supabase (PostgreSQL + Auth + Storage) | RLS 有効。マイグレーションは `database-design.md` 順に。|
| 非同期 | Celery + Redis | 音声/動画/レポート生成は全てワーカーで処理。|
| AI | Gemini API (gemini-1.5-flash) | キーワード/敬語/感情/印象分析。キャッシュ必須。|
| 音声 | faster-whisper, librosa, pydub | 文字起こし・音響特徴抽出。|
| 動画 (Phase4~) | OpenCV + MediaPipe | 目線・姿勢・表情分析。|
| レポート | Markdown + WeasyPrint (PDF) + Jinja2 | `reports/{student}/{session}.md|pdf` で保存。|

---

## 3. コーディングルール

### 3.1 共通
- **Lint/Format**: Python → Ruff + black 互換 (PEP8)。TS/JS → ESLint + Prettier。
- **型安全**: Python は `pydantic` model または `typing` ヒント必須。TypeScript は `any` 禁止（やむを得ない場合は `TODO` 付き）。
- **ロギング**: print 禁止。`structlog` or `logging` を使用し、PII を直接出力しない。
- **コメント**: 日本語 UI 文言の意図や複雑ロジックのみ。冗長なコメントは避ける。
- **エラー処理**: Gemini/外部 I/O はリトライ + graceful fallback（詳細は `.github/ai-implementation.md`）。

### 3.2 Backend (FastAPI)
- ルーター: `app/api/v1/<feature>.py` に分割。依存関係は `Depends` で注入。
- スキーマ: `app/schemas` 内で `BaseModel` を利用。フロントとの契約は `.github/api-design.md` をソース・オブ・トゥルースとする。
- サービス層: ビジネスロジックは `app/services/` に切り出し、エンドポイントを薄く保つ。
- Supabase: 行ごとに `school_id` / `teacher_id` でフィルタ。RLS と整合するよう必ず `session.user.id` を参照。
- Celery タスク: 音声/動画/レポート生成は同期 API から切り離し、ジョブ ID を返す。

### 3.3 Frontend (React)
- 状態: グローバルは Zustand、局所は React hook。サーバー通信は React Query または独自 fetch wrapper。
- shadcn/ui: デザイン一貫性のため既存トークン・プリセットを流用。独自 CSS は Tailwind ユーティリティで完結。
- 文言: すべて日本語。数値/単位は `toLocaleString("ja-JP")` 等で整形。
- アクセシビリティ: キーボード操作可、ARIA 属性付与。

### 3.4 レポート生成
- Markdown テンプレ: `.github/DESIGN.md` / `6A.1` の構造に準拠。教師コメント欄を必ず残す。
- PDF: WeasyPrint で Markdown → HTML → PDF。フォントは Noto Sans JP。
- ファイル保存: `reports/<student_id>/<session_id>.md|pdf`。DB にパス + (任意) GitHub commit URL を保存。

---

## 4. データ & API 参照

| 参照 | 内容 | 使い方 |
|------|------|--------|
| `.github/database-design.md` | 11 テーブル + RLS | モデル・マイグレーション実装時の唯一の仕様 |
| `.github/api-design.md` | REST/Graph エンドポイント | スキーマ定義の根拠。Response を変更する場合は必ず更新 |
| `.github/ai-implementation.md` | Gemini プロンプト・キャッシュ | AI 機能実装時にそのまま利用。プロンプト変更時は文書も更新 |
| `.github/DESIGN.md` | 総合設計書 | フェーズ境界、ビデオ分析仕様、レポート構造の確認 |
| `docs/tech-stack-simple.md` | 推奨開発環境 | DevContainer/Poetry/pnpm 設定の参照 |

---

## 5. Gemini / AI 実装ガイドライン

1. **キャッシュ必須**: `ai_analysis_cache` を経由。キーは `analysis_type + md5(text)`。
2. **リトライ**: `retry_with_backoff` (max 3) → 失敗時はフォールバック（ルールベース or ユーザーへ警告）。
3. **入力制限**: 1 リクエスト 4000 tokens 以内。長文はチャンク化。
4. **JSON 応答検証**: `pydantic` でバリデーション。異常値はログ + fallback。
5. **教師確認**: 敬語/感情分析結果は「提案」と明記し、教師の修正余地を残す。

---

## 6. セキュリティ & プライバシー

- **PII マスキング**: ログ・外部送信時に生徒名などを含めない。
- **ファイルアクセス**: 生徒ごとディレクトリの ACL を徹底。生徒本人以外の閲覧は禁止。
- **GitHub 連携**: レポートをプッシュする場合はプライベートリポジトリが前提。コミットメッセージは個人情報を避ける。
- **環境変数**: `GEMINI_API_KEY`, `SUPABASE_*` などは `.env` で管理し Git には含めない。

---

## 7. 開発ワークフロー

1. `develop` ブランチから feature ブランチ作成 (`feature/<topic>`)。
2. 実装前に該当仕様書を必ず参照し、差分がある場合は文書を更新。
3. コード + 単体テスト + ドキュメント (API/DB/設計) を同じ PR で揃える。
4. PR テンプレ
   - Summary / Testing / Linked Docs (どの md を更新したか)
   - スクリーンショット or API レスポンス例
5. `main` は本番リリース用。`develop` → 定期的に PR #1 (Develop) で統合。

---

## 8. テスト & 品質

| 種別 | ツール | 必須条件 |
|------|--------|---------|
| Lint | `ruff`, `eslint` | CI でエラー 0 |
| 単体テスト | `pytest`, `vitest` | 変更箇所に対応したテスト追加 |
| API テスト | `pytest-asyncio` + FastAPI `TestClient` | 主要エンドポイントの happy/edge ケース |
| フロント E2E | `Playwright` (Phase2~) | 主要ユーザーフロー |
| パフォーマンス | `locust` or custom | Whisper/レポート生成の処理時間測定 |

---

## 9. コーディングチェックリスト (AI向け)

- [ ] どのフェーズの機能かを確認したか？
- [ ] 関連 md (API/DB/AI/Design) を参照・更新したか？
- [ ] ローカル/学校ネットワーク内で完結する設計か？
- [ ] 教師が最終編集できる UI / レポート構造を保持したか？
- [ ] Gemini 呼び出しはキャッシュ + リトライ付きか？
- [ ] テスト・型・リンターを追加/更新したか？
- [ ] 生徒情報の漏洩がないかログ/レスポンスを確認したか？

---

## 10. よくある実装タスク例

| タスク | 参照 | 注意点 |
|--------|------|--------|
| セッション CRUD | `.github/api-design.md` → Sessions | Supabase Storage との同期、RLS を意識 |
| 音声アップロード | `.github/api-design.md` → `/sessions/{id}/audio` | ファイルは Supabase Storage、メタ情報は DB |
| レポート Markdown | `.github/DESIGN.md` → 6A.1 | 教師コメント欄必須、Mermaid グラフは fallback あり |
| Gemini キーワード | `.github/ai-implementation.md` → keywords | `ai_analysis_cache` 利用。テキストは 4k tokens 以内 |
| ビデオ分析 (Phase4) | `.github/DESIGN.md` → 4.4 & 7A.1 | MediaPipe Pose/Face Mesh + OpenCV、結果は `video_analysis` テーブル |

---

## 11. 禁止事項

- 教師の承認なしに自動でレポート送信・公開する処理
- 生徒の個人情報を含むログ出力・外部 API 送信
- Gemini API 以外の有料/未承認サービス呼び出し
- Supabase RLS を無視した直書き SQL（`rpc` などで権限昇格しない）
- `any` や未チェック例外の放置

---

## 12. 用語

| 用語 | 説明 |
|------|------|
| セッション (session) | 1回の面接練習記録。音声/ビデオ/分析結果/レポートを含む |
| 教師コメント | Markdown レポート内で教師が最終所見を書く欄（削除不可） |
| 受け手印象ベクトル | Gemini が推定する面接官視点の印象 (professionalism 等) |
| 音声感情スコア | librosa で算出する話者の感情状態 (confidence, calmness...) |
| Markdown レポート | 生徒共有用の一次成果物。PDF は派生物 |

---

AI エージェントは本書の指針に従い、仕様が不足している場合は既存ドキュメントを更新しつつ質問・提案を行ってください。
