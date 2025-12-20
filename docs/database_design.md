# 圧勝面接 - データベース設計書

## ドキュメント情報
- **作成日**: 2025年12月20日
- **バージョン**: 1.0
- **プロジェクト名**: 圧勝面接 (mensetu_renshyuu)
- **DBMS**: SQLite 3

---

## 1. データベース概要

### 1.1 目的
面接練習セッションの履歴と分析結果を永続化し、過去のデータを参照・比較可能にする。

### 1.2 データベース情報
- **データベース名**: `interviews.db`
- **場所**: `./data/interviews.db`
- **DBMS**: SQLite 3
- **文字コード**: UTF-8
- **バックアップ**: ユーザーが手動でファイルをコピー

### 1.3 設計方針
- **シンプル性**: 単一テーブルで管理（正規化は最小限）
- **拡張性**: 将来のカラム追加を考慮した設計
- **パフォーマンス**: 頻繁に検索されるカラムにインデックス設定
- **プライバシー**: 個人を特定する情報は保存しない

---

## 2. テーブル定義

### 2.1 interviews テーブル

#### 概要
面接練習セッションの基本情報と分析結果を保存

#### テーブル構造

| カラム名 | データ型 | 制約 | デフォルト値 | 説明 |
|---------|---------|------|------------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | - | 面接ID（主キー） |
| filename | VARCHAR(255) | NOT NULL, UNIQUE | - | 音声ファイル名 |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 作成日時 |
| duration | FLOAT | NULL | NULL | 録音時間（秒） |
| status | VARCHAR(20) | NOT NULL | 'uploaded' | 処理ステータス |
| transcription | TEXT | NULL | NULL | 文字起こし結果（JSON形式） |
| corrected_text | TEXT | NULL | NULL | AI補正後テキスト（JSON形式） |
| teacher_pitch_mean | FLOAT | NULL | NULL | 教師の平均ピッチ（Hz） |
| teacher_pitch_std | FLOAT | NULL | NULL | 教師のピッチ標準偏差（Hz） |
| teacher_volume_mean | FLOAT | NULL | NULL | 教師の平均音量（dB） |
| teacher_speaking_rate | FLOAT | NULL | NULL | 教師の話速（文字/分） |
| student_pitch_mean | FLOAT | NULL | NULL | 生徒の平均ピッチ（Hz） |
| student_pitch_std | FLOAT | NULL | NULL | 生徒のピッチ標準偏差（Hz） |
| student_volume_mean | FLOAT | NULL | NULL | 生徒の平均音量（dB） |
| student_speaking_rate | FLOAT | NULL | NULL | 生徒の話速（文字/分） |
| student_confidence | FLOAT | NULL | NULL | 生徒の自信度（0.0-1.0） |
| student_tension | FLOAT | NULL | NULL | 生徒の緊張度（0.0-1.0） |
| student_calmness | FLOAT | NULL | NULL | 生徒の落ち着き度（0.0-1.0） |
| student_clarity | FLOAT | NULL | NULL | 生徒の明瞭度（0.0-1.0） |
| keigo_score | INTEGER | NULL | NULL | 敬語スコア（0-100） |
| report_path | VARCHAR(255) | NULL | NULL | レポートファイルパス |
| error_message | TEXT | NULL | NULL | エラーメッセージ |

#### SQL定義

```sql
CREATE TABLE interviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(255) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    duration FLOAT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'uploaded',
    
    -- 文字起こし結果
    transcription TEXT NULL,
    corrected_text TEXT NULL,
    
    -- 教師の音声特徴
    teacher_pitch_mean FLOAT NULL,
    teacher_pitch_std FLOAT NULL,
    teacher_volume_mean FLOAT NULL,
    teacher_speaking_rate FLOAT NULL,
    
    -- 生徒の音声特徴
    student_pitch_mean FLOAT NULL,
    student_pitch_std FLOAT NULL,
    student_volume_mean FLOAT NULL,
    student_speaking_rate FLOAT NULL,
    
    -- 生徒の感情分析
    student_confidence FLOAT NULL,
    student_tension FLOAT NULL,
    student_calmness FLOAT NULL,
    student_clarity FLOAT NULL,
    
    -- 敬語評価
    keigo_score INTEGER NULL,
    
    -- レポート
    report_path VARCHAR(255) NULL,
    error_message TEXT NULL
);

-- インデックス作成
CREATE INDEX idx_interviews_status ON interviews(status);
CREATE INDEX idx_interviews_created_at ON interviews(created_at);
CREATE UNIQUE INDEX idx_interviews_filename ON interviews(filename);
```

#### インデックス

| インデックス名 | カラム | 理由 |
|-------------|-------|------|
| idx_interviews_status | status | ステータスでのフィルタリングが頻繁 |
| idx_interviews_created_at | created_at | 日時でのソート・検索が頻繁 |
| idx_interviews_filename | filename | ファイル名での検索（UNIQUE制約） |

---

## 3. カラム詳細

### 3.1 status カラムの値

| 値 | 説明 |
|---|------|
| uploaded | アップロード完了、処理待ち |
| processing | 処理中 |
| completed | 処理完了 |
| failed | 処理失敗 |

### 3.2 transcription カラムの形式

JSON配列形式で保存:
```json
[
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
    "text": "はい、私は〇〇大学の△△です。"
  }
]
```

### 3.3 corrected_text カラムの形式

JSON配列形式で保存:
```json
[
  {
    "speaker": "生徒",
    "original": "えーと、私は、その、〇〇大学の△△です。",
    "corrected": "私は〇〇大学の△△です。",
    "issues": [
      {
        "type": "冗長表現",
        "location": "えーと、その",
        "suggestion": "削除推奨"
      }
    ]
  }
]
```

---

## 4. データ操作

### 4.1 INSERT（新規登録）

```python
from src.database.models import Interview, get_db

db = next(get_db())

interview = Interview(
    filename="interview_20251220_143000.wav",
    status="uploaded"
)

db.add(interview)
db.commit()
db.refresh(interview)

print(f"新規面接ID: {interview.id}")
```

対応SQL:
```sql
INSERT INTO interviews (filename, status)
VALUES ('interview_20251220_143000.wav', 'uploaded');
```

### 4.2 SELECT（検索）

#### 全件取得
```python
interviews = db.query(Interview).all()
```

```sql
SELECT * FROM interviews;
```

#### ID指定
```python
interview = db.query(Interview).filter(Interview.id == 1).first()
```

```sql
SELECT * FROM interviews WHERE id = 1;
```

#### ステータスでフィルタ
```python
completed = db.query(Interview).filter(Interview.status == "completed").all()
```

```sql
SELECT * FROM interviews WHERE status = 'completed';
```

#### 日付範囲で検索
```python
from datetime import datetime, timedelta

week_ago = datetime.now() - timedelta(days=7)
recent = db.query(Interview).filter(Interview.created_at >= week_ago).all()
```

```sql
SELECT * FROM interviews
WHERE created_at >= datetime('now', '-7 days');
```

#### ページネーション
```python
page = 1
per_page = 20
offset = (page - 1) * per_page

interviews = db.query(Interview)\
    .order_by(Interview.created_at.desc())\
    .limit(per_page)\
    .offset(offset)\
    .all()
```

```sql
SELECT * FROM interviews
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;
```

### 4.3 UPDATE（更新）

#### ステータス更新
```python
interview = db.query(Interview).filter(Interview.id == 1).first()
interview.status = "processing"
db.commit()
```

```sql
UPDATE interviews
SET status = 'processing'
WHERE id = 1;
```

#### 分析結果の保存
```python
interview.transcription = json.dumps(transcription_data)
interview.student_pitch_mean = 220.5
interview.student_volume_mean = -22.1
interview.keigo_score = 85
interview.status = "completed"
db.commit()
```

```sql
UPDATE interviews
SET transcription = '...',
    student_pitch_mean = 220.5,
    student_volume_mean = -22.1,
    keigo_score = 85,
    status = 'completed'
WHERE id = 1;
```

#### エラー記録
```python
interview.status = "failed"
interview.error_message = "Whisper初期化に失敗しました"
db.commit()
```

```sql
UPDATE interviews
SET status = 'failed',
    error_message = 'Whisper初期化に失敗しました'
WHERE id = 1;
```

### 4.4 DELETE（削除）

```python
interview = db.query(Interview).filter(Interview.id == 1).first()
if interview:
    # 関連ファイルも削除
    if interview.report_path and os.path.exists(interview.report_path):
        os.remove(interview.report_path)
    
    audio_path = f"./data/uploads/{interview.filename}"
    if os.path.exists(audio_path):
        os.remove(audio_path)
    
    # レコード削除
    db.delete(interview)
    db.commit()
```

```sql
DELETE FROM interviews WHERE id = 1;
```

---

## 5. ビュー・ストアドプロシージャ

### 5.1 統計ビュー（将来実装）

```sql
CREATE VIEW interview_statistics AS
SELECT
    COUNT(*) AS total_interviews,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) AS completed_count,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) AS failed_count,
    AVG(duration) AS avg_duration,
    AVG(student_pitch_mean) AS avg_student_pitch,
    AVG(keigo_score) AS avg_keigo_score
FROM interviews
WHERE status IN ('completed', 'failed');
```

---

## 6. データ整合性

### 6.1 制約

#### 主キー制約
- `id`: 自動採番、一意性保証

#### UNIQUE制約
- `filename`: 同じファイル名の重複登録を防止

#### NOT NULL制約
- `filename`: 必須項目
- `created_at`: 必須項目
- `status`: 必須項目

#### CHECK制約（将来実装）
```sql
ALTER TABLE interviews
ADD CONSTRAINT chk_status
CHECK (status IN ('uploaded', 'processing', 'completed', 'failed'));

ALTER TABLE interviews
ADD CONSTRAINT chk_keigo_score
CHECK (keigo_score >= 0 AND keigo_score <= 100);

ALTER TABLE interviews
ADD CONSTRAINT chk_emotion_scores
CHECK (
    student_confidence BETWEEN 0 AND 1
    AND student_tension BETWEEN 0 AND 1
    AND student_calmness BETWEEN 0 AND 1
    AND student_clarity BETWEEN 0 AND 1
);
```

### 6.2 外部キー制約
現在なし（単一テーブル設計のため）

---

## 7. トランザクション管理

### 7.1 基本的なトランザクション

```python
from sqlalchemy.orm import Session

db = next(get_db())

try:
    # トランザクション開始
    interview = Interview(filename="test.wav")
    db.add(interview)
    
    # 複数の更新
    interview.status = "processing"
    interview.duration = 120.5
    
    # コミット
    db.commit()
except Exception as e:
    # ロールバック
    db.rollback()
    raise e
finally:
    db.close()
```

### 7.2 セーブポイント（将来実装）

```python
try:
    interview = Interview(filename="test.wav")
    db.add(interview)
    db.flush()  # セーブポイント
    
    # 処理続行...
    db.commit()
except Exception:
    db.rollback()
```

---

## 8. パフォーマンス最適化

### 8.1 インデックス戦略

**作成済みインデックス**:
- `idx_interviews_status`: ステータス検索の高速化
- `idx_interviews_created_at`: 日時ソートの高速化
- `idx_interviews_filename`: ファイル名検索の高速化

**将来追加候補**:
```sql
-- 敬語スコアでのソート用
CREATE INDEX idx_interviews_keigo_score ON interviews(keigo_score);

-- 生徒の自信度での検索用
CREATE INDEX idx_interviews_student_confidence ON interviews(student_confidence);
```

### 8.2 クエリ最適化

#### 不要なカラムは取得しない
```python
# Bad: 全カラム取得
interviews = db.query(Interview).all()

# Good: 必要なカラムのみ
interviews = db.query(
    Interview.id,
    Interview.filename,
    Interview.created_at,
    Interview.status
).all()
```

#### LIMIT使用
```python
# Bad: 全件取得後にスライス
interviews = db.query(Interview).all()[:10]

# Good: SQLでLIMIT
interviews = db.query(Interview).limit(10).all()
```

### 8.3 VACUUM（定期メンテナンス）

```sql
-- データベースの最適化
VACUUM;

-- 統計情報の更新
ANALYZE;
```

Pythonから実行:
```python
from sqlalchemy import text

db.execute(text("VACUUM"))
db.execute(text("ANALYZE"))
```

---

## 9. バックアップ・リストア

### 9.1 バックアップ方法

#### ファイルコピー（推奨）
```bash
# 日付付きバックアップ
cp ./data/interviews.db ./data/interviews_backup_$(date +%Y%m%d).db
```

#### SQLダンプ
```bash
sqlite3 ./data/interviews.db .dump > interviews_backup.sql
```

### 9.2 リストア方法

#### ファイルコピーから
```bash
cp ./data/interviews_backup_20251220.db ./data/interviews.db
```

#### SQLダンプから
```bash
sqlite3 ./data/interviews.db < interviews_backup.sql
```

---

## 10. マイグレーション

### 10.1 バージョン1.0 → 1.1（例）

新しいカラム `teacher_confidence` を追加:

```sql
-- カラム追加
ALTER TABLE interviews
ADD COLUMN teacher_confidence FLOAT NULL;

-- デフォルト値設定（既存レコード）
UPDATE interviews
SET teacher_confidence = 0.7
WHERE status = 'completed' AND teacher_confidence IS NULL;
```

Pythonでの実装:
```python
from sqlalchemy import text

db = next(get_db())
db.execute(text("""
    ALTER TABLE interviews
    ADD COLUMN teacher_confidence FLOAT NULL
"""))
db.commit()
```

### 10.2 マイグレーションツール（将来実装）

Alembicを使用した自動マイグレーション:
```bash
# 初期化
alembic init alembic

# マイグレーションファイル生成
alembic revision --autogenerate -m "Add teacher_confidence column"

# 適用
alembic upgrade head
```

---

## 11. セキュリティ

### 11.1 SQLインジェクション対策

**NG: 文字列連結**
```python
# 危険！
query = f"SELECT * FROM interviews WHERE id = {user_input}"
```

**OK: パラメータバインディング**
```python
# 安全
interview = db.query(Interview).filter(Interview.id == user_input).first()
```

### 11.2 データ暗号化（将来実装）

SQLCipherを使用した暗号化:
```python
from sqlalchemy import create_engine

engine = create_engine(
    "sqlite+pysqlcipher://:password@/./data/interviews.db"
)
```

---

## 12. モニタリング・ログ

### 12.1 クエリログ

```python
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### 12.2 スロークエリ検出

```python
import time
from sqlalchemy import event

@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, params, context, executemany):
    elapsed = time.time() - context._query_start_time
    if elapsed > 1.0:  # 1秒以上かかったクエリをログ
        logging.warning(f"Slow query ({elapsed:.2f}s): {statement}")
```

---

## 13. テストデータ

### 13.1 テストデータ投入

```sql
INSERT INTO interviews (filename, status, duration, student_pitch_mean, student_volume_mean, keigo_score)
VALUES
    ('test_interview_1.wav', 'completed', 120.5, 220.5, -22.1, 85),
    ('test_interview_2.wav', 'completed', 180.3, 210.2, -20.5, 92),
    ('test_interview_3.wav', 'processing', NULL, NULL, NULL, NULL),
    ('test_interview_4.wav', 'failed', NULL, NULL, NULL, NULL);
```

### 13.2 テストデータクリア

```sql
-- テストデータのみ削除
DELETE FROM interviews WHERE filename LIKE 'test_%';

-- 全データ削除（注意）
DELETE FROM interviews;
VACUUM;
```

---

## 14. ER図

```
┌─────────────────────────────────────┐
│           interviews                │
├─────────────────────────────────────┤
│ id (PK)                    INTEGER  │
│ filename (UNIQUE)          VARCHAR  │
│ created_at                 DATETIME │
│ duration                   FLOAT    │
│ status                     VARCHAR  │
│ transcription              TEXT     │
│ corrected_text             TEXT     │
│ teacher_pitch_mean         FLOAT    │
│ teacher_pitch_std          FLOAT    │
│ teacher_volume_mean        FLOAT    │
│ teacher_speaking_rate      FLOAT    │
│ student_pitch_mean         FLOAT    │
│ student_pitch_std          FLOAT    │
│ student_volume_mean        FLOAT    │
│ student_speaking_rate      FLOAT    │
│ student_confidence         FLOAT    │
│ student_tension            FLOAT    │
│ student_calmness           FLOAT    │
│ student_clarity            FLOAT    │
│ keigo_score                INTEGER  │
│ report_path                VARCHAR  │
│ error_message              TEXT     │
└─────────────────────────────────────┘
```

---

## 15. 変更履歴

| バージョン | 日付 | 変更内容 |
|----------|------|---------|
| 1.0 | 2025-12-20 | 初版作成 |

---

## 16. 関連ドキュメント

- [開発設計書](./design_document.md)
- [システム仕様書](./system_specification.md)
- [API仕様書](./api_specification.md)

---

**文書ステータス**: 承認済み
**次回レビュー日**: 2026-01-20
