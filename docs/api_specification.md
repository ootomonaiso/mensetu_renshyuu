# 圧勝面接 - API仕様書

## ドキュメント情報
- **作成日**: 2025年12月20日
- **バージョン**: 1.0
- **プロジェクト名**: 圧勝面接 (mensetu_renshyuu)
- **ベースURL**: `http://127.0.0.1:8000`

---

## 1. 概要

### 1.1 APIの目的
圧勝面接システムのWebインターフェースとバックエンド処理を接続するREST APIを提供する。

### 1.2 認証
- **認証方式**: なし（ローカルホストのみアクセス可能）
- **アクセス制限**: `127.0.0.1` からのみアクセス可能

### 1.3 通信プロトコル
- **プロトコル**: HTTP/1.1
- **データ形式**: JSON, multipart/form-data

### 1.4 エンコーディング
- **文字コード**: UTF-8
- **タイムゾーン**: UTC

---

## 2. エンドポイント一覧

| メソッド | エンドポイント | 説明 | 認証 |
|---------|---------------|------|------|
| GET | `/` | メインページ表示 | 不要 |
| POST | `/api/upload` | 音声ファイルアップロード | 不要 |
| GET | `/api/status/{interview_id}` | 処理状況取得 | 不要 |
| GET | `/api/report/{interview_id}` | レポート取得 | 不要 |
| GET | `/reports/{interview_id}` | レポートHTML表示 | 不要 |
| GET | `/api/interviews` | 面接履歴一覧取得 | 不要 |
| DELETE | `/api/interviews/{interview_id}` | 面接データ削除 | 不要 |
| GET | `/health` | ヘルスチェック | 不要 |

---

## 3. エンドポイント詳細

### 3.1 メインページ表示

#### リクエスト
```
GET /
```

#### パラメータ
なし

#### レスポンス
```
Content-Type: text/html
Status: 200 OK
```
HTMLページを返却

---

### 3.2 音声ファイルアップロード

#### リクエスト
```
POST /api/upload
Content-Type: multipart/form-data
```

#### パラメータ

| パラメータ名 | 型 | 必須 | 説明 |
|------------|---|------|------|
| file | File | ○ | 音声ファイル（WAV, MP3, M4A, OGG, FLAC） |

#### リクエスト例
```bash
curl -X POST "http://127.0.0.1:8000/api/upload" \
  -F "file=@interview_sample.wav"
```

#### レスポンス

**成功時（200 OK）**:
```json
{
  "success": true,
  "interview_id": 1,
  "message": "ファイルをアップロードしました。分析を開始します..."
}
```

**失敗時（400 Bad Request）**:
```json
{
  "success": false,
  "error": "ファイルサイズが上限（100MB）を超えています"
}
```

**失敗時（415 Unsupported Media Type）**:
```json
{
  "success": false,
  "error": "非対応のファイル形式です。WAV, MP3, M4A, OGG, FLACのみ対応しています"
}
```

#### エラーコード

| ステータスコード | 説明 |
|----------------|------|
| 200 | アップロード成功 |
| 400 | ファイルサイズ超過、パラメータ不正 |
| 415 | 非対応のファイル形式 |
| 500 | サーバーエラー |

---

### 3.3 処理状況取得

#### リクエスト
```
GET /api/status/{interview_id}
```

#### パスパラメータ

| パラメータ名 | 型 | 必須 | 説明 |
|------------|---|------|------|
| interview_id | Integer | ○ | 面接ID |

#### リクエスト例
```bash
curl -X GET "http://127.0.0.1:8000/api/status/1"
```

#### レスポンス

**処理中（200 OK）**:
```json
{
  "interview_id": 1,
  "status": "processing",
  "progress": 45,
  "current_step": "音声分析中...",
  "estimated_time_remaining": 120
}
```

**完了時（200 OK）**:
```json
{
  "interview_id": 1,
  "status": "completed",
  "progress": 100,
  "report_path": "/reports/1"
}
```

**失敗時（200 OK）**:
```json
{
  "interview_id": 1,
  "status": "failed",
  "error_message": "Whisper初期化に失敗しました"
}
```

**見つからない場合（404 Not Found）**:
```json
{
  "error": "指定された面接IDが見つかりません"
}
```

#### ステータス値

| ステータス | 説明 |
|-----------|------|
| uploaded | アップロード完了、処理待ち |
| processing | 処理中 |
| completed | 処理完了 |
| failed | 処理失敗 |

---

### 3.4 レポート取得（JSON）

#### リクエスト
```
GET /api/report/{interview_id}
```

#### パスパラメータ

| パラメータ名 | 型 | 必須 | 説明 |
|------------|---|------|------|
| interview_id | Integer | ○ | 面接ID |

#### リクエスト例
```bash
curl -X GET "http://127.0.0.1:8000/api/report/1"
```

#### レスポンス

**成功時（200 OK）**:
```json
{
  "interview_id": 1,
  "filename": "interview_20251220_143000_sample.wav",
  "created_at": "2025-12-20T14:30:00Z",
  "duration": 120.5,
  "transcription": [
    {
      "speaker": "教師",
      "start": 0.5,
      "end": 3.2,
      "text": "自己紹介をお願いします。"
    },
    {
      "speaker": "生徒",
      "start": 3.5,
      "end": 10.8,
      "text": "はい、私は〇〇大学の△△です。よろしくお願いいたします。"
    }
  ],
  "audio_analysis": {
    "overall": {
      "duration": 120.5,
      "speaking_rate": 350.2
    },
    "by_speaker": {
      "教師": {
        "pitch_mean": 180.5,
        "pitch_std": 35.2,
        "volume_mean": -18.3,
        "speaking_rate": 320.5,
        "zero_crossing_rate": 0.08,
        "spectral_centroid": 2100.3
      },
      "生徒": {
        "pitch_mean": 220.8,
        "pitch_std": 42.1,
        "volume_mean": -22.1,
        "speaking_rate": 380.9,
        "zero_crossing_rate": 0.12,
        "spectral_centroid": 2450.6
      }
    }
  },
  "emotion_analysis": {
    "生徒": {
      "confidence": 0.65,
      "tension": 0.72,
      "calmness": 0.58,
      "clarity": 0.80
    }
  },
  "keigo_evaluation": {
    "segments": [
      {
        "speaker": "生徒",
        "original_text": "私は〇〇大学の△△です。よろしくお願いいたします。",
        "issues": [],
        "score": 95
      }
    ],
    "overall_score": 92,
    "summary": "敬語の使用は適切です。面接にふさわしい丁寧な表現ができています。"
  }
}
```

**見つからない場合（404 Not Found）**:
```json
{
  "error": "指定された面接IDが見つかりません"
}
```

---

### 3.5 レポートHTML表示

#### リクエスト
```
GET /reports/{interview_id}
```

#### パスパラメータ

| パラメータ名 | 型 | 必須 | 説明 |
|------------|---|------|------|
| interview_id | Integer | ○ | 面接ID |

#### リクエスト例
```bash
curl -X GET "http://127.0.0.1:8000/reports/1"
```

#### レスポンス
```
Content-Type: text/html
Status: 200 OK
```
HTMLレポートページを返却

---

### 3.6 面接履歴一覧取得

#### リクエスト
```
GET /api/interviews
```

#### クエリパラメータ

| パラメータ名 | 型 | 必須 | デフォルト | 説明 |
|------------|---|------|-----------|------|
| page | Integer | × | 1 | ページ番号 |
| per_page | Integer | × | 20 | 1ページあたりの件数 |
| status | String | × | all | ステータスフィルタ（uploaded/processing/completed/failed/all） |

#### リクエスト例
```bash
curl -X GET "http://127.0.0.1:8000/api/interviews?page=1&per_page=10&status=completed"
```

#### レスポンス

**成功時（200 OK）**:
```json
{
  "total": 45,
  "page": 1,
  "per_page": 10,
  "total_pages": 5,
  "interviews": [
    {
      "id": 15,
      "filename": "interview_20251220_150000.wav",
      "created_at": "2025-12-20T15:00:00Z",
      "duration": 180.2,
      "status": "completed",
      "report_url": "/reports/15"
    },
    {
      "id": 14,
      "filename": "interview_20251220_143000.wav",
      "created_at": "2025-12-20T14:30:00Z",
      "duration": 120.5,
      "status": "completed",
      "report_url": "/reports/14"
    }
  ]
}
```

---

### 3.7 面接データ削除

#### リクエスト
```
DELETE /api/interviews/{interview_id}
```

#### パスパラメータ

| パラメータ名 | 型 | 必須 | 説明 |
|------------|---|------|------|
| interview_id | Integer | ○ | 面接ID |

#### リクエスト例
```bash
curl -X DELETE "http://127.0.0.1:8000/api/interviews/1"
```

#### レスポンス

**成功時（200 OK）**:
```json
{
  "success": true,
  "message": "面接データを削除しました"
}
```

**見つからない場合（404 Not Found）**:
```json
{
  "success": false,
  "error": "指定された面接IDが見つかりません"
}
```

---

### 3.8 ヘルスチェック

#### リクエスト
```
GET /health
```

#### パラメータ
なし

#### リクエスト例
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

#### レスポンス

**成功時（200 OK）**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-20T15:30:00Z",
  "services": {
    "whisper": "available",
    "pyannote": "available",
    "ollama": "available",
    "database": "connected"
  }
}
```

**一部サービス利用不可（200 OK）**:
```json
{
  "status": "degraded",
  "timestamp": "2025-12-20T15:30:00Z",
  "services": {
    "whisper": "available",
    "pyannote": "unavailable",
    "ollama": "unavailable",
    "database": "connected"
  }
}
```

---

## 4. データ型定義

### 4.1 Interview（面接データ）
```typescript
interface Interview {
  id: number;
  filename: string;
  created_at: string;  // ISO 8601形式
  duration: number;    // 秒
  status: "uploaded" | "processing" | "completed" | "failed";
  report_url?: string;
  error_message?: string;
}
```

### 4.2 Transcription（文字起こし結果）
```typescript
interface TranscriptionSegment {
  speaker: string;     // "教師" | "生徒"
  start: number;       // 開始時間（秒）
  end: number;         // 終了時間（秒）
  text: string;        // 発話内容
}

type Transcription = TranscriptionSegment[];
```

### 4.3 AudioAnalysis（音声分析結果）
```typescript
interface AudioAnalysis {
  overall: {
    duration: number;
    speaking_rate: number;
  };
  by_speaker: {
    [speaker: string]: {
      pitch_mean: number;
      pitch_std: number;
      volume_mean: number;
      speaking_rate: number;
      zero_crossing_rate: number;
      spectral_centroid: number;
    };
  };
}
```

### 4.4 EmotionAnalysis（感情分析結果）
```typescript
interface EmotionAnalysis {
  [speaker: string]: {
    confidence: number;   // 0.0-1.0
    tension: number;      // 0.0-1.0
    calmness: number;     // 0.0-1.0
    clarity: number;      // 0.0-1.0
  };
}
```

### 4.5 KeigoEvaluation（敬語評価結果）
```typescript
interface KeigoIssue {
  type: string;         // "敬語ミス" | "口語表現" | "若者言葉"
  location: string;     // 問題箇所
  suggestion: string;   // 修正案
  severity: "低" | "中" | "高";
}

interface KeigoSegment {
  speaker: string;
  original_text: string;
  issues: KeigoIssue[];
  score: number;        // 0-100
}

interface KeigoEvaluation {
  segments: KeigoSegment[];
  overall_score: number;
  summary: string;
}
```

---

## 5. エラーレスポンス

### 5.1 共通エラーフォーマット
```json
{
  "error": "エラーメッセージ",
  "error_code": "E-001",
  "details": {
    "field": "file",
    "reason": "ファイルサイズが上限を超えています"
  }
}
```

### 5.2 HTTPステータスコード一覧

| ステータスコード | 説明 |
|----------------|------|
| 200 OK | リクエスト成功 |
| 400 Bad Request | リクエストパラメータが不正 |
| 404 Not Found | リソースが見つからない |
| 415 Unsupported Media Type | 非対応のファイル形式 |
| 500 Internal Server Error | サーバー内部エラー |
| 503 Service Unavailable | サービス利用不可（モジュール初期化失敗等） |

---

## 6. レート制限

**制限なし**（ローカル実行のため）

---

## 7. 使用例

### 7.1 完全なワークフロー例

```bash
# 1. 音声ファイルをアップロード
RESPONSE=$(curl -X POST "http://127.0.0.1:8000/api/upload" \
  -F "file=@interview.wav")
INTERVIEW_ID=$(echo $RESPONSE | jq -r '.interview_id')

# 2. 処理状況を定期的に確認
while true; do
  STATUS=$(curl -X GET "http://127.0.0.1:8000/api/status/$INTERVIEW_ID" | jq -r '.status')
  if [ "$STATUS" = "completed" ]; then
    echo "処理完了"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "処理失敗"
    exit 1
  fi
  echo "処理中... ($STATUS)"
  sleep 5
done

# 3. レポート取得
curl -X GET "http://127.0.0.1:8000/api/report/$INTERVIEW_ID" | jq .

# 4. HTMLレポートをブラウザで開く
open "http://127.0.0.1:8000/reports/$INTERVIEW_ID"
```

### 7.2 JavaScript (Fetch API) 使用例

```javascript
// ファイルアップロード
async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://127.0.0.1:8000/api/upload', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  return result.interview_id;
}

// 処理状況確認
async function checkStatus(interviewId) {
  const response = await fetch(`http://127.0.0.1:8000/api/status/${interviewId}`);
  const status = await response.json();
  return status;
}

// レポート取得
async function getReport(interviewId) {
  const response = await fetch(`http://127.0.0.1:8000/api/report/${interviewId}`);
  const report = await response.json();
  return report;
}

// 使用例
const file = document.getElementById('fileInput').files[0];
const interviewId = await uploadFile(file);

// ポーリングで処理完了を待つ
const interval = setInterval(async () => {
  const status = await checkStatus(interviewId);
  if (status.status === 'completed') {
    clearInterval(interval);
    const report = await getReport(interviewId);
    console.log('レポート:', report);
    window.location.href = `/reports/${interviewId}`;
  }
}, 3000);
```

---

## 8. WebSocket API（将来実装）

### 8.1 リアルタイム進捗通知
```
ws://127.0.0.1:8000/ws/progress/{interview_id}
```

**メッセージフォーマット**:
```json
{
  "interview_id": 1,
  "step": "文字起こし",
  "progress": 45,
  "message": "文字起こし処理中..."
}
```

---

## 9. バージョニング

現在のバージョン: **v1.0**

将来的にAPIに破壊的変更が必要な場合は、URLにバージョンを含める:
```
/api/v2/upload
```

---

## 10. CORS設定

**現在の設定**: CORS無効（ローカルホストのみアクセス可）

**将来の拡張時**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 11. 変更履歴

| バージョン | 日付 | 変更内容 |
|----------|------|---------|
| 1.0 | 2025-12-20 | 初版作成 |

---

## 12. 関連ドキュメント

- [開発設計書](./design_document.md)
- [システム仕様書](./system_specification.md)
- [データベース設計書](./database_design.md)

---

**文書ステータス**: 承認済み
**次回レビュー日**: 2026-01-20
