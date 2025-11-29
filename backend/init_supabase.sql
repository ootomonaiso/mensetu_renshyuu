-- =====================================
-- 圧勝面接練習 - Supabase データベース初期化
-- =====================================
-- 実行方法: Supabase SQL Editor で実行
-- 注意: RLS (Row Level Security) を有効化しています

-- UUID拡張を有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================
-- 1. user_profiles (ユーザー基本情報)
-- =====================================
CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('teacher', 'student', 'admin')),
  name TEXT NOT NULL,
  school_name TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(user_id)
);

-- RLS設定
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can read own profile" ON user_profiles;
CREATE POLICY "Users can read own profile"
  ON user_profiles FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own profile" ON user_profiles;
CREATE POLICY "Users can update own profile"
  ON user_profiles FOR UPDATE
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own profile" ON user_profiles;
CREATE POLICY "Users can insert own profile"
  ON user_profiles FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- =====================================
-- 2. student_profiles (生徒詳細情報)
-- =====================================
CREATE TABLE IF NOT EXISTS student_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  grade TEXT,
  class_name TEXT,
  target_industry TEXT,
  target_company TEXT,
  target_position TEXT,
  club_activity TEXT,
  achievements JSONB,
  certifications JSONB,
  strengths TEXT[],
  weaknesses TEXT[],
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_student_profiles_user_id ON student_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_student_profiles_grade ON student_profiles(grade);

ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Students can read own profile" ON student_profiles;
CREATE POLICY "Students can read own profile"
  ON student_profiles FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Students can update own profile" ON student_profiles;
CREATE POLICY "Students can update own profile"
  ON student_profiles FOR UPDATE
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Students can insert own profile" ON student_profiles;
CREATE POLICY "Students can insert own profile"
  ON student_profiles FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Teachers can read all student profiles" ON student_profiles;
CREATE POLICY "Teachers can read all student profiles"
  ON student_profiles FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM user_profiles
      WHERE user_id = auth.uid() AND role IN ('teacher', 'admin')
    )
  );

-- =====================================
-- 3. interview_sessions (面接セッション)
-- =====================================
CREATE TABLE IF NOT EXISTS interview_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  teacher_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  
  title TEXT NOT NULL,
  session_type TEXT NOT NULL CHECK (session_type IN ('practice', 'mock', 'real')),
  target_company TEXT,
  target_position TEXT,
  
  audio_url TEXT,
  audio_duration INTEGER,
  
  transcript TEXT,
  transcript_with_timestamps JSONB,
  
  status TEXT NOT NULL DEFAULT 'recording' 
    CHECK (status IN ('recording', 'processing', 'completed', 'failed')),
  
  started_at TIMESTAMP,
  ended_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_student_id ON interview_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_sessions_teacher_id ON interview_sessions(teacher_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON interview_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON interview_sessions(created_at DESC);

ALTER TABLE interview_sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Students can read own sessions" ON interview_sessions;
CREATE POLICY "Students can read own sessions"
  ON interview_sessions FOR SELECT
  USING (auth.uid() = student_id);

DROP POLICY IF EXISTS "Students can create own sessions" ON interview_sessions;
CREATE POLICY "Students can create own sessions"
  ON interview_sessions FOR INSERT
  WITH CHECK (auth.uid() = student_id);

DROP POLICY IF EXISTS "Students can update own sessions" ON interview_sessions;
CREATE POLICY "Students can update own sessions"
  ON interview_sessions FOR UPDATE
  USING (auth.uid() = student_id);

DROP POLICY IF EXISTS "Students can delete own sessions" ON interview_sessions;
CREATE POLICY "Students can delete own sessions"
  ON interview_sessions FOR DELETE
  USING (auth.uid() = student_id);

DROP POLICY IF EXISTS "Teachers can read all sessions" ON interview_sessions;
CREATE POLICY "Teachers can read all sessions"
  ON interview_sessions FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM user_profiles
      WHERE user_id = auth.uid() AND role IN ('teacher', 'admin')
    )
  );

DROP POLICY IF EXISTS "Teachers can create sessions" ON interview_sessions;
CREATE POLICY "Teachers can create sessions"
  ON interview_sessions FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_profiles
      WHERE user_id = auth.uid() AND role IN ('teacher', 'admin')
    )
  );

DROP POLICY IF EXISTS "Teachers can update all sessions" ON interview_sessions;
CREATE POLICY "Teachers can update all sessions"
  ON interview_sessions FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM user_profiles
      WHERE user_id = auth.uid() AND role IN ('teacher', 'admin')
    )
  );

DROP POLICY IF EXISTS "Teachers can delete sessions" ON interview_sessions;
CREATE POLICY "Teachers can delete sessions"
  ON interview_sessions FOR DELETE
  USING (
    auth.uid() = teacher_id OR
    EXISTS (
      SELECT 1 FROM user_profiles
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );

-- =====================================
-- 4. audio_analysis (音響分析)
-- =====================================
CREATE TABLE IF NOT EXISTS audio_analysis (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
  
  avg_speech_rate FLOAT,
  speech_rate_timeline JSONB,
  
  avg_volume_db FLOAT,
  volume_timeline JSONB,
  
  avg_pitch_hz FLOAT,
  pitch_variation FLOAT,
  pitch_timeline JSONB,
  
  pause_count INTEGER,
  avg_pause_duration FLOAT,
  pause_timeline JSONB,
  
  filler_count INTEGER,
  filler_details JSONB,
  
  emotion_scores JSONB,
  
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audio_analysis_session_id ON audio_analysis(session_id);

ALTER TABLE audio_analysis ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can read analysis for their sessions" ON audio_analysis;
CREATE POLICY "Users can read analysis for their sessions"
  ON audio_analysis FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM interview_sessions
      WHERE id = session_id 
      AND (student_id = auth.uid() OR teacher_id = auth.uid())
    )
  );

-- =====================================
-- 5. evaluations (評価・分析結果)
-- =====================================
CREATE TABLE IF NOT EXISTS evaluations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
  
  appearance_score INTEGER CHECK (appearance_score >= 0 AND appearance_score <= 100),
  speech_clarity_score INTEGER CHECK (speech_clarity_score >= 0 AND speech_clarity_score <= 100),
  keigo_score INTEGER CHECK (keigo_score >= 0 AND keigo_score <= 100),
  content_relevance_score INTEGER CHECK (content_relevance_score >= 0 AND content_relevance_score <= 100),
  logic_score INTEGER CHECK (logic_score >= 0 AND logic_score <= 100),
  enthusiasm_score INTEGER CHECK (enthusiasm_score >= 0 AND enthusiasm_score <= 100),
  
  total_score INTEGER CHECK (total_score >= 0 AND total_score <= 100),
  
  strengths TEXT[],
  improvements TEXT[],
  
  extracted_keywords JSONB,
  topic_categories TEXT[],
  
  keigo_analysis JSONB,
  
  sentiment_analysis JSONB,
  
  voice_emotion_scores JSONB,
  
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evaluations_session_id ON evaluations(session_id);

ALTER TABLE evaluations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can read evaluations for their sessions" ON evaluations;
CREATE POLICY "Users can read evaluations for their sessions"
  ON evaluations FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM interview_sessions
      WHERE id = session_id 
      AND (student_id = auth.uid() OR teacher_id = auth.uid())
    )
  );

-- =====================================
-- 6. ai_analysis_cache (Gemini APIキャッシュ)
-- =====================================
CREATE TABLE IF NOT EXISTS ai_analysis_cache (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  analysis_type TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  result JSONB NOT NULL,
  model_version TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  
  UNIQUE(analysis_type, input_hash)
);

CREATE INDEX IF NOT EXISTS idx_ai_cache_type_hash ON ai_analysis_cache(analysis_type, input_hash);
CREATE INDEX IF NOT EXISTS idx_ai_cache_expires ON ai_analysis_cache(expires_at);

-- AIキャッシュはシステム内部用なのでRLSなし（アプリケーション層で管理）

-- =====================================
-- 完了メッセージ
-- =====================================
DO $$
BEGIN
  RAISE NOTICE '✓ データベーステーブルの作成が完了しました';
  RAISE NOTICE '次のステップ: テストユーザーを作成し、アプリケーションから接続してください';
END $$;
