# 圧勝面接 - 開発設計書

## ドキュメント情報
- **作成日**: 2025年12月20日
- **バージョン**: 1.0
- **プロジェクト名**: 圧勝面接 (mensetu_renshyuu)
- **リポジトリ**: https://github.com/ootomonaiso/mensetu_renshyuu

---

## 1. システム概要

### 1.1 目的
面接練習における音声を自動分析し、客観的なフィードバックを提供することで、教師と生徒の面接対策を支援する。

### 1.2 システムの特徴
- **完全無料**: API料金ゼロ、すべてローカル実行
- **プライバシー保護**: 録音データは外部送信せず、ローカルで処理
- **多角的分析**: 文字起こし、話者分離、音声特徴分析、敬語チェック
- **使いやすいUI**: Webブラウザから簡単に操作可能

### 1.3 主要機能
1. 音声録音・ファイルアップロード
2. 話者分離（教師/生徒の自動識別）
3. 高精度文字起こし
4. AI による日本語補正・敬語チェック
5. 音声特徴分析（ピッチ、音量、話速、感情推定）
6. レポート生成（HTML/PDF）

---

## 2. システムアーキテクチャ

### 2.1 全体構成

```
┌─────────────────────────────────────────────────────────┐
│                   クライアント層                          │
│            (Webブラウザ - HTML/CSS/JS)                   │
│  ・録音UI                                                │
│  ・ファイルアップロード                                    │
│  ・レポート表示                                           │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP/REST API
                   ↓
┌─────────────────────────────────────────────────────────┐
│              Webアプリケーション層                         │
│                (FastAPI - app.py)                       │
│  ・ルーティング                                           │
│  ・ファイル管理                                           │
│  ・バックグラウンド処理                                    │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┼──────────┬──────────┬─────────┐
        ↓          ↓          ↓          ↓         ↓
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌─────────┐
│  音声処理 │ │   AI層   │ │データベース│ │レポート  │ │ファイル  │
│   層     │ │          │ │   層     │ │生成層    │ │管理層    │
└──────────┘ └──────────┘ └──────────┘ └─────────┘ └─────────┘
```

### 2.2 レイヤー構成

#### 2.2.1 プレゼンテーション層
- **技術**: HTML5, CSS3, JavaScript (Vanilla)
- **責務**: ユーザーインターフェース、録音制御、レポート表示
- **ファイル**: `templates/index.html`, `static/css/style.css`, `static/js/app.js`

#### 2.2.2 アプリケーション層
- **技術**: FastAPI (Python 3.9+)
- **責務**: リクエストルーティング、ビジネスロジック調整、バックグラウンド処理
- **ファイル**: `app.py`

#### 2.2.3 ドメイン層（ビジネスロジック）
- **音声処理モジュール** (`src/audio/`)
  - `transcriber.py`: 文字起こし (Whisper)
  - `diarization.py`: 話者分離 (pyannote.audio)
  - `analyzer.py`: 音声特徴分析 (librosa)

- **AI処理モジュール** (`src/ai/`)
  - `corrector.py`: 日本語補正・敬語チェック (Ollama + Llama 3.2)

- **レポート生成モジュール** (`src/report/`)
  - `generator.py`: HTML/PDFレポート生成

#### 2.2.4 データアクセス層
- **技術**: SQLAlchemy + SQLite
- **責務**: 面接履歴の永続化
- **ファイル**: `src/database/models.py`

---

## 3. モジュール設計

### 3.1 音声処理モジュール

#### 3.1.1 Transcriber (文字起こし)
```python
class Transcriber:
    """OpenAI Whisperを使用した文字起こし"""
    
    def __init__(self, model_name: str = "medium")
    def transcribe(self, audio_path: str) -> Dict
    def get_segments_with_timestamps(self, result: Dict) -> List[Dict]
```

**主要機能**:
- 音声ファイルをテキストに変換
- タイムスタンプ付きセグメント取得
- 日本語に特化した最適化

**使用ライブラリ**: `openai-whisper`

#### 3.1.2 Diarizer (話者分離)
```python
class Diarizer:
    """pyannote.audioを使用した話者分離"""
    
    def __init__(self, hf_token: str = None)
    def diarize(self, audio_path: str, num_speakers: int = None) -> List[Dict]
    def assign_speakers_to_transcription(
        self, transcription: List[Dict], 
        diarization: List[Dict]
    ) -> List[Dict]
```

**主要機能**:
- 話者の自動識別（教師/生徒）
- 話者ごとのタイムスタンプ記録
- 文字起こし結果との統合

**使用ライブラリ**: `pyannote.audio`

#### 3.1.3 AudioAnalyzer (音声分析)
```python
class AudioAnalyzer:
    """librosaを使用した音声特徴分析"""
    
    def __init__(self, sample_rate: int = 16000)
    def analyze(self, audio_path: str, segments: List[Dict]) -> Dict
    def analyze_emotion(self, audio_path: str, segments: List[Dict]) -> Dict
```

**主要機能**:
- ピッチ（声の高さ）分析
- 音量レベル測定
- 話速計算
- 感情推定（自信度、緊張度、落ち着き度）

**使用ライブラリ**: `librosa`, `soundfile`

### 3.2 AI処理モジュール

#### 3.2.1 TextCorrector (日本語補正)
```python
class TextCorrector:
    """Ollama (Llama 3.2) を使用した日本語補正"""
    
    def __init__(self, model: str = "llama3.2", host: str = None)
    def correct_text(self, text: str) -> str
    def evaluate_keigo(self, text: str, speaker: str) -> Dict
    def analyze_all_segments(self, segments: List[Dict]) -> Dict
```

**主要機能**:
- 文法・誤字脱字の修正
- 敬語の適切性評価
- 不自然な表現の検出

**使用ライブラリ**: `ollama`

### 3.3 レポート生成モジュール

#### 3.3.1 ReportGenerator
```python
class ReportGenerator:
    """HTMLレポート生成"""
    
    def __init__(self, report_folder: str = "./data/reports")
    def generate_html_report(
        self, interview_id: int, 
        filename: str,
        transcription: List[Dict],
        audio_analysis: Dict,
        keigo_evaluation: Dict
    ) -> str
```

**主要機能**:
- HTML形式のレポート生成
- グラフ・チャート生成 (matplotlib)
- PDF出力 (FPDF2)

**使用ライブラリ**: `matplotlib`, `fpdf2`

### 3.4 データベースモジュール

#### 3.4.1 Models (データモデル)
```python
class Interview(Base):
    """面接セッションモデル"""
    
    # フィールド
    - id: Integer (主キー)
    - filename: String (ユニーク)
    - created_at: DateTime
    - duration: Float
    - status: String (uploaded/processing/completed/failed)
    - transcription: Text
    - corrected_text: Text
    - teacher_pitch_mean: Float
    - student_pitch_mean: Float
    - report_path: String
    - error_message: Text
```

---

## 4. 処理フロー

### 4.1 メイン処理フロー

```
[1] ユーザーがファイルアップロード
    ↓
[2] app.py: /api/upload エンドポイント受信
    ↓
[3] ファイルを ./data/uploads/ に保存
    ↓
[4] データベースに Interview レコード作成 (status="uploaded")
    ↓
[5] バックグラウンドタスク開始 (process_interview)
    ↓
[6] モジュール初期化 (遅延ロード)
    - Transcriber (Whisper)
    - Diarizer (pyannote.audio)
    - TextCorrector (Ollama)
    ↓
[7] 文字起こし (Transcriber.transcribe)
    ↓
[8] 話者分離 (Diarizer.diarize)
    ↓
[9] 話者と文字起こし結果を統合
    ↓
[10] 音声分析 (AudioAnalyzer.analyze)
     - ピッチ、音量、話速を計算
    ↓
[11] 感情分析 (AudioAnalyzer.analyze_emotion)
     - 自信度、緊張度、落ち着き度を推定
    ↓
[12] AI補正 (TextCorrector.analyze_all_segments)
     - 敬語評価
     - 文法チェック
    ↓
[13] レポート生成 (ReportGenerator.generate_html_report)
    ↓
[14] データベース更新 (status="completed")
    ↓
[15] ユーザーにレポート表示
```

### 4.2 エラーハンドリング

```
各ステップで例外発生
    ↓
try-except でキャッチ
    ↓
データベースに error_message を記録
    ↓
status を "failed" に更新
    ↓
ユーザーにエラーメッセージ表示
```

---

## 5. データフロー

### 5.1 入力データ
- **形式**: 音声ファイル (WAV, MP3, M4A 等)
- **推奨スペック**: 
  - サンプリングレート: 16kHz 以上
  - チャンネル数: モノラルまたはステレオ
  - 時間: 1〜30分

### 5.2 中間データ
- **文字起こし結果**: JSON形式、セグメント + タイムスタンプ
- **話者分離結果**: JSON形式、話者ラベル + タイムスタンプ
- **音声特徴量**: 数値配列（ピッチ、音量、ゼロ交差率等）

### 5.3 出力データ
- **HTMLレポート**: `./data/reports/report_{id}_{timestamp}.html`
- **データベースレコード**: `./data/interviews.db` (SQLite)

---

## 6. セキュリティ設計

### 6.1 プライバシー保護
- **ローカル処理**: すべての処理をローカルで実行、外部API送信なし
- **データ保存**: ユーザーのPC内のみにデータ保存
- **匿名化**: レポートには話者名を含めない（「教師」「生徒」と表記）

### 6.2 ファイルセキュリティ
- **アップロード制限**: 
  - ファイルサイズ上限: 100MB
  - 許可拡張子: `.wav`, `.mp3`, `.m4a`, `.ogg`
- **パス検証**: ディレクトリトラバーサル攻撃を防止
- **タイムスタンプ付きファイル名**: 衝突を回避

### 6.3 アクセス制御
- **ローカルホスト限定**: デフォルトで `127.0.0.1` のみアクセス可能
- **認証不要**: ローカル利用のため、認証機能なし（将来の拡張候補）

---

## 7. パフォーマンス設計

### 7.1 最適化戦略
- **遅延初期化**: モジュールを必要時にロード（起動時間短縮）
- **バックグラウンド処理**: 長時間処理は非同期実行
- **キャッシュ**: モデルのメモリ保持（再利用）

### 7.2 推奨スペック
- **CPU**: Intel Core i5 以上 / Apple M1 以上
- **RAM**: 8GB 以上
- **ストレージ**: 5GB 以上の空き容量（モデル含む）
- **OS**: Windows 10/11, macOS 11+, Ubuntu 20.04+

### 7.3 処理時間目安
- 5分の音声: 約3〜5分の処理時間
- 10分の音声: 約6〜10分の処理時間

---

## 8. 拡張性設計

### 8.1 モジュール追加
- **プラグインアーキテクチャ**: 各モジュールは独立しており、容易に追加・削除可能
- **インターフェース統一**: 各クラスは共通のメソッド構造を持つ

### 8.2 将来の拡張案
1. **リアルタイム分析**: ストリーミング音声の即時分析
2. **多言語対応**: 英語・中国語等への対応
3. **AI面接官**: 自動質問生成と対話機能
4. **クラウド版**: 複数ユーザーでの利用
5. **モバイルアプリ**: iOS/Android対応

---

## 9. テスト戦略

### 9.1 単体テスト
- 各モジュールのメソッド単位でテスト
- テストフレームワーク: `pytest`

### 9.2 統合テスト
- エンドツーエンドの処理フローをテスト
- サンプル音声ファイルを使用

### 9.3 パフォーマンステスト
- 大容量ファイル（30分以上）での動作確認
- メモリリーク検出

---

## 10. デプロイメント

### 10.1 ローカルインストール
```bash
# リポジトリクローン
git clone https://github.com/ootomonaiso/mensetu_renshyuu.git
cd mensetu_renshyuu

# 依存関係インストール
pip install -r requirements.txt

# Ollama インストール（個別）
# https://ollama.ai/ から入手

# 起動
uvicorn app:app --host 127.0.0.1 --port 8000
```

### 10.2 環境変数設定
`.env` ファイルで設定可能:
- `OLLAMA_MODEL`: 使用するLLMモデル (デフォルト: `llama3.2`)
- `OLLAMA_HOST`: Ollama サーバーURL (デフォルト: `http://localhost:11434`)
- `HUGGINGFACE_TOKEN`: pyannote.audio用トークン
- `DIARIZATION_ENABLED`: 話者分離の有効化 (デフォルト: `true`)
- `NUM_SPEAKERS`: 話者数（指定しない場合は自動検出）

---

## 11. 保守性

### 11.1 コーディング規約
- **PEP 8**: Python標準スタイルガイドに準拠
- **型ヒント**: 関数の引数・戻り値に型を明記
- **ドキュメント**: すべてのクラス・関数にdocstring

### 11.2 ログ出力
- 各処理ステップで進捗をログ出力
- エラー発生時は詳細なスタックトレースを記録

### 11.3 バージョン管理
- Git を使用
- セマンティックバージョニング (MAJOR.MINOR.PATCH)

---

## 12. 参考資料

### 12.1 使用技術
- **FastAPI**: https://fastapi.tiangolo.com/
- **OpenAI Whisper**: https://github.com/openai/whisper
- **pyannote.audio**: https://github.com/pyannote/pyannote-audio
- **Ollama**: https://ollama.ai/
- **librosa**: https://librosa.org/

### 12.2 関連ドキュメント
- [システム仕様書](./system_specification.md)
- [API仕様書](./api_specification.md)
- [データベース設計書](./database_design.md)
- [テスト計画書](./test_plan.md)

---

## 変更履歴

| バージョン | 日付 | 変更内容 | 担当者 |
|----------|------|---------|-------|
| 1.0 | 2025-12-20 | 初版作成 | - |

---

**文書ステータス**: 承認済み
**次回レビュー日**: 2026-01-20
