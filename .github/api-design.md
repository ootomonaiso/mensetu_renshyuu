# API設計書

**更新日**: 2025年11月29日

---

## ベースURL

- **開発**: `http://localhost:8000/api/v1`
- **本番**: `https://api.mensetu-app.example.com/api/v1`

---

## 認証

### ヘッダー
```http
Authorization: Bearer {access_token}
```

Supabase Authのトークンを使用。

---

## エンドポイント一覧

### 認証 (Auth)

#### POST /auth/signup
ユーザー登録

**Request:**
```json
{
  "email": "student@example.com",
  "password": "SecurePass123!",
  "name": "山田太郎",
  "role": "student"
}
```

**Response: 201**
```json
{
  "user": {
    "id": "uuid",
    "email": "student@example.com"
  },
  "session": {
    "access_token": "eyJ...",
    "refresh_token": "...",
    "expires_in": 3600
  }
}
```

#### POST /auth/login
ログイン

**Request:**
```json
{
  "email": "student@example.com",
  "password": "SecurePass123!"
}
```

**Response: 200**
```json
{
  "session": {
    "access_token": "eyJ...",
    "refresh_token": "...",
    "expires_in": 3600
  },
  "user": {
    "id": "uuid",
    "email": "student@example.com",
    "role": "student"
  }
}
```

#### POST /auth/refresh
トークンリフレッシュ

**Request:**
```json
{
  "refresh_token": "..."
}
```

**Response: 200**
```json
{
  "access_token": "eyJ...",
  "expires_in": 3600
}
```

#### POST /auth/logout
ログアウト

**Response: 204**

---

### プロフィール (Profiles)

#### GET /profiles/me
自分のプロフィール取得

**Response: 200**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "role": "student",
  "name": "山田太郎",
  "student_profile": {
    "grade": "高3",
    "target_industry": "IT",
    "target_company": "株式会社サイバーエージェント",
    "club_activity": "バスケットボール部",
    "achievements": [
      {
        "title": "県大会優勝",
        "description": "キャプテンとしてチームをまとめた",
        "date": "2024-08"
      }
    ]
  }
}
```

#### PUT /profiles/me
プロフィール更新

**Request:**
```json
{
  "name": "山田太郎",
  "student_profile": {
    "grade": "高3",
    "target_industry": "IT",
    "club_activity": "バスケットボール部"
  }
}
```

**Response: 200**
```json
{
  "id": "uuid",
  "updated_at": "2025-11-29T10:00:00Z"
}
```

#### GET /students/{student_id}
生徒情報取得 (教師のみ)

**Response: 200**
```json
{
  "id": "uuid",
  "name": "山田太郎",
  "grade": "高3",
  "target_industry": "IT",
  "session_count": 5,
  "avg_score": 75,
  "last_session_date": "2025-11-28"
}
```

---

### セッション (Sessions)

#### POST /sessions
新規セッション作成

**Request:**
```json
{
  "title": "IT企業面接練習 第3回",
  "session_type": "practice",
  "target_company": "株式会社サイバーエージェント",
  "target_position": "エンジニア"
}
```

**Response: 201**
```json
{
  "id": "uuid",
  "student_id": "uuid",
  "title": "IT企業面接練習 第3回",
  "status": "recording",
  "created_at": "2025-11-29T10:00:00Z"
}
```

#### GET /sessions
セッション一覧取得

**Query Parameters:**
- `student_id` (optional): 生徒ID
- `status` (optional): recording, completed, failed
- `limit` (default: 20)
- `offset` (default: 0)

**Response: 200**
```json
{
  "sessions": [
    {
      "id": "uuid",
      "title": "IT企業面接練習 第3回",
      "session_type": "practice",
      "status": "completed",
      "duration": 1200,
      "total_score": 78,
      "created_at": "2025-11-28T14:00:00Z"
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0
}
```

#### GET /sessions/{session_id}
セッション詳細取得

**Response: 200**
```json
{
  "id": "uuid",
  "student_id": "uuid",
  "teacher_id": "uuid",
  "title": "IT企業面接練習 第3回",
  "session_type": "practice",
  "target_company": "株式会社サイバーエージェント",
  "audio_url": "https://storage.supabase.co/...",
  "audio_duration": 1200,
  "transcript": "はい、本日はよろしくお願いいたします...",
  "status": "completed",
  "created_at": "2025-11-28T14:00:00Z"
}
```

#### POST /sessions/{session_id}/audio
音声アップロード

**Request: multipart/form-data**
```
audio: File (audio/wav, audio/mp3, audio/webm)
```

**Response: 200**
```json
{
  "audio_url": "https://storage.supabase.co/...",
  "duration": 1200,
  "status": "processing"
}
```

#### DELETE /sessions/{session_id}
セッション削除

**Response: 204**

---

### 分析 (Analysis)

#### POST /analyze/transcribe
音声文字起こし

**Request:**
```json
{
  "session_id": "uuid",
  "audio_url": "https://storage.supabase.co/..."
}
```

**Response: 200**
```json
{
  "transcript": "はい、本日はよろしくお願いいたします...",
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "はい、本日はよろしくお願いいたします。",
      "speaker": "student"
    }
  ],
  "duration": 1200
}
```

#### POST /analyze/acoustic
音響分析

**Request:**
```json
{
  "session_id": "uuid",
  "audio_url": "https://storage.supabase.co/..."
}
```

**Response: 200**
```json
{
  "speech_rate": {
    "avg": 165,
    "timeline": [
      {"time": 0, "rate": 150},
      {"time": 10, "rate": 170}
    ]
  },
  "volume": {
    "avg_db": 65,
    "timeline": [
      {"time": 0, "db": 62},
      {"time": 10, "db": 68}
    ]
  },
  "pitch": {
    "avg_hz": 180,
    "variation": 25.5
  },
  "pauses": {
    "count": 15,
    "avg_duration": 0.8,
    "timeline": [
      {"start": 5.2, "end": 6.0, "duration": 0.8}
    ]
  },
  "fillers": {
    "count": 8,
    "details": [
      {"word": "えーと", "count": 5, "timestamps": [10.2, 45.6]},
      {"word": "あの", "count": 3, "timestamps": [30.1, 60.5]}
    ]
  }
}
```

#### POST /analyze/keywords
キーワード抽出 (Gemini API使用)

**Request:**
```json
{
  "text": "はい、本日はよろしくお願いいたします。私は大学時代、バスケットボール部でキャプテンを務めておりました..."
}
```

**Response: 200**
```json
{
  "keywords": [
    {
      "keyword": "バスケットボール部",
      "relevance": 0.95,
      "context": "学生時代の経験"
    },
    {
      "keyword": "キャプテン",
      "relevance": 0.90,
      "context": "リーダーシップ"
    },
    {
      "keyword": "チームワーク",
      "relevance": 0.85,
      "context": "協調性"
    }
  ],
  "categories": ["学生時代の経験", "自己PR", "リーダーシップ"],
  "summary": "バスケットボール部でのキャプテン経験を通じて..."
}
```

#### POST /analyze/keigo
敬語分析 (Gemini API使用)

**Request:**
```json
{
  "text": "はい、そうっすね。マジでやばいと思いました。御社に入りたいと思っております。"
}
```

**Response: 200**
```json
{
  "score": 52,
  "overall_assessment": "敬語の使い方に問題があります。タメ口表現が目立ちます。",
  "errors": [
    {
      "text": "っす",
      "position": 6,
      "issue": "タメ口表現",
      "suggestion": "です",
      "severity": "warning",
      "explanation": "「っす」はカジュアルすぎます。面接では「です」を使いましょう。"
    },
    {
      "text": "マジで",
      "position": 11,
      "issue": "俗語・タメ口",
      "suggestion": "本当に、非常に",
      "severity": "critical",
      "explanation": "「マジで」は俗語です。「本当に」または「非常に」と言い換えましょう。"
    },
    {
      "text": "やばい",
      "position": 15,
      "issue": "俍語・不適切",
      "suggestion": "大変、素晴らしい、印象的",
      "severity": "critical",
      "explanation": "「やばい」は面接では不適切です。具体的な表現に置き換えましょう。"
    }
  ],
  "strengths": [
    {
      "text": "御社に入りたいと思っております",
      "explanation": "「御社」「おります」と適切な謙譲語が使えています。"
    }
  ],
  "recommendations": [
    "タメ口表現を避け、丁寧語を使いましょう",
    "俽語や俽言を正式な言葉に置き換える練習をしましょう"
  ],
  "correct_expressions_count": 3,
  "total_expressions_count": 8
}
```

#### POST /analyze/sentiment
感情分析 (Gemini API + 音声分析)

**Request:**
```json
{
  "text": "はい、本日はよろしくお願いいたします。非常に楽しみにしておりました。緑張していますが、精一杯お答えいたします。",
  "audio_features": {
    "avg_pitch": 180,
    "pitch_variation": 25,
    "avg_volume": 65,
    "speech_rate": 165
  }
}
```

**Response: 200**
```json
{
  "overall_sentiment": "positive_with_nervousness",
  "confidence": 0.85,
  "text_analysis": {
    "sentiment_scores": {
      "positive": 0.70,
      "neutral": 0.25,
      "negative": 0.05
    },
    "emotions": {
      "enthusiastic": 0.75,
      "nervous": 0.45,
      "confident": 0.55,
      "polite": 0.90
    },
    "key_indicators": [
      {
        "phrase": "非常に楽しみにしておりました",
        "emotion": "enthusiastic",
        "intensity": 0.8
      },
      {
        "phrase": "緑張していますが",
        "emotion": "nervous",
        "intensity": 0.6
      }
    ]
  },
  "voice_analysis": {
    "emotion_from_voice": {
      "confident": 0.50,
      "nervous": 0.50
    },
    "indicators": [
      "音声の変動がやや大きい（緑張の兆候）",
      "声量は適切なレベル"
    ]
  },
  "combined_assessment": {
    "summary": "前向きで熱意が伝わりますが、適度な緑張感も感じられます。このバランスは良い状態です。",
    "strengths": [
      "熱意が明確に伝わっている",
      "丁寧な言葉遣い"
    ],
    "improvements": [
      "深呼吸で緑張をコントロールするとより落ち着いた印象に"
    ]
  },
  "timeline": [
    {
      "time_range": "0-5s",
      "dominant_emotion": "polite",
      "intensity": 0.9
    },
    {
      "time_range": "5-10s",
      "dominant_emotion": "enthusiastic",
      "intensity": 0.75
    },
    {
      "time_range": "10-15s",
      "dominant_emotion": "nervous",
      "intensity": 0.6
    }
  ]
}
```

---

### 評価 (Evaluations)

#### POST /evaluations
評価作成

**Request:**
```json
{
  "session_id": "uuid",
  "appearance_score": 85,
  "speech_clarity_score": 75,
  "keigo_score": 80,
  "content_relevance_score": 78,
  "logic_score": 82,
  "enthusiasm_score": 88,
  "strengths": [
    "明るく元気な挨拶ができていた",
    "具体的なエピソードを交えて説明できていた"
  ],
  "improvements": [
    "話速がやや速い",
    "フィラーが多い"
  ]
}
```

**Response: 201**
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "total_score": 81,
  "created_at": "2025-11-29T10:00:00Z"
}
```

#### GET /evaluations/{evaluation_id}
評価詳細取得

**Response: 200**
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "appearance_score": 85,
  "speech_clarity_score": 75,
  "keigo_score": 80,
  "total_score": 81,
  "strengths": ["..."],
  "improvements": ["..."],
  "extracted_keywords": [...],
  "keigo_errors": [...],
  "created_at": "2025-11-29T10:00:00Z"
}
```

---

### フィードバック (Feedback)

#### POST /feedback
フィードバック作成

**Request:**
```json
{
  "session_id": "uuid",
  "feedback_type": "ai_generated",
  "summary": "全体的に良い面接でした。特に志望動機が明確で...",
  "good_points": [
    "明るく元気な挨拶",
    "具体的なエピソード"
  ],
  "improvement_points": [
    "話速を少し落とす",
    "フィラーを減らす"
  ],
  "specific_advice": "深呼吸してから話し始めると良いでしょう。",
  "practice_tasks": [
    "鏡の前で練習",
    "タイマーで時間管理"
  ]
}
```

**Response: 201**
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "created_at": "2025-11-29T10:00:00Z"
}
```

#### GET /feedback/{session_id}
セッションのフィードバック取得

**Response: 200**
```json
{
  "feedbacks": [
    {
      "id": "uuid",
      "feedback_type": "ai_generated",
      "summary": "...",
      "good_points": ["..."],
      "improvement_points": ["..."],
      "created_at": "2025-11-29T10:00:00Z"
    },
    {
      "id": "uuid",
      "feedback_type": "teacher_manual",
      "summary": "...",
      "created_by": "teacher-uuid",
      "created_at": "2025-11-29T11:00:00Z"
    }
  ]
}
```

---

### レポート (Reports)

#### GET /reports/{session_id}
レポート取得 (JSON)

**Response: 200**
```json
{
  "session": {
    "id": "uuid",
    "title": "IT企業面接練習 第3回",
    "date": "2025-11-28",
    "duration": 1200
  },
  "student": {
    "name": "山田太郎",
    "grade": "高3"
  },
  "evaluation": {
    "total_score": 81,
    "scores": {
      "appearance": 85,
      "speech_clarity": 75,
      "keigo": 80,
      "content": 78,
      "logic": 82,
      "enthusiasm": 88
    }
  },
  "audio_analysis": {
    "speech_rate": 165,
    "volume_db": 65,
    "filler_count": 8
  },
  "feedback": {
    "summary": "...",
    "good_points": ["..."],
    "improvements": ["..."]
  },
  "history": [
    {
      "date": "2025-11-20",
      "total_score": 75
    },
    {
      "date": "2025-11-28",
      "total_score": 81
    }
  ]
}
```

#### GET /reports/{session_id}/pdf
PDFレポート生成・取得

**Response: 200**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="report_20251128.pdf"

[PDF Binary Data]
```

#### GET /reports/history/{student_id}
生徒の履歴取得

**Query Parameters:**
- `limit` (default: 10)
- `offset` (default: 0)

**Response: 200**
```json
{
  "student": {
    "id": "uuid",
    "name": "山田太郎"
  },
  "sessions": [
    {
      "id": "uuid",
      "date": "2025-11-28",
      "title": "IT企業面接練習 第3回",
      "total_score": 81
    }
  ],
  "statistics": {
    "total_sessions": 5,
    "avg_score": 78,
    "improvement_rate": 8.5
  },
  "score_trend": [
    {"date": "2025-11-01", "score": 70},
    {"date": "2025-11-10", "score": 75},
    {"date": "2025-11-20", "score": 75},
    {"date": "2025-11-28", "score": 81}
  ]
}
```

---

### 質問管理 (Questions)

#### GET /questions
質問一覧取得

**Query Parameters:**
- `category` (optional): 志望動機, 自己PR, 学生時代の経験
- `industry` (optional): IT, 金融, 製造
- `difficulty` (optional): basic, intermediate, advanced

**Response: 200**
```json
{
  "questions": [
    {
      "id": "uuid",
      "category": "志望動機",
      "question_text": "当社を志望した理由を教えてください。",
      "difficulty": "basic",
      "frequency": 100
    }
  ]
}
```

#### POST /questions/generate
生徒プロフィールから質問生成

**Request:**
```json
{
  "student_id": "uuid",
  "count": 5,
  "categories": ["志望動機", "自己PR"]
}
```

**Response: 200**
```json
{
  "questions": [
    "バスケットボール部での経験を、IT業界でどう活かせますか？",
    "キャプテンとして最も苦労したことは何ですか？",
    "エンジニアとして働く上で、あなたの強みは何ですか？"
  ]
}
```

---

## エラーレスポンス

### 共通エラー形式
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    }
  }
}
```

### エラーコード一覧

| HTTPステータス | コード | 説明 |
|--------------|--------|------|
| 400 | VALIDATION_ERROR | 入力検証エラー |
| 401 | UNAUTHORIZED | 認証エラー |
| 403 | FORBIDDEN | 権限エラー |
| 404 | NOT_FOUND | リソースが見つからない |
| 409 | CONFLICT | リソース競合 |
| 422 | UNPROCESSABLE_ENTITY | 処理不可能 |
| 429 | RATE_LIMIT_EXCEEDED | レート制限超過 |
| 500 | INTERNAL_SERVER_ERROR | サーバーエラー |
| 503 | SERVICE_UNAVAILABLE | サービス利用不可 |

---

## レート制限

- **一般エンドポイント**: 60 req/min
- **分析エンドポイント**: 10 req/min
- **アップロード**: 5 req/min

レート制限超過時のレスポンス:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "retry_after": 60
  }
}
```

---

## Webhooks (将来実装)

### POST /webhooks/session-completed
セッション完了時のWebhook

**Payload:**
```json
{
  "event": "session.completed",
  "session_id": "uuid",
  "timestamp": "2025-11-29T10:00:00Z"
}
```
