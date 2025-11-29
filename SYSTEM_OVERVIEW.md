# 圧勝面接練習システム - 全体機能解説

## 📋 システム概要

就職面接の練習をサポートするAI分析システム。音声を入力すると、リアルタイムまたはファイルアップロードで文字起こし・AI分析を実施し、改善点をフィードバックします。

---

## 🎯 主要機能

### 1. **リアルタイム面接練習** 🎙️
**エンドポイント**: `http://localhost:8000/static/realtime.html`

#### 動作フロー:
```
ブラウザ (MediaRecorder API)
    ↓ 音声チャンク (500ms間隔)
WebSocket (/ws/realtime)
    ↓ Base64エンコード音声
RealtimeTranscriber (3秒バッファ)
    ↓ 文字起こし
faster-whisper (base model, Japanese)
    ↓ テキスト累積
Gemini API (gemini-1.5-flash)
    ↓ AI分析
WebSocket → クライアント
    ↓ リアルタイム表示
```

#### 機能詳細:
- **録音**: ブラウザのマイクから音声取得（16kHz, mono推奨）
- **ストリーミング**: 500msごとにWebSocketで音声チャンク送信
- **文字起こし**: 3秒分の音声が貯まると faster-whisper で処理
- **累積テキスト**: 発話内容を連結して保持
- **AI分析**: 累積テキストが100文字を超えるとGemini APIで分析開始
- **ライブ更新**: キーワード、敬語、自信度・緊張度スコアをリアルタイム表示

#### UI要素:
| 要素 | 表示内容 |
|------|----------|
| 文字起こし結果 | リアルタイムで更新されるテキスト |
| 自信度スコア | 0-100（Gemini推定） |
| 緊張度スコア | 0-100（Gemini推定） |
| 検出キーワード | 面接で重要なキーワード（志望動機、強みなど）|
| 敬語フィードバック | 敬語の使い方についての具体的なアドバイス |

---

### 2. **音声ファイル分析** 📁
**エンドポイント**: `http://localhost:8000/` → `/api/analyze`

#### 動作フロー:
```
音声ファイルアップロード (.mp3, .wav, .m4a)
    ↓
FastAPI エンドポイント
    ↓ 並列処理
┌─────────────┬──────────────┬──────────────┐
│ 文字起こし  │ 音響分析     │ 声の感情分析 │
│ (Whisper)   │ (librosa)    │ (librosa)    │
└─────────────┴──────────────┴──────────────┘
    ↓ 結果統合
Gemini API (文字起こしテキストのみ使用)
    ↓ AI分析結果
Markdown レポート生成 (Jinja2)
    ↓
output/reports/{timestamp}.md
```

#### 分析内容:

##### A. 文字起こし (faster-whisper)
- **モデル**: base（軽量・高速）
- **言語**: 日本語
- **出力**: タイムスタンプ付きセグメント + 全文テキスト

##### B. 音響分析 (librosa)
| 項目 | 説明 | 計算方法 |
|------|------|----------|
| 話速 | 文字/分 | 全文字数 ÷ 音声長(分) |
| 平均音量 | dB | RMS エネルギーの平均 |
| 最大音量 | dB | RMS エネルギーの最大値 |
| ポーズ回数 | 無音区間の数 | 音量が閾値以下の連続区間 |
| 平均ピッチ | Hz | 基本周波数の平均 |

##### C. 声の感情分析 (librosa + scipy)
| 項目 | 説明 | 計算方法 |
|------|------|----------|
| Jitter (声の震え) | % | 周波数変動率 |
| ピッチ分散 | Hz² | ピッチの標準偏差² |
| エネルギー分散 | - | 音量の標準偏差² |
| 自信度スコア | 0-100 | 100 - (jitter×1000 + pitch_var/100) |
| 緊張度スコア | 0-100 | jitter×1000 + pitch_var/100 |

##### D. AI分析 (Gemini API)
**入力**: 文字起こしテキスト（最大4000文字）

**出力**:
```json
{
  "keywords": ["志望動機", "強み", "チームワーク", ...],
  "keigo_feedback": "「おっしゃられる」は二重敬語です。「おっしゃる」が正しいです。",
  "confidence_score": 75,
  "nervousness_score": 40,
  "overall_impression": "明るくハキハキした話し方で好印象。..."
}
```

**フォールバック**: Gemini APIが使えない場合、ルールベース分析に自動切替
- キーワード: 形態素解析 or 正規表現
- 敬語: パターンマッチング
- スコア: 音響特徴から推定

---

### 3. **Markdownレポート生成** 📄

#### テンプレート構造:
```markdown
# 面接練習分析レポート

**日時**: 2025-01-15 14:30:00
**分析モデル**: Gemini 1.5 Flash

---

## 📊 分析サマリー

| 項目 | スコア |
|------|--------|
| 自信度 | 75/100 |
| 緊張度 | 40/100 |
| 話速 | 350 文字/分 |

---

## 💬 文字起こし全文

[00:00 - 00:05] はい、よろしくお願いします。
[00:05 - 00:12] 私の志望動機は、貴社の...

---

## 🎤 音響分析

- 平均音量: -25.3 dB
- ポーズ回数: 8回
- 平均ピッチ: 180 Hz

---

## 😊 声の感情分析

- Jitter (声の震え): 0.5%
- 自信度: 75/100
- 緊張度: 40/100

**フィードバック**: 声の震えが少なく、落ち着いた印象です。

---

## 🤖 AI分析結果

### キーワード
- 志望動機
- 強み
- チームワーク

### 敬語チェック
良好です。適切な敬語が使えています。

### 全体印象
明るくハキハキした話し方で好印象...

---

## 📝 教師コメント

（ここに教師が最終所見を記入）
```

#### 出力先:
- **パス**: `output/reports/interview_YYYYMMDD_HHMMSS.md`
- **PDF生成**: 将来的に WeasyPrint で PDF 化（Phase 2+）

---

## 🔧 技術スタック

### バックエンド
| 技術 | 用途 | バージョン |
|------|------|-----------|
| **FastAPI** | Web API フレームワーク | 0.104.0+ |
| **uvicorn** | ASGI サーバー | 0.24.0+ |
| **WebSocket** | リアルタイム通信 | 12.0+ |

### 音声処理
| ライブラリ | 用途 | モデル/設定 |
|-----------|------|------------|
| **faster-whisper** | 文字起こし | base model, Japanese, int8 |
| **librosa** | 音響分析 | RMS, pitch, MFCC |
| **soundfile** | 音声ファイルI/O | - |
| **scipy** | 信号処理 | Jitter計算 |

### AI分析
| サービス | モデル | 用途 |
|---------|--------|------|
| **Gemini API** | gemini-1.5-flash | キーワード抽出、敬語チェック、印象評価 |

### フロントエンド
| 技術 | 用途 |
|------|------|
| **HTML5 MediaRecorder API** | ブラウザ録音 |
| **WebSocket API** | リアルタイム通信 |
| **Vanilla JavaScript** | UI制御（React等は未使用） |

### レポート生成
| 技術 | 用途 |
|------|------|
| **Jinja2** | Markdownテンプレート |
| **python-dateutil** | 日時フォーマット |

---

## 📂 ディレクトリ構造

```
mensetu_renshyuu/
├── backend/
│   ├── main.py                 # FastAPI サーバー + WebSocket
│   ├── services/
│   │   ├── transcription.py         # 文字起こし (Whisper)
│   │   ├── audio_analysis.py        # 音響分析 (librosa)
│   │   ├── voice_emotion.py         # 声の感情分析 (jitter, pitch)
│   │   ├── ai_analysis.py           # Gemini API 統合
│   │   ├── report.py                # Markdown レポート生成
│   │   ├── realtime_transcription.py # リアルタイム処理
│   │   └── video_analysis.py        # Phase 4: ビデオ分析 (stub)
│   ├── templates/
│   │   └── report.md.j2        # Markdownテンプレート
│   └── static/
│       └── realtime.html       # リアルタイムUI
├── output/
│   ├── audio/                  # アップロード音声
│   ├── reports/                # 生成レポート
│   └── temp_chunk.wav          # 一時ファイル
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 起動方法

### 1. 環境構築
```powershell
# 依存パッケージインストール
pip install -r requirements.txt

# 環境変数設定（オプション）
# .env ファイル作成
GEMINI_API_KEY=your_api_key_here
```

### 2. サーバー起動
```powershell
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. アクセス
- **トップページ**: http://localhost:8000/
- **リアルタイム分析**: http://localhost:8000/static/realtime.html
- **ヘルスチェック**: http://localhost:8000/health

---

## 🔐 セキュリティ・プライバシー

### 現在の実装:
- ✅ ローカル実行（学校ネットワーク内で完結）
- ✅ Gemini APIへは文字起こしテキストのみ送信（音声データは送らない）
- ✅ 音声ファイルは `output/audio/` に保存（外部送信なし）
- ⚠️ 認証・権限管理は未実装（Phase 2以降）

### Phase 2以降で追加予定:
- Supabase Auth による教師・生徒認証
- 行レベルセキュリティ (RLS) でデータ分離
- 生徒ごとのディレクトリACL

---

## 📊 分析精度について

### 文字起こし精度
- **モデル**: faster-whisper base（軽量版）
- **想定精度**: 80-90%（クリアな音声の場合）
- **向上方法**: 
  - より大きなモデル（small, medium, large）に変更可能
  - 音声品質向上（ノイズ除去、明瞭な発音）

### AI分析精度
- **モデル**: Gemini 1.5 Flash
- **強み**: 日本語の敬語・ニュアンス理解、文脈把握
- **弱み**: ハルシネーション（事実と異なる分析）の可能性
- **対策**: 教師が最終確認・編集する前提

### 音響分析精度
- **Jitter計算**: librosa の pitch 検出精度に依存
- **想定**: 参考値として利用（医療レベルの精度は保証しない）

---

## 🎯 今後の拡張予定

### Phase 2: リアルタイム機能強化
- [ ] 話者識別（教師・生徒の区別）
- [ ] 教師メモ機能（タイムスタンプ同期）
- [ ] セッション管理（SQLite or JSON）
- [ ] PDF レポート生成（WeasyPrint）

### Phase 3: データ蓄積・可視化
- [ ] Supabase 統合（PostgreSQL + Auth）
- [ ] 練習履歴の記録・閲覧
- [ ] 成長グラフ（スコア推移）
- [ ] 教師ダッシュボード

### Phase 4: ビデオ分析
- [ ] MediaPipe Face Mesh（表情分析）
- [ ] MediaPipe Pose（姿勢分析）
- [ ] MediaPipe Hands（ジェスチャー検出）
- [ ] 目線トラッキング
- [ ] ブラウザカメラ録画

---

## ⚙️ 設定・カスタマイズ

### Whisper モデル変更
`backend/services/transcription.py` の `MODEL_SIZE` を変更:
```python
MODEL_SIZE = "base"  # tiny, base, small, medium, large から選択
```

### バッファ時間調整（リアルタイム）
`backend/services/realtime_transcription.py`:
```python
self.buffer_duration = 3.0  # 秒単位（推奨: 2-5秒）
```

### 音声チャンク送信間隔
`backend/static/realtime.html`:
```javascript
mediaRecorder.start(500);  // ms単位（推奨: 500-1000ms）
```

### Gemini プロンプト調整
`backend/services/ai_analysis.py` の `prompt` 変数を編集

---

## 🐛 トラブルシューティング

### Q: 文字起こしが遅い
**A**: Whisper モデルサイズを `tiny` に変更、またはGPU版のインストール

### Q: マイクが認識されない（リアルタイム）
**A**: 
1. ブラウザのマイク許可を確認
2. HTTPSが必要な場合あり（本番環境では証明書設定）
3. Chrome/Edge推奨（Firefox/Safariは一部制限あり）

### Q: Gemini APIエラー
**A**: 
1. `.env` に正しいAPIキーを設定
2. API使用量制限を確認
3. エラー時はルールベース分析に自動切替

### Q: WebSocket接続エラー
**A**: 
1. サーバーが起動しているか確認
2. ファイアウォール設定を確認
3. ブラウザコンソールでエラーログ確認

---

## 📞 サポート・貢献

- **Issue報告**: GitHub Issues
- **機能リクエスト**: GitHub Discussions
- **開発参加**: Pull Request歓迎

---

**最終更新**: 2025年11月29日
**バージョン**: 1.0.0 (Phase 1 完了)
