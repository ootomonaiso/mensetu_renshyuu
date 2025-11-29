# データベース設計書

**更新日**: 2025年11月29日

---

## ER図

```
users (Supabase Auth)
  ↓
  ├─ student_profiles
  │   └─ interview_sessions
  │       ├─ evaluations
  │       ├─ session_feedback
  │       └─ audio_analysis
  │
  └─ teacher_profiles

question_templates
feedback_templates
keigo_patterns
```

---

## テーブル定義

### 1. users (Supabase Auth管理)
```sql
-- Supabase Authが自動管理
-- 以下のカラムを使用
id: UUID (PRIMARY KEY)
email: TEXT
created_at: TIMESTAMP
```

### 2. user_profiles
ユーザーの追加情報
```sql
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('teacher', 'student', 'admin')),
  name TEXT NOT NULL,
  school_name TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(user_id)
);

-- RLS (Row Level Security)
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- ポリシー: 自分のプロフィールは読み書き可能
CREATE POLICY "Users can read own profile"
  ON user_profiles FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update own profile"
  ON user_profiles FOR UPDATE
  USING (auth.uid() = user_id);
```

### 3. student_profiles
生徒の詳細情報
```sql
CREATE TABLE student_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  grade TEXT,  -- 学年: '高1', '高2', '高3', '大1'等
  class_name TEXT,  -- クラス: '1-A'
  target_industry TEXT,  -- 志望業界
  target_company TEXT,  -- 志望企業
  target_position TEXT,  -- 志望職種
  club_activity TEXT,  -- 部活動
  achievements JSONB,  -- 実績 [{title, description, date}]
  certifications JSONB,  -- 資格 [{name, date, score}]
  strengths TEXT[],  -- 強み
  weaknesses TEXT[],  -- 弱み
  notes TEXT,  -- 備考
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(user_id)
);

-- インデックス
CREATE INDEX idx_student_profiles_user_id ON student_profiles(user_id);
CREATE INDEX idx_student_profiles_grade ON student_profiles(grade);

-- RLS
ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Students can read own profile"
  ON student_profiles FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Teachers can read all student profiles"
  ON student_profiles FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM user_profiles
      WHERE user_id = auth.uid() AND role = 'teacher'
    )
  );
```

### 4. teacher_profiles
教師の詳細情報
```sql
CREATE TABLE teacher_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  department TEXT,  -- 担当部署: '進路指導部'
  specialization TEXT[],  -- 専門分野
  assigned_grades TEXT[],  -- 担当学年
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(user_id)
);

-- RLS
ALTER TABLE teacher_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Teachers can read own profile"
  ON teacher_profiles FOR SELECT
  USING (auth.uid() = user_id);
```

### 5. interview_sessions
面接セッション
```sql
CREATE TABLE interview_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  teacher_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  
  -- 基本情報
  title TEXT NOT NULL,  -- 'IT企業面接練習 第3回'
  session_type TEXT NOT NULL CHECK (session_type IN ('practice', 'mock', 'real')),
  target_company TEXT,
  target_position TEXT,
  
  -- 音声データ
  audio_url TEXT,  -- Supabase Storage URL
  audio_duration INTEGER,  -- 秒
  
  -- 文字起こし
  transcript TEXT,
  transcript_with_timestamps JSONB,  -- [{start, end, speaker, text}]
  
  -- ステータス
  status TEXT NOT NULL DEFAULT 'recording' 
    CHECK (status IN ('recording', 'processing', 'completed', 'failed')),
  
  -- タイムスタンプ
  started_at TIMESTAMP,
  ended_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- インデックス
CREATE INDEX idx_sessions_student_id ON interview_sessions(student_id);
CREATE INDEX idx_sessions_teacher_id ON interview_sessions(teacher_id);
CREATE INDEX idx_sessions_status ON interview_sessions(status);
CREATE INDEX idx_sessions_created_at ON interview_sessions(created_at DESC);

-- RLS
ALTER TABLE interview_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Students can read own sessions"
  ON interview_sessions FOR SELECT
  USING (auth.uid() = student_id);

CREATE POLICY "Teachers can read all sessions"
  ON interview_sessions FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM user_profiles
      WHERE user_id = auth.uid() AND role = 'teacher'
    )
  );
```

### 6. audio_analysis
音響分析結果
```sql
CREATE TABLE audio_analysis (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
  
  -- 話速
  avg_speech_rate FLOAT,  -- wpm (words per minute)
  speech_rate_timeline JSONB,  -- [{time, rate}]
  
  -- 音量
  avg_volume_db FLOAT,
  volume_timeline JSONB,  -- [{time, db}]
  
  -- ピッチ
  avg_pitch_hz FLOAT,
  pitch_variation FLOAT,  -- 標準偏差
  pitch_timeline JSONB,  -- [{time, hz}]
  
  -- 間・ポーズ
  pause_count INTEGER,
  avg_pause_duration FLOAT,  -- 秒
  pause_timeline JSONB,  -- [{start, end, duration}]
  
  -- フィラー
  filler_count INTEGER,
  filler_details JSONB,  -- [{word, count, timestamps}]
  
  -- 感情推定 (音声ベース)
  emotion_scores JSONB,  -- {confident: 0.7, nervous: 0.3, ...}
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- インデックス
CREATE INDEX idx_audio_analysis_session_id ON audio_analysis(session_id);

-- RLS
ALTER TABLE audio_analysis ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read analysis for their sessions"
  ON audio_analysis FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM interview_sessions
      WHERE id = session_id 
      AND (student_id = auth.uid() OR teacher_id = auth.uid())
    )
  );
```

### 7. evaluations
総合評価
```sql
CREATE TABLE evaluations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
  
  -- 評価スコア (0-100)
  appearance_score INTEGER CHECK (appearance_score >= 0 AND appearance_score <= 100),
  speech_clarity_score INTEGER CHECK (speech_clarity_score >= 0 AND speech_clarity_score <= 100),
  keigo_score INTEGER CHECK (keigo_score >= 0 AND keigo_score <= 100),
  content_relevance_score INTEGER CHECK (content_relevance_score >= 0 AND content_relevance_score <= 100),
  logic_score INTEGER CHECK (logic_score >= 0 AND logic_score <= 100),
  enthusiasm_score INTEGER CHECK (enthusiasm_score >= 0 AND enthusiasm_score <= 100),
  
  -- 総合スコア
  total_score INTEGER CHECK (total_score >= 0 AND total_score <= 100),
  
  -- 詳細評価
  strengths TEXT[],  -- 良かった点
  improvements TEXT[],  -- 改善点
  
  -- キーワード分析 (Gemini API)
  extracted_keywords JSONB,  -- [{keyword, relevance, context}]
  topic_categories TEXT[],  -- ['志望動機', '自己PR', '学生時代の経験']
  
  -- 敬語分析 (Gemini API)
  keigo_analysis JSONB,  -- {score, errors: [{text, position, issue, suggestion, severity, explanation}], strengths: []}
  
  -- 感情分析 (Gemini API - 文字起こしテキストから)
  sentiment_analysis JSONB,  -- {overall: 'positive', confidence: 0.8, emotions: {confident: 0.7, nervous: 0.3}, timeline: [{time, emotion, intensity}]}
  
  -- 音声ベース感情 (librosaから)
  voice_emotion_scores JSONB  -- {confident: 0.6, nervous: 0.4} - 音響特徴から推定
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- インデックス
CREATE INDEX idx_evaluations_session_id ON evaluations(session_id);

-- RLS
ALTER TABLE evaluations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read evaluations for their sessions"
  ON evaluations FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM interview_sessions
      WHERE id = session_id 
      AND (student_id = auth.uid() OR teacher_id = auth.uid())
    )
  );
```

### 8. session_feedback
教師・AIからのフィードバック
```sql
CREATE TABLE session_feedback (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
  
  -- フィードバック種別
  feedback_type TEXT NOT NULL CHECK (feedback_type IN ('ai_generated', 'teacher_manual')),
  created_by UUID REFERENCES auth.users(id),  -- 教師の場合
  
  -- フィードバック内容
  summary TEXT,  -- 総評
  good_points TEXT[],  -- 良かった点
  improvement_points TEXT[],  -- 改善点
  specific_advice TEXT,  -- 具体的アドバイス
  practice_tasks TEXT[],  -- 次回までの練習課題
  
  -- タイムスタンプ付きコメント
  timestamped_comments JSONB,  -- [{timestamp, comment, type}]
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- インデックス
CREATE INDEX idx_feedback_session_id ON session_feedback(session_id);

-- RLS
ALTER TABLE session_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read feedback for their sessions"
  ON session_feedback FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM interview_sessions
      WHERE id = session_id 
      AND (student_id = auth.uid() OR teacher_id = auth.uid())
    )
  );
```

### 9. question_templates
質問テンプレート
```sql
CREATE TABLE question_templates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  -- 分類
  category TEXT NOT NULL,  -- '志望動機', '自己PR', '学生時代の経験'
  industry TEXT,  -- 業界: 'IT', '金融', '製造'
  position TEXT,  -- 職種: '営業', 'エンジニア'
  difficulty TEXT CHECK (difficulty IN ('basic', 'intermediate', 'advanced')),
  
  -- 質問内容
  question_text TEXT NOT NULL,
  question_template TEXT,  -- テンプレート変数: '{club}での経験を...'
  
  -- メタ情報
  frequency INTEGER DEFAULT 0,  -- 使用頻度
  is_active BOOLEAN DEFAULT true,
  tags TEXT[],
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- インデックス
CREATE INDEX idx_questions_category ON question_templates(category);
CREATE INDEX idx_questions_industry ON question_templates(industry);
CREATE INDEX idx_questions_is_active ON question_templates(is_active);

-- サンプルデータ
INSERT INTO question_templates (category, question_text, frequency) VALUES
  ('志望動機', '当社を志望した理由を教えてください。', 100),
  ('自己PR', 'あなたの強みを教えてください。', 95),
  ('学生時代の経験', '学生時代に最も力を入れたことは何ですか？', 90),
  ('チームワーク', 'チームで協力して成果を出した経験を教えてください。', 80);
```

### 10. feedback_templates
フィードバックテンプレート
```sql
CREATE TABLE feedback_templates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  -- 評価項目
  category TEXT NOT NULL,  -- 'speech_rate', 'volume', 'keigo', 'filler'
  
  -- 条件
  condition_type TEXT NOT NULL,  -- 'too_fast', 'too_slow', 'too_high', 'too_low'
  min_value FLOAT,
  max_value FLOAT,
  
  -- フィードバックテンプレート
  feedback_text TEXT NOT NULL,  -- '{value}wpmで少し速いです。理想は{ideal_min}-{ideal_max}wpmです。'
  advice TEXT,  -- 具体的アドバイス
  
  -- 理想値
  ideal_min FLOAT,
  ideal_max FLOAT,
  
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- サンプルデータ
INSERT INTO feedback_templates (category, condition_type, min_value, feedback_text, ideal_min, ideal_max) VALUES
  ('speech_rate', 'too_fast', 180, '話速が{value}wpmで少し速いです。理想は{ideal_min}-{ideal_max}wpmです。落ち着いて、一文ごとに区切りを意識しましょう。', 150, 180),
  ('speech_rate', 'too_slow', NULL, '話速が{value}wpmで少し遅いです。理想は{ideal_min}-{ideal_max}wpmです。もう少しテンポを上げましょう。', 150, 180),
  ('filler', 'too_high', 10, 'フィラー語が{value}回検出されました。深呼吸して落ち着いて話すことを心がけましょう。', 0, 5),
  ('volume', 'too_low', NULL, '声量が{value}dBで小さいです。理想は{ideal_min}-{ideal_max}dBです。もう少し大きな声で話しましょう。', 60, 75);
```

### 11. ai_analysis_cache
AI分析結果キャッシュ（コスト削減用）
```sql
CREATE TABLE ai_analysis_cache (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  -- キャッシュキー
  cache_key TEXT NOT NULL,  -- MD5(text + analysis_type)
  analysis_type TEXT NOT NULL CHECK (analysis_type IN ('keigo', 'sentiment', 'keywords')),
  
  -- 入力
  input_text TEXT NOT NULL,
  input_hash TEXT NOT NULL,  -- MD5ハッシュ
  
  -- 結果
  result JSONB NOT NULL,
  
  -- メタ情報
  model_version TEXT,  -- 'gemini-1.5-flash'
  hit_count INTEGER DEFAULT 0,
  
  created_at TIMESTAMP DEFAULT NOW(),
  last_used_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,  -- TTL: 30日
  
  UNIQUE(cache_key)
);

-- インデックス
CREATE INDEX idx_ai_cache_key ON ai_analysis_cache(cache_key);
CREATE INDEX idx_ai_cache_type ON ai_analysis_cache(analysis_type);
CREATE INDEX idx_ai_cache_expires ON ai_analysis_cache(expires_at);

-- 自動削除トリガー（期限切れキャッシュ）
CREATE OR REPLACE FUNCTION delete_expired_cache()
RETURNS void AS $$
BEGIN
  DELETE FROM ai_analysis_cache WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;
```

---

## マイグレーション実行順序

1. `user_profiles`
2. `student_profiles`
3. `teacher_profiles`
4. `interview_sessions`
5. `audio_analysis`
6. `evaluations`
7. `session_feedback`
8. `question_templates`
9. `feedback_templates`
10. `ai_analysis_cache`

---

## Supabase Storage バケット

### audio-files
```javascript
// 公開: false (認証必要)
// パス構造: {user_id}/{session_id}/audio.wav
// 許可サイズ: 最大100MB
// 許可形式: audio/wav, audio/mp3, audio/webm
```

### reports
```javascript
// 公開: false
// パス構造: {user_id}/{session_id}/report.pdf
// 許可サイズ: 最大10MB
// 許可形式: application/pdf
```

---

## インデックス戦略

### 頻繁に検索されるカラム
- `student_profiles.user_id`
- `interview_sessions.student_id`
- `interview_sessions.created_at` (DESC)
- `interview_sessions.status`

### 複合インデックス (将来的に検討)
```sql
CREATE INDEX idx_sessions_student_date 
  ON interview_sessions(student_id, created_at DESC);
```

---

## データ保持期間

- **アクティブセッション**: 無期限
- **音声ファイル**: 1年 (自動アーカイブ)
- **分析結果**: 無期限
- **ログ**: 3ヶ月
