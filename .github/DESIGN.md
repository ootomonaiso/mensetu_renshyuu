# 圧勝面接 - 総合設計書

**プロジェクト名**: 圧勝面接  
**作成日**: 2025年11月29日  
**バージョン**: 1.0.0

---

## 目次

1. [プロジェクト概要](#1-プロジェクト概要)
2. [システムアーキテクチャ](#2-システムアーキテクチャ)
3. [技術スタック](#3-技術スタック)
4. [機能要件](#4-機能要件)
5. [データベース設計](#5-データベース設計)
6. [API設計](#6-api設計)
7. [AI実装方針](#7-ai実装方針)
8. [開発フェーズ](#8-開発フェーズ)
9. [コスト試算](#9-コスト試算)

---

## 1. プロジェクト概要

### 1.1 目的
学校現場における生徒と教師の面接練習を、AI技術でリアルタイム評価・分析し、客観的なフィードバックを提供するシステム。

**❗ 重要な位置づけ**:  
このシステムはあくまで**教師の指導をサポートするツール**です。  
- AIの分析結果は**参考情報**であり、最終的な評価やフィードバックは**教師が主導**します
- 数値データや客観的指標で教師の気づきを補助します
- 生徒の個性や背景を踏まえた指導は教師の専門性が必須です

### 1.2 ターゲットユーザー
- **主要**: 高校・大学の進路指導担当教師（指導の主体）
- **二次**: 就職・進学を控えた生徒（練習の主体）

**使用シーン**:
1. 教師が生徒と面接練習を実施
2. システムが音声・ビデオを分析し、数値データを提供
3. **教師がデータを参考にしつつ、自身の所見を追加**
4. 教師が生徒に合わせてフィードバックを調整
5. Markdown/PDFレポートを生徒と共有

### 1.3 主要機能
- 音声認識による文字起こし
- 音響分析（話速、声量、ピッチ）
- ビデオ分析（目線、姿勢、表情）
- AI敬語分析（Gemini API）
- AI感情分析（Gemini API + 音声特徴）
- キーワード抽出（Gemini API）
- **Markdownレポート自動生成** → GitHub/ローカル保存
- **PDFレポート出力** → 印刷・共有用
- 履歴管理・成長追跡（データベース保存）

### 1.4 差別化ポイント
- **教師主導のサポートツール**: AIは提案、教師が最終判断
- 完全ローカル音声処理（プライバシー重視）
- AI活用（低コスト）
- 日本語敬語の詳細分析
- **Markdown/PDF共有による柔軟な運用**
  - データベースは分析データの保存・履歴管理用
  - レポートは静的ファイル（.md, .pdf）で管理
  - GitHub保存、メール添付、印刷など多様な共有方法
- **教師が編集・カスタマイズ可能**: AI提案をベースに教師が調整

---

## 2. システムアーキテクチャ

### 2.1 全体構成

```
┌─────────────────────────────────────────────────────────┐
│                    クライアント層                          │
│  [Webブラウザ: React + TypeScript + shadcn/ui]           │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTPS
                   ↓
┌─────────────────────────────────────────────────────────┐
│                 アプリケーション層                          │
│  [FastAPI サーバー]                                       │
│   - 認証・認可                                            │
│   - ビジネスロジック                                       │
│   - API エンドポイント                                     │
└──┬───────────┬──────────────┬───────────────────────────┘
   │           │              │
   ↓           ↓              ↓
┌─────┐  ┌──────────┐  ┌────────────────┐
│Redis│  │ Celery   │  │  分析処理層     │
│     │  │ Worker   │  │  - Whisper      │
└─────┘  └────┬─────┘  │  - librosa      │
              │         │  - MediaPipe    │
              │         │  - sudachipy    │
              ↓         └────────────────┘
       ┌──────────────┐
       │ 非同期処理    │
       │ - 音声解析   │
       │ - ビデオ解析 │
       │ - MD生成     │
       │ - PDF生成    │
       └──────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────┐
│                    データ層                               │
│  [Supabase]                                              │
│   - PostgreSQL (データベース)                             │
│   - Auth (認証)                                          │
│   - Storage (音声・PDFファイル)                           │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│                  外部サービス                             │
│  [Gemini API]                                            │
│   - キーワード抽出                                        │
│   - 敬語分析                                             │
│   - 感情分析                                             │
└─────────────────────────────────────────────────────────┘
```

### 2.2 データフロー

```
1. 音声/ビデオ録画 → 2. Supabase Storage → 3. Celery Worker
                                               ↓
4. 分析処理（並列実行）
   ├─ Whisper文字起こし
   ├─ librosa音響分析
   └─ MediaPipeビデオ分析（目線・姿勢・表情）
         ↓
5. Gemini API分析（並列実行）
   ├─ キーワード抽出
   ├─ 敬語分析
   ├─ テキスト感情分析
   └─ 受け手印象ベクトル
         ↓
6. 統合評価スコア計算
         ↓
7. データベース保存（履歴管理用）
         ↓
8. レポート生成（並列実行）
   ├─ Markdownファイル生成 → ローカル保存/GitHub保存
   └─ PDFファイル生成 → ダウンロード/メール添付
         ↓
9. クライアントにファイルパス返却
```

---

## 3. 技術スタック

### 3.1 バックエンド

| 技術 | バージョン | 用途 |
|-----|----------|------|
| Python | 3.11+ | メイン言語 |
| FastAPI | 0.104+ | Webフレームワーク |
| Supabase | - | DB/Auth/Storage |
| Celery | 5.3+ | 非同期タスク |
| Redis | 7.0+ | Celeryブローカー |
| faster-whisper | latest | 音声認識 |
| librosa | 0.10+ | 音響分析 |
| sudachipy | 0.6+ | 形態素解析 |
| google-generativeai | latest | Gemini API |
| opencv-python | 4.8+ | ビデオ処理 (Phase 4) |
| mediapipe | 0.10+ | 顔・姿勢検出 (Phase 4) |
| markdown2 | latest | Markdown生成 |
| weasyprint | latest | PDF生成 |
| jinja2 | 3.1+ | レポートテンプレート |

### 3.2 フロントエンド

| 技術 | バージョン | 用途 |
|-----|----------|------|
| React | 18+ | UIフレームワーク |
| TypeScript | 5.0+ | 型安全性 |
| Vite | 5.0+ | ビルドツール |
| shadcn/ui | latest | UIコンポーネント |
| Tailwind CSS | 3.3+ | スタイリング |
| Zustand | 4.4+ | 状態管理 |

### 3.3 インフラ

| 技術 | 用途 |
|-----|------|
| Docker + Docker Compose | コンテナ化 |
| Supabase | マネージドDB・認証・ストレージ |
| GitHub Actions | CI/CD |

---

## 4. 機能要件

### 4.1 Phase 1: MVP (2-3ヶ月)

#### 認証機能
- ユーザー登録・ログイン（Supabase Auth）
- 教師・生徒ロール管理
- プロフィール管理

#### 音声処理
- 音声録音・アップロード
- faster-whisperで文字起こし
- 基本的な音響分析（話速、声量）

#### 評価機能
- シンプルな評価スコア（6項目）
- 教師による手動メモ
- **Markdownレポート自動生成**
  - セッション情報
  - 文字起こし全文
  - 音響分析結果（話速・声量グラフ）
  - スコア表
  - フィードバックコメント
- **PDF出力機能**

#### データ管理
- セッション作成・一覧・詳細（DB保存）
- 生徒プロフィール登録
- **生成ファイル管理**
  - `reports/{student_id}/{session_id}.md`
  - `reports/{student_id}/{session_id}.pdf`

### 4.2 Phase 2: データ連携 (2-3ヶ月)

#### 生徒管理
- 詳細プロフィール（部活、実績、資格）
- 志望先情報管理

#### 履歴機能
- 過去セッション一覧
- スコア推移グラフ
- 成長トレンド分析

#### レポート強化
- **Markdown拡張**
  - Mermaidグラフ埋め込み（スコア推移）
  - 過去セッションとの比較表
  - GitHub Pagesでの公開対応
- **PDF強化**
  - グラフ・チャート画像埋め込み
  - 印刷最適化レイアウト
  - カスタムテンプレート対応
- **共有機能**
  - GitHubリポジトリ自動コミット
  - メール添付送信
  - QRコード生成（レポートURL）

### 4.3 Phase 3: AI高度化 (2-3ヶ月)

#### Gemini API統合
- キーワード自動抽出
- 敬語詳細分析
- 感情分析（テキスト+音声）

#### 詳細分析
- フィラー検出
- ポーズ分析
- イントネーション評価

#### フィードバック生成
- **AI支援フィードバック** (参考情報)
  - AIが提案する改善点
  - 教師が確認・承認してからレポートに反映
- **教師による上書き・追加**
  - AI提案を修正・削除可能
  - 教師独自の所見を追加
  - 生徒個別の背景情報を踏まえたアドバイス
- 質問生成 (次回練習用の提案)

#### レポート高度化
- **AI解説のMarkdown整形**
  - 敬語エラーの詳細説明
  - 受け手印象ベクトルの可視化
  - 改善提案のアクションリスト
- **インタラクティブPDF**
  - 目次・しおり機能
  - ハイパーリンク（関連セクションへのジャンプ）

### 4.4 Phase 4: ビデオ分析 (3-4ヶ月)

#### 視線・姿勢分析
- **目線追跡**: カメラ目線の維持率（MediaPipe Face Mesh）
- **視線の揺れ**: 不自然な視線移動の検出
- **姿勢安定性**: 体の揺れ・前後左右の動きを定量化
- **表情分析**: 笑顔頻度、緊張表情の検出
- **姿勢評価**: 背筋の伸び、前のめり過ぎ、猫背検出

#### ジェスチャー分析
- **手の動き**: 適切なジェスチャー vs 落ち着きのない動き
- **頭の動き**: 頷きの適切さ、首振りの頻度
- **視線の自然さ**: 考える時の視線の動き（自然 vs 不自然）

#### 見た目・身だしなみ（補助機能）
- **服装チェック**: スーツの色、ネクタイの有無（検出のみ、評価は教師）
- **背景チェック**: オンライン面接時の背景適切性
- **照明アドバイス**: 顔の明るさが適切か

#### ビデオ分析レポート
- **Markdownに動画埋め込み**
  - タイムスタンプ付きコメント
  - 重要シーンのスクリーンショット
  - 目線・姿勢のグラフ
- **PDF用の静止画抽出**
  - 良い表情のキャプチャ
  - 姿勢改善前後の比較画像

### 4.5 Phase 5: 高度な機能 (将来)

#### 質問生成・AI模擬面接
- **動的質問生成**: 生徒の回答に応じたAI提案 → 教師が選択
- **AIアバター面接官** (練習用)
  - 教師不在時の自主練習用
  - 最終評価は必ず教師が行う
- **シナリオベース練習**: 教師がシナリオを選択・カスタマイズ

#### 比較・ベンチマーク機能
- **同学年比較**: 匿名化された平均スコア (参考情報)
- **業界別傾向**: 合格者傾向データ (参考情報)
- **成長率ランキング**: モチベーション用

**❗ 注意事項**:
- スコアはあくまで目安であり、絶対的な基準ではありません
- 生徒個々の背景や状況を教師が考慮します
- スコアのみでの評価を避け、定性的な成長も重視

#### モバイル・拡張対応
- **モバイルアプリ**: スマホでの簡易練習モード
- **複数校展開**: マルチテナント対応
- **オフライン対応**: ネットなしでも録音可能

#### GitHub連携強化
- **自動コミット**: セッション終了時にMarkdownを自動プッシュ
- **GitHub Issues連携**: 改善タスクをIssueとして登録
- **GitHub Pages**: 生徒用ポートフォリオサイト自動生成
- **バージョン管理**: 過去のレポートをGit履歴で管理

---

## 5. データベース設計

### 5.1 主要テーブル

#### users (Supabase Auth管理)
```sql
id: UUID (PK)
email: TEXT
created_at: TIMESTAMP
```

#### user_profiles
```sql
id: UUID (PK)
user_id: UUID (FK → auth.users)
role: TEXT (teacher/student/admin)
name: TEXT
school_name: TEXT
created_at, updated_at: TIMESTAMP
```

#### student_profiles
```sql
id: UUID (PK)
user_id: UUID (FK → auth.users)
grade: TEXT
target_industry: TEXT
target_company: TEXT
target_position: TEXT
club_activity: TEXT
achievements: JSONB
certifications: JSONB
strengths: TEXT[]
weaknesses: TEXT[]
```

#### interview_sessions
```sql
id: UUID (PK)
student_id: UUID (FK)
teacher_id: UUID (FK)
title: TEXT
session_type: TEXT (practice/mock/real)
audio_url: TEXT
video_url: TEXT (Phase 4)
audio_duration: INTEGER
transcript: TEXT
transcript_with_timestamps: JSONB
markdown_report_path: TEXT (生成されたMarkdownファイルのパス)
pdf_report_path: TEXT (生成されたPDFファイルのパス)
github_commit_url: TEXT (GitHubにプッシュした場合のURL)
status: TEXT (recording/processing/completed/failed)
started_at, ended_at: TIMESTAMP
```

#### audio_analysis
```sql
id: UUID (PK)
session_id: UUID (FK)
avg_speech_rate: FLOAT (wpm)
speech_rate_timeline: JSONB
avg_volume_db: FLOAT
volume_timeline: JSONB
avg_pitch_hz: FLOAT
pitch_variation: FLOAT
pause_count: INTEGER
filler_count: INTEGER
filler_details: JSONB
emotion_scores: JSONB (音声ベース)
```

#### evaluations
```sql
id: UUID (PK)
session_id: UUID (FK)
appearance_score: INTEGER (0-100)
speech_clarity_score: INTEGER
keigo_score: INTEGER
content_relevance_score: INTEGER
logic_score: INTEGER
enthusiasm_score: INTEGER
total_score: INTEGER
strengths: TEXT[]
improvements: TEXT[]
extracted_keywords: JSONB (Gemini結果)
keigo_analysis: JSONB (Gemini結果)
sentiment_analysis: JSONB (Gemini結果)
voice_emotion_scores: JSONB (librosa結果 - 話者感情)
interviewer_impression: JSONB (Gemini結果 - 受け手印象ベクトル)
impression_gap_analysis: JSONB (話者感情 vs 受け手印象のギャップ)
```

#### session_feedback
```sql
id: UUID (PK)
session_id: UUID (FK)
feedback_type: TEXT (ai_generated/teacher_manual)
created_by: UUID (FK - 教師の場合)
summary: TEXT
good_points: TEXT[]
improvement_points: TEXT[]
specific_advice: TEXT
practice_tasks: TEXT[]
timestamped_comments: JSONB
```

#### ai_analysis_cache
```sql
id: UUID (PK)
cache_key: TEXT (UNIQUE)
analysis_type: TEXT (keigo/sentiment/keywords)
input_text: TEXT
input_hash: TEXT
result: JSONB
model_version: TEXT
hit_count: INTEGER
expires_at: TIMESTAMP (TTL: 30日)
```

#### video_analysis (Phase 4)
```sql
id: UUID (PK)
session_id: UUID (FK)
video_url: TEXT
video_duration: INTEGER
eye_contact_rate: FLOAT (0-100%)
eye_movement_stability: FLOAT
posture_score: FLOAT (0-100)
posture_sway_metrics: JSONB (前後左右の揺れ)
facial_expression_timeline: JSONB (笑顔・緊張の時系列)
gesture_analysis: JSONB (手の動き、頷き)
head_movement_count: INTEGER
background_quality_score: FLOAT (オンライン面接用)
lighting_quality_score: FLOAT
processed_at: TIMESTAMP
```

#### practice_questions (新規)
```sql
id: UUID (PK)
student_id: UUID (FK)
question_text: TEXT
question_category: TEXT (自己PR/志望動機/強み弱み/挫折経験/時事問題)
difficulty: TEXT (easy/medium/hard)
prepared_answer: TEXT (生徒の準備した回答)
practice_count: INTEGER (この質問での練習回数)
avg_score: FLOAT (この質問での平均点)
last_practiced_at: TIMESTAMP
```

### 5.2 ER図概要

```
users (Auth)
  ├─ user_profiles
  ├─ student_profiles
  │   └─ interview_sessions
  │       ├─ audio_analysis
  │       ├─ evaluations
  │       └─ session_feedback
  └─ teacher_profiles
  
question_templates
feedback_templates
ai_analysis_cache
```

---

## 6. API設計

### 6.1 ベースURL
- 開発: `http://localhost:8000/api/v1`
- 本番: `https://api.mensetu-app.example.com/api/v1`

### 6.2 認証
```http
Authorization: Bearer {access_token}
```

### 6.3 主要エンドポイント

#### 認証
- `POST /auth/signup` - ユーザー登録
- `POST /auth/login` - ログイン
- `POST /auth/refresh` - トークンリフレッシュ
- `POST /auth/logout` - ログアウト

#### プロフィール
- `GET /profiles/me` - 自分のプロフィール
- `PUT /profiles/me` - プロフィール更新
- `GET /students/{student_id}` - 生徒情報（教師のみ）

#### セッション
- `POST /sessions` - 新規セッション作成
- `GET /sessions` - セッション一覧
- `GET /sessions/{session_id}` - セッション詳細
- `POST /sessions/{session_id}/audio` - 音声アップロード
- `DELETE /sessions/{session_id}` - セッション削除

#### 分析
- `POST /analyze/transcribe` - 音声文字起こし
- `POST /analyze/acoustic` - 音響分析
- `POST /analyze/voice-emotion` - 音声感情分析（librosa）話者の感情状態
- `POST /analyze/impression` - 受け手印象分析（Gemini）面接官視点の印象ベクトル
- `POST /analyze/keywords` - キーワード抽出（Gemini）
- `POST /analyze/keigo` - 敬語分析（Gemini）
- `POST /analyze/sentiment` - テキスト感情分析（Gemini）
- `POST /analyze/comprehensive` - 統合分析（音声感情 + 受け手印象 + ギャップ検出）

#### 評価・フィードバック
- `POST /evaluations` - 評価作成
- `GET /evaluations/{evaluation_id}` - 評価詳細
- `POST /feedback` - フィードバック作成
- `GET /feedback/{session_id}` - フィードバック取得

#### レポート
- `GET /reports/{session_id}` - レポート取得（JSON）
- `POST /reports/{session_id}/markdown` - Markdownレポート生成
  - Response: `{"file_path": "reports/student123/session456.md", "content": "..."}`
- `POST /reports/{session_id}/pdf` - PDFレポート生成
  - Response: `{"file_path": "reports/student123/session456.pdf", "download_url": "..."}`
- `GET /reports/{session_id}/download` - ファイルダウンロード（MD or PDF）
- `POST /reports/{session_id}/github-push` - GitHubへ自動プッシュ
  - Response: `{"commit_url": "https://github.com/.../commit/abc123"}`
- `GET /reports/history/{student_id}` - 履歴取得（ファイルパス含む）

#### 質問管理
- `GET /questions` - 質問一覧
- `POST /questions/generate` - AI質問生成（生徒情報・志望先に基づく）
- `POST /questions/custom` - カスタム質問作成
- `GET /questions/weak-areas` - 苦手分野の質問取得
- `POST /questions/answer` - 準備回答の保存

#### ビデオ分析 (Phase 4)
- `POST /video/upload` - ビデオアップロード
- `POST /video/analyze/eye-contact` - 目線分析
- `POST /video/analyze/posture` - 姿勢分析
- `POST /video/analyze/expression` - 表情分析
- `POST /video/analyze/comprehensive` - 統合ビデオ分析

#### 比較・統計 (Phase 5)
- `GET /stats/peer-comparison` - 同学年比較
- `GET /stats/growth-rate` - 成長率分析
- `GET /stats/industry-trends` - 業界別傾向

#### AI模擬面接 (Phase 5)
- `POST /mock-interview/start` - 模擬面接開始
- `POST /mock-interview/answer` - 回答送信 → AI追加質問生成
- `POST /mock-interview/end` - 模擬面接終了・評価取得

---

## 7. AI実装方針

### ❗ 基本考え方: AIは「提案」、教師が「判断」

1. **AIの分析結果は参考情報**
   - 敬語エラー検出 → 教師が文脈を踏まえて判断
   - 感情分析 → 教師が生徒の特性を踏まえて解釈
   - スコア → 教師が調整・上書き可能

2. **教師が自由に編集可能**
   - MarkdownレポートはPlaintextなので編集容易
   - AI提案を削除、追加、修正できる
   - 教師のコメント欄を必ず用意

3. **数値と定性のバランス**
   - 話速・声量などは客観的数値
   - 熱意・誠実さはAIが提案、教師が最終評価
   - 生徒の背景・状況は教師だけが知る

### 7.1 Gemini API活用

#### キーワード抽出
- 面接文字起こしから重要キーワード抽出
- 関連性スコア付与
- コンテキスト分類（志望動機/自己PR/経験）

#### 敬語分析
- タメ口・俗語検出
- 二重敬語・不自然な表現検出
- 正しい表現の提案 + 詳細説明

#### 感情分析
- テキストから感情推定（ポジティブ/ネガティブ/熱意/緊張）
- 時系列での感情変化追跡
- 感情を示すキーフレーズ抽出

### 7.2 音声感情分析（librosa）

**話者の感情状態検出**:
- 話速（wpm）測定 → 緊張度・自信度
- 声量（dB）測定 → 積極性・エネルギー
- ピッチ（Hz）・変動分析 → 感情の起伏・緊張
- ポーズ・間の検出 → 思考の整理・不安
- フィラー語検出 → 準備不足・緊張

**出力ベクトル** (0-100):
```json
{
  "confidence": 75,      // 自信度
  "calmness": 60,        // 落ち着き
  "energy": 80,          // エネルギー・熱意
  "nervousness": 40,     // 緊張度
  "stability": 70        // 安定性
}
```

### 7.3 受け手印象ベクトル（Gemini）

**面接官視点での印象評価**:

発言内容（文字起こし）から、面接官が受ける印象を多次元ベクトルで定量化:

```json
{
  "professionalism": 85,      // 専門性・真剣さ
  "enthusiasm": 90,           // 熱意・意欲
  "clarity": 75,              // 明瞭さ・分かりやすさ
  "sincerity": 80,            // 誠実さ・正直さ
  "maturity": 70,             // 成熟度・落ち着き
  "positivity": 85,           // ポジティブさ・前向きさ
  "logic": 65,                // 論理性・一貫性
  "confidence_perceived": 75  // 自信があるように見えるか
}
```

**分析内容**:
- 言葉選び（謙虚さ vs 傲慢さ）
- 具体性（抽象的 vs 具体例あり）
- 自己認識（強み・弱みの理解）
- 企業理解度（リサーチの深さ）
- 将来ビジョン（明確 vs 曖昧）

### 7.4 統合分析

**多層評価システム**:

```
話者感情（librosa音声分析）
  ↓
├─ 自信度: 75
├─ 緊張度: 40  
└─ エネルギー: 80

受け手印象（Geminiテキスト分析）
  ↓
├─ 熱意: 90
├─ 誠実さ: 80
└─ 論理性: 65

        ↓
   総合評価スコア
```

**ギャップ検出**:
- 話者は自信があるつもりだが、声に緊張が現れている
- 熱意は伝わるが、論理的な説明が不足
- 落ち着いた声だが、内容が抽象的で印象が弱い

### 7.5 コスト最適化

- **キャッシュ**: 同じテキストは30日間再利用（キーワード・敬語・受け手印象）
- **無料枠**: Gemini API 1500 requests/day
  - 1セッションあたり: 3-4 API calls（キーワード・敬語・受け手印象・感情）
  - 1日あたり: 約375セッション分析可能
- **フォールバック**: API制限時はルールベース
- **音声分析**: 完全ローカル（librosa）でAPI費用なし

---

## 6A. Markdown/PDFレポート詳細

### 6A.1 Markdownレポート構造

```markdown
# 面接練習レポート

**生徒名**: 山田太郎  
**日時**: 2025年11月29日 14:30  
**セッションID**: abc123  
**面接種別**: 模擬面接（志望動機）

---

## 📊 総合評価

| 項目 | スコア | 前回比 |
|-----|-------|-------|
| 身だしなみ | 85 | +5 |
| 話し方の明瞭さ | 78 | +2 |
| 敬語使用 | 72 | +8 |
| 内容の適切性 | 80 | +3 |
| 論理性 | 75 | +1 |
| 熱意 | 90 | +7 |
| **総合** | **80** | **+4** |

## 🎤 音声分析

### 話速
- 平均: 320 wpm (適切: 280-350 wpm)
- 評価: ✅ 適切な話速です

### 声量
- 平均: -18 dB
- 評価: ✅ 聞き取りやすい声量です

### フィラー語
- 「えー」: 15回 (前回: 22回)
- 「あの」: 8回 (前回: 12回)
- 改善率: 31%改善 👍

## 🎥 ビデオ分析 (Phase 4)

### 目線
- カメラ目線維持率: 75.5%
- 評価: ✅ 良好

### 姿勢
- 安定性スコア: 82/100
- 左右の揺れ: 3.2cm (少し気になる)
- 改善点: 意識的に体を安定させましょう

## 💬 文字起こし

```
[00:00] 本日はお時間いただきありがとうございます。
[00:05] 私は貴社のAI事業に強く興味を持っており...
[00:45] 大学時代には、えー、機械学習のプロジェクトで...
         ^^^ フィラー語
```

## 🎯 AI分析結果

### キーワード
- 「AI事業」(3回)
- 「機械学習」(2回)
- 「チーム開発」(2回)

### 敬語分析
| 位置 | 問題 | 提案 | 重要度 |
|-----|------|------|--------|
| 0:45 | 「やってました」 | 「取り組んでおりました」 | 中 |
| 2:30 | 「すごく」 | 「非常に」 | 低 |

### 受け手印象ベクトル
```mermaid
radar
  title 面接官が受ける印象
  polarArea
  専門性: 85
  熱意: 90
  明瞭さ: 75
  誠実さ: 80
  成熟度: 70
  論理性: 65
```

## ✅ 良かった点
- 熱意が非常に伝わる回答でした
- フィラー語が前回から31%改善
- 具体的な数値を入れて説明できています

## 📝 改善点
- 「やってました」→「取り組んでおりました」など敬語の精度向上
- もう少し論理的な構成を意識（結論→理由→具体例）
- 体の揺れを減らす（椅子の高さ調整推奨）

## 👩‍🏫 教師の所見

> **ここに教師のコメントを追加してください**
> 
> - 生徒の背景や状況を踏まえた所見
> - AI分析と異なる視点
> - 個別のアドバイス

## 🎯 次回の練習課題
1. 敬語表現リストを事前に確認
2. PREP法で回答を構成してみる
3. 鏡の前で姿勢を確認しながら練習

---

**生成日時**: 2025-11-29 15:00  
**次回セッション予定**: 2025-12-06 14:00
```

### 6A.2 PDFレポート特徴

- **印刷最適化**: A4サイズ、余白調整
- **グラフ埋め込み**: 話速・声量のグラフを画像化
- **カラーコード**: スコアを色分け（緑=良好、黄=要改善、赤=要対策）
- **目次・しおり**: 長いレポートでもナビゲーション容易
- **ヘッダー/フッター**: ページ番号、生徒名、日付

### 6A.3 ファイル管理構造

```
reports/
├── student_abc123/
│   ├── 2025-11-20_session001.md
│   ├── 2025-11-20_session001.pdf
│   ├── 2025-11-25_session002.md
│   ├── 2025-11-25_session002.pdf
│   ├── 2025-11-29_session003.md
│   ├── 2025-11-29_session003.pdf
│   └── assets/
│       ├── session001_speech_rate.png
│       ├── session001_volume.png
│       └── session003_posture.png
└── student_def456/
    └── ...
```

### 6A.4 GitHub連携フロー

```
1. セッション完了
     ↓
2. Markdown生成 → ローカル保存
     ↓
3. Git操作（オプション）
     ├─ git add reports/student_abc123/2025-11-29_session003.md
     ├─ git commit -m "Add session report for 山田太郎 (2025-11-29)"
     └─ git push origin main
     ↓
4. commit URLをDBに保存
     ↓
5. GitHub Pages自動デプロイ（設定している場合）
     → https://username.github.io/mensetu_renshyuu/reports/student_abc123/
```

### 6A.5 共有方法

#### 方法1: ローカルファイル共有
- 教師が生徒にUSBメモリで渡す
- ネットワークドライブ経由

#### 方法2: メール送信
- PDFを自動添付してメール送信
- Markdownファイルも添付（編集可能）

#### 方法3: GitHub共有
- プライベートリポジトリで生徒に招待
- 履歴管理、差分確認が容易

#### 方法4: QRコード
- GitHub PagesのURLをQRコード化
- スマホでスキャン→即座に閲覧

---

## 7A. 追加機能詳細

### 7A.1 ビデオ分析（Phase 4）

#### 目線分析
```python
# MediaPipe Face Meshを使用
{
  "eye_contact_rate": 75.5,  # カメラ目線の割合
  "gaze_stability": 82.0,    # 視線の安定性
  "look_away_count": 12,     # 視線を外した回数
  "avg_look_away_duration": 1.5,  # 平均逸らし時間（秒）
  "gaze_pattern": "natural",  # natural/nervous/distracted
  "timeline": [
    {"time": "0:15", "status": "direct"},
    {"time": "0:45", "status": "away", "duration": 2.0}
  ]
}
```

#### 姿勢・揺れ分析
```python
# MediaPipe Poseを使用
{
  "posture_score": 85.0,
  "sway_metrics": {
    "horizontal_sway": 3.2,  # cm単位の左右の揺れ
    "vertical_sway": 1.5,    # 前後の揺れ
    "rotation": 5.0          # 回転の揺れ（度）
  },
  "posture_issues": [
    {"type": "slouching", "severity": "mild", "timestamp": "2:30"},
    {"type": "leaning_forward", "severity": "moderate", "timestamp": "5:15"}
  ],
  "stability_rating": "good"  # excellent/good/fair/poor
}
```

#### 表情分析
```python
{
  "smile_frequency": 15,        # 笑顔の回数
  "smile_duration_avg": 2.5,    # 平均笑顔持続時間（秒）
  "tension_indicators": 8,      # 緊張表情の検出回数
  "expression_variety": 6.5,    # 表情の豊かさスコア
  "neutral_time_ratio": 0.65,   # 無表情の時間割合
  "emotions_detected": {
    "happy": 25,
    "neutral": 65,
    "nervous": 10
  }
}
```

### 7A.2 動的質問生成（Phase 5）

#### コンテキスト考慮型質問
```python
# 入力: 生徒プロフィール + 過去の回答
context = {
  "student_profile": {
    "grade": "大学3年",
    "target_industry": "IT",
    "target_company": "メガベンチャー",
    "strengths": ["プログラミング", "チームワーク"],
    "weaknesses": ["プレゼン経験不足"]
  },
  "previous_answer": "チーム開発でリーダーを務めました",
  "weak_areas": ["具体性不足", "数値データ欠如"]
}

# Gemini APIが生成する追加質問
{
  "question": "そのチーム開発プロジェクトで、具体的にメンバーは何人でしたか？また、あなたはどのような技術的課題を解決しましたか？",
  "intent": "具体性を引き出す",
  "category": "深堀り質問",
  "difficulty": "medium",
  "expected_elements": ["人数", "技術名", "課題内容", "解決方法"]
}
```

#### 苦手分野の特定と集中練習
```python
# 自動分析: 質問カテゴリ別のスコア
{
  "自己PR": {"avg_score": 85, "count": 12},
  "志望動機": {"avg_score": 78, "count": 10},
  "挫折経験": {"avg_score": 62, "count": 5},  # ← 苦手
  "強み弱み": {"avg_score": 88, "count": 8},
  "時事問題": {"avg_score": 55, "count": 3}   # ← 苦手
}

# システムからの提案
「挫折経験と時事問題のスコアが低いです。
  次回は以下の質問で練習しましょう：
  1. これまでで最も大きな失敗は何ですか？
  2. 最近の○○業界のニュースについてどう思いますか？」
```

### 7A.3 準備回答管理

生徒が事前に回答を準備し、練習時に参照可能：

```python
{
  "question": "当社を志望する理由を教えてください",
  "prepared_answer": "御社のAI事業に興味があり...",
  "key_points": ["AI事業", "成長環境", "技術力向上"],
  "practice_results": [
    {
      "date": "2025-11-20",
      "score": 75,
      "feedback": "もう少し具体的なエピソードを"
    },
    {
      "date": "2025-11-25",
      "score": 82,
      "feedback": "改善されました"
    }
  ],
  "improvement_rate": "+7点"
}
```

### 7A.4 フィードバックテンプレート

よくある課題に対する定型フィードバック：

```yaml
template_id: "lack_of_specificity"
trigger_conditions:
  - keyword_count < 3
  - no_numbers_in_answer
  - abstract_words > 50%

feedback:
  summary: "回答が抽象的です"
  advice: |
    具体的な数字や固有名詞を入れましょう。
    例：「たくさん頑張った」→「週20時間、3ヶ月間取り組んだ」
  practice_task: "次回は数値を3つ以上入れて回答してください"
```

### 7A.5 オンライン面接モード

リモート面接特有のチェック項目：

```python
{
  "background_check": {
    "cleanliness": "good",      # 背景の整理整頓
    "professionalism": "excellent",  # 適切な背景か
    "distractions": []          # 気を散らすものがないか
  },
  "lighting_check": {
    "face_visibility": 85,       # 顔の明るさ
    "recommendation": "正面からもう少し光を当てると良いでしょう"
  },
  "audio_quality": {
    "clarity": 90,
    "background_noise": "low"
  },
  "camera_angle": {
    "position": "slightly_low",   # 少し下から撮影
    "recommendation": "カメラを目線の高さに調整してください"
  }
}
```

---

## 8. 開発フェーズ

### Phase 1: MVP (2-3ヶ月)
```
Week 1-2:  環境構築・Supabaseセットアップ
Week 3-4:  認証・プロフィール機能
Week 5-6:  音声アップロード・Whisper統合
Week 7-8:  基本UI・セッション管理
Week 9-10: 簡易評価・Markdownレポート生成
Week 11-12: PDF生成・ファイル管理・テスト・デバッグ
```

### Phase 2: データ連携 (2-3ヶ月)
```
Week 1-2:  生徒詳細プロフィール
Week 3-4:  履歴管理機能
Week 5-6:  スコア推移グラフ
Week 7-8:  Markdownグラフ埋め込み・PDF強化
Week 9-10: データ比較・可視化・GitHub連携
Week 11-12: テスト・改善・共有機能実装
```

### Phase 3: AI高度化 (2-3ヶ月)
```
Week 1-2:  Gemini API統合
Week 3-4:  キーワード抽出実装
Week 5-6:  敬語分析実装
Week 7-8:  感情分析実装
Week 9-10: 詳細フィードバック生成
Week 11-12: 最適化・テスト
```

### Phase 4: 拡張 (将来)
- ビデオ分析
- モバイルアプリ
- 複数校対応

---

## 9. コスト試算

### 9.1 初期費用
- **ハードウェア**: ¥100,000 - ¥200,000
  - 音声処理用PC/サーバー
  - CPU: i5以上、RAM: 8GB以上
  - SSD: 20GB以上

### 9.2 年間ランニングコスト

#### 小規模校（5-10人）
| 項目 | 金額 |
|-----|------|
| Supabase無料プラン | ¥0 |
| Gemini API無料枠 | ¥0 |
| サーバー電気代 | ¥6,000-12,000 |
| **合計** | **¥6,000-12,000/年** |

#### 中規模校（20-50人）
| 項目 | 金額 |
|-----|------|
| Supabase Pro | ¥40,000 |
| Gemini API無料枠 | ¥0 |
| サーバー電気代 | ¥6,000-12,000 |
| **合計** | **¥46,000-52,000/年** |

### 9.3 Gemini API無料枠
- 15 requests/min
- 1500 requests/day
- キーワード抽出・敬語分析・感情分析に十分

---

## 10. セキュリティ

### 10.1 認証・認可
- Supabase Auth（JWT）
- Row Level Security (RLS)
- ロールベースアクセス制御

### 10.2 データ保護
- HTTPS/TLS 1.3通信
- 保管時暗号化（Supabase標準）
- 音声ファイル暗号化
- 個人情報保護法準拠

### 10.3 アクセス制御
- 生徒: 自分のデータのみ閲覧可能
- 教師: 担当生徒のデータ閲覧・編集可能
- 教師: AI生成レポートの修正・上書き権限
- 教師: スコア調整権限
- 管理者: 全データアクセス可能

**重要**: 最終的なレポート内容は教師が承認したものであることを明示

---

## 11. パフォーマンス要件

- 音声文字起こし: 実時間の2倍以内
- 音響分析: 30秒以内
- Gemini API分析: 10秒以内（キャッシュヒット時は即時）
- レポート生成: 30秒以内
- 同時セッション: 最大10セッション

---

## 12. 品質保証

### 12.1 テスト戦略
- **単体テスト**: pytest（カバレッジ80%目標）
- **統合テスト**: FastAPI TestClient
- **E2Eテスト**: Playwright（Phase 2以降）
- **パフォーマンステスト**: locust

### 12.2 CI/CD
- GitHub Actions
- 自動テスト実行
- コード品質チェック（Ruff, ESLint）
- Docker イメージビルド

---

## 13. 運用・保守

### 13.1 監視
- サーバー稼働監視
- API使用量監視
- エラーログ収集

### 13.2 バックアップ
- Supabase自動バックアップ
- 音声ファイル定期バックアップ
- データベーススナップショット

### 13.3 更新戦略
- 週次パッチ更新
- 月次機能追加
- 四半期メジャーアップデート

---

## 14. リスク管理

### 14.1 技術的リスク
| リスク | 対策 |
|-------|------|
| Whisper精度不足 | モデルサイズ調整、手動修正機能 |
| Gemini API制限 | キャッシュ活用、フォールバック |
| サーバー負荷 | Celery非同期化、スケーリング |

### 14.2 運用リスク
| リスク | 対策 |
|-------|------|
| 教師のITリテラシー | 直感的UI、マニュアル整備 |
| 生徒のプライバシー懸念 | 同意取得、データ暗号化 |
| システム障害 | バックアップ、復旧手順 |

---

## 15. 今後の展開

### 15.1 短期（6ヶ月）
- MVP完成・テスト校導入
- フィードバック収集・改善

### 15.2 中期（1年）
- Phase 2-3完成
- 5校導入達成

### 15.3 長期（2年以降）
- Phase 4実装
- 複数校展開
- 機能拡充（ビデオ分析、モバイル）

---

## 付録

### A. 参考ドキュメント
- [データベース設計詳細](./.github/database-design.md)
- [API設計詳細](./.github/api-design.md)
- [AI実装ガイド](./.github/ai-implementation.md)
- [技術スタック詳細](./docs/tech-stack-simple.md)

### B. 開発環境セットアップ
```bash
# Backend
cd backend
poetry install
poetry run uvicorn app.main:app --reload

# Frontend
cd frontend
pnpm install
pnpm dev

# Docker
docker-compose up -d
```

### C. 連絡先
- プロジェクトオーナー: ootomonaiso
- リポジトリ: https://github.com/ootomonaiso/mensetu_renshyuu
