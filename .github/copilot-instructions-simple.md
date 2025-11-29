# Copilot Instructions (簡易版 MVP)

> **簡易版 MVP**: ログイン・DB・非同期処理は不要。音声アップロード → 分析 → Markdown レポート出力のみ。

関連ドキュメント: `requirements.md`, `plan.md`, `docs/tech-stack.md`

---

## 1. 開発全体方針

1. **シンプル第一**: FastAPI で音声アップロード → 同期処理 → Markdown 出力。
2. **ローカル完結**: 音声と分析結果のみローカル保存 (`output/audio/`, `output/reports/`)。
3. **コスト最小化**: Gemini API のみ使用 (無料枠 1,500 リクエスト/日)。
4. **日本語出力**: レポートは日本語。教師コメント欄を必ず残す。

---

## 2. アーキテクチャ (簡易版)

| 層 | 技術 | 備考 |
|----|------|------|
| API | FastAPI (Python 3.11+) | 音声アップロード受付のみ |
| 文字起こし | faster-whisper | CPU で動作 (GPU あれば高速) |
| 音響分析 | librosa | 話速、音量、ポーズ検出 |
| AI 分析 | Gemini API (gemini-1.5-flash) | キーワード/敬語/感情 |
| レポート | Jinja2 + Markdown | `output/reports/{timestamp}.md` |
| 保存 | ローカルファイルシステム | DB 不要 |

---

## 3. ディレクトリ構造

```
mensetu_renshyuu/
├── backend/
│   ├── main.py              # FastAPI サーバー (全エンドポイント)
│   ├── services/
│   │   ├── transcription.py # faster-whisper
│   │   ├── audio_analysis.py # librosa
│   │   ├── ai_analysis.py   # Gemini API
│   │   └── report.py        # Markdown 生成
│   └── templates/
│       └── report.md.j2     # レポートテンプレート
├── output/
│   ├── audio/               # アップロード音声
│   └── reports/             # 生成レポート
├── .env                     # GEMINI_API_KEY
└── requirements.txt
```

---

## 4. コーディングルール

### 4.1 Backend (FastAPI)
- **構成**: `backend/main.py` に全エンドポイント (Phase 1 は 1 ファイルでOK)
- **サービス層**: `backend/services/` に分離
  - `transcription.py`: `faster_whisper.WhisperModel` で文字起こし
  - `audio_analysis.py`: `librosa` で話速/音量/ポーズ
  - `ai_analysis.py`: `google.generativeai` でキーワード/敬語/感情
  - `report.py`: Jinja2 で Markdown 生成
- **テンプレート**: `backend/templates/report.md.j2` で管理
- **ファイル保存**:
  - 音声: `output/audio/{timestamp}_{filename}`
  - レポート: `output/reports/{timestamp}.md`

### 4.2 エラー処理
- Gemini API: リトライ 3 回、失敗時はルールベースでフォールバック
- ファイルアップロード: 拡張子 (mp3/wav/m4a) とサイズ (< 100MB) チェック
- ログ: `logging` モジュール使用、`print()` は開発時のみ

### 4.3 Gemini API 使用方針
- **キーワード抽出**: 面接内容から重要語句を 5~10 個
- **敬語チェック**: 不適切な表現を指摘
- **感情分析**: 自信度、緊張度を 0~100 で推定
- **入力制限**: 4000 tokens 以内
- **リトライ**: 3 回まで、失敗時は「分析できませんでした」と記載

---

## 5. レポート構造 (Markdown)

```markdown
# 面接練習レポート

**日時**: {timestamp}  
**音声ファイル**: {filename}

## 📝 文字起こし結果

{transcript}

## 📊 音響分析

- **話速**: {speech_rate} 文字/分
- **平均音量**: {volume_db} dB
- **ポーズ回数**: {pause_count} 回

## 🤖 AI 分析

### キーワード
{keywords}

### 敬語チェック
{keigo_feedback}

### 感情分析
- **自信度**: {confidence_score}/100
- **緊張度**: {nervousness_score}/100

## 💬 教師コメント

<!-- ここに教師がコメントを追加 -->
```

---

## 6. 実装順序

1. ✅ `backend/main.py` - FastAPI 最小サーバー
2. ⏳ 音声アップロード API (`POST /api/analyze`)
3. ⏳ `transcription.py` - faster-whisper 連携
4. ⏳ `audio_analysis.py` - librosa 音響分析
5. ⏳ `ai_analysis.py` - Gemini API 連携
6. ⏳ `report.py` + `report.md.j2` - Markdown 生成
7. ⏳ 簡易 Web UI (HTML フォーム)

---

## 7. テスト

- **手動テスト**: 音声ファイルをアップロードしてレポート生成確認
- **API テスト** (Phase 2): `pytest` + FastAPI `TestClient`

---

## 8. チェックリスト

- [ ] 音声ファイルが `output/audio/` に保存されるか
- [ ] faster-whisper で文字起こしが成功するか
- [ ] librosa で話速/音量/ポーズが計算されるか
- [ ] Gemini API でキーワード/敬語/感情が取得できるか
- [ ] Markdown レポートが `output/reports/` に生成されるか
- [ ] 教師コメント欄がレポートに含まれているか
- [ ] エラー時に適切なフォールバック処理が動くか

---

## 9. 禁止事項

- DB/認証機能の実装 (Phase 2 以降)
- 複雑な非同期処理 (Celery/Redis は不要)
- Gemini API 以外の有料サービス利用
- 生徒の個人情報をログに出力

---

AI エージェントは本指針に従い、シンプルで動作する MVP を優先して実装してください。
