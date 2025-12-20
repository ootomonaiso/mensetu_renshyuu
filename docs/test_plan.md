# 圧勝面接 - テスト計画書

## ドキュメント情報
- **作成日**: 2025年12月20日
- **バージョン**: 1.0
- **プロジェクト名**: 圧勝面接 (mensetu_renshyuu)

---

## 1. テスト概要

### 1.1 テストの目的
圧勝面接システムの品質を保証し、仕様通りに動作することを確認する。

### 1.2 テスト方針
- **包括性**: すべての主要機能をテスト対象とする
- **自動化**: 可能な限り自動テストを実装
- **継続性**: CI/CDパイプラインでの自動実行
- **実用性**: 実際の利用シーンを想定したテスト

### 1.3 テストレベル
1. **単体テスト（Unit Test）**: 各モジュール・関数単位
2. **統合テスト（Integration Test）**: モジュール間の連携
3. **システムテスト（System Test）**: エンドツーエンドの動作確認
4. **性能テスト（Performance Test）**: レスポンス時間、メモリ使用量
5. **ユーザビリティテスト（Usability Test）**: 実際のユーザーによる評価

### 1.4 テスト環境

| 項目 | 内容 |
|-----|------|
| OS | Windows 11, macOS 14, Ubuntu 22.04 |
| Python | 3.9, 3.10, 3.11 |
| ブラウザ | Chrome 120+, Firefox 120+, Edge 120+ |
| テストフレームワーク | pytest, pytest-asyncio |
| モックツール | unittest.mock, pytest-mock |

---

## 2. 単体テスト

### 2.1 Transcriber（文字起こし）

#### テストケース

| テストID | テスト項目 | 入力 | 期待結果 |
|---------|----------|------|---------|
| UT-001 | 正常な音声ファイルの文字起こし | 5分のWAVファイル | 文字起こし結果が返る |
| UT-002 | 短い音声（1秒未満） | 0.5秒のWAVファイル | エラーまたは空文字列 |
| UT-003 | 存在しないファイル | 無効なパス | FileNotFoundError |
| UT-004 | 破損したファイル | 破損したWAV | エラーハンドリング |
| UT-005 | 日本語音声 | 日本語音声ファイル | 正確な日本語テキスト |
| UT-006 | 無音ファイル | 無音のWAV | 空の結果または警告 |

#### テストコード例

```python
import pytest
from src.audio.transcriber import Transcriber

@pytest.fixture
def transcriber():
    return Transcriber(model_name="tiny")  # テスト用に軽量モデル

def test_transcribe_valid_file(transcriber):
    """正常な音声ファイルの文字起こし"""
    result = transcriber.transcribe("tests/data/sample_interview.wav")
    
    assert result is not None
    assert "text" in result
    assert len(result["text"]) > 0

def test_transcribe_nonexistent_file(transcriber):
    """存在しないファイル"""
    with pytest.raises(FileNotFoundError):
        transcriber.transcribe("nonexistent.wav")

def test_get_segments_with_timestamps(transcriber):
    """タイムスタンプ付きセグメント取得"""
    result = transcriber.transcribe("tests/data/sample_interview.wav")
    segments = transcriber.get_segments_with_timestamps(result)
    
    assert isinstance(segments, list)
    assert len(segments) > 0
    assert "start" in segments[0]
    assert "end" in segments[0]
    assert "text" in segments[0]
```

---

### 2.2 Diarizer（話者分離）

#### テストケース

| テストID | テスト項目 | 入力 | 期待結果 |
|---------|----------|------|---------|
| UT-101 | 2人の話者識別 | 2人の会話音声 | 2つの話者ラベル |
| UT-102 | 1人のみの音声 | 1人の音声 | 1つの話者ラベル |
| UT-103 | 3人以上の音声 | 3人の会話 | 3つの話者ラベル（または設定値） |
| UT-104 | 話者分離と文字起こしの統合 | 2人の会話 | 各セグメントに話者ラベル付与 |

#### テストコード例

```python
import pytest
from src.audio.diarization import Diarizer

@pytest.fixture
def diarizer():
    return Diarizer()

def test_diarize_two_speakers(diarizer):
    """2人の話者識別"""
    segments = diarizer.diarize(
        "tests/data/two_speakers.wav",
        num_speakers=2
    )
    
    assert len(segments) > 0
    speakers = set(seg["speaker"] for seg in segments)
    assert len(speakers) == 2

def test_assign_speakers_to_transcription(diarizer):
    """話者分離と文字起こしの統合"""
    transcription = [
        {"start": 0.5, "end": 3.0, "text": "こんにちは"},
        {"start": 3.5, "end": 6.0, "text": "よろしくお願いします"}
    ]
    diarization = [
        {"start": 0.5, "end": 3.0, "speaker": "SPEAKER_00"},
        {"start": 3.5, "end": 6.0, "speaker": "SPEAKER_01"}
    ]
    
    result = diarizer.assign_speakers_to_transcription(transcription, diarization)
    
    assert result[0]["speaker"] == "SPEAKER_00"
    assert result[1]["speaker"] == "SPEAKER_01"
```

---

### 2.3 AudioAnalyzer（音声分析）

#### テストケース

| テストID | テスト項目 | 入力 | 期待結果 |
|---------|----------|------|---------|
| UT-201 | ピッチ分析 | 音声ファイル | ピッチの平均・標準偏差 |
| UT-202 | 音量分析 | 音声ファイル | RMS音量値 |
| UT-203 | 話速計算 | セグメント情報 | 文字数/分 |
| UT-204 | 感情分析 | 音声ファイル | 自信度、緊張度、落ち着き度 |
| UT-205 | ゼロ交差率計算 | 音声ファイル | 0.0-1.0の範囲 |

#### テストコード例

```python
import pytest
from src.audio.analyzer import AudioAnalyzer

@pytest.fixture
def analyzer():
    return AudioAnalyzer()

def test_analyze_pitch(analyzer):
    """ピッチ分析"""
    result = analyzer.analyze("tests/data/sample_interview.wav")
    
    assert "by_speaker" in result
    for speaker_data in result["by_speaker"].values():
        assert "pitch_mean" in speaker_data
        assert "pitch_std" in speaker_data
        assert speaker_data["pitch_mean"] > 0

def test_analyze_emotion(analyzer):
    """感情分析"""
    segments = [
        {"start": 0.5, "end": 10.0, "speaker": "生徒"}
    ]
    result = analyzer.analyze_emotion("tests/data/sample_interview.wav", segments)
    
    assert "生徒" in result
    assert "confidence" in result["生徒"]
    assert 0.0 <= result["生徒"]["confidence"] <= 1.0
```

---

### 2.4 TextCorrector（AI補正）

#### テストケース

| テストID | テスト項目 | 入力 | 期待結果 |
|---------|----------|------|---------|
| UT-301 | 文法補正 | 誤った文法のテキスト | 修正されたテキスト |
| UT-302 | 敬語評価 | 面接での発話 | 敬語スコアと問題箇所 |
| UT-303 | Ollama接続失敗 | Ollama停止状態 | 適切なエラーハンドリング |
| UT-304 | 長文処理 | 1000文字以上のテキスト | 正常に処理完了 |

#### テストコード例

```python
import pytest
from src.ai.corrector import TextCorrector

@pytest.fixture
def corrector():
    return TextCorrector()

def test_correct_text(corrector):
    """文法補正"""
    text = "えーと、私は、その、〇〇大学の△△です。"
    corrected = corrector.correct_text(text)
    
    assert len(corrected) > 0
    assert "えーと" not in corrected or "その" not in corrected

def test_evaluate_keigo(corrector):
    """敬語評価"""
    text = "御社に入社したいです。"
    result = corrector.evaluate_keigo(text, speaker="生徒")
    
    assert "score" in result
    assert "issues" in result
    assert 0 <= result["score"] <= 100
```

---

### 2.5 ReportGenerator（レポート生成）

#### テストケース

| テストID | テスト項目 | 入力 | 期待結果 |
|---------|----------|------|---------|
| UT-401 | HTMLレポート生成 | 分析結果 | HTMLファイル作成 |
| UT-402 | グラフ生成 | 音声分析データ | PNG画像生成 |
| UT-403 | 日本語表示 | 日本語テキスト | 文字化けなし |
| UT-404 | 大量データ | 1時間分の音声 | レポート生成成功 |

#### テストコード例

```python
import pytest
import os
from src.report.generator import ReportGenerator

@pytest.fixture
def report_gen():
    return ReportGenerator(report_folder="tests/output")

def test_generate_html_report(report_gen):
    """HTMLレポート生成"""
    transcription = [
        {"speaker": "教師", "text": "自己紹介をお願いします。"}
    ]
    audio_analysis = {
        "overall": {"duration": 120.0},
        "by_speaker": {}
    }
    
    report_path = report_gen.generate_html_report(
        interview_id=1,
        filename="test.wav",
        transcription=transcription,
        audio_analysis=audio_analysis
    )
    
    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "自己紹介" in content
```

---

## 3. 統合テスト

### 3.1 エンドツーエンド処理

#### テストケース

| テストID | テスト項目 | 手順 | 期待結果 |
|---------|----------|------|---------|
| IT-001 | 完全な処理フロー | ファイルアップロード → 処理 → レポート生成 | 全ステップ成功 |
| IT-002 | バックグラウンド処理 | 非同期処理の確認 | 処理完了まで正常動作 |
| IT-003 | データベース連携 | DB登録 → 更新 → 取得 | データ整合性確保 |

#### テストコード例

```python
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_full_workflow():
    """完全な処理フロー"""
    # 1. ファイルアップロード
    with open("tests/data/sample_interview.wav", "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("test.wav", f, "audio/wav")}
        )
    
    assert response.status_code == 200
    interview_id = response.json()["interview_id"]
    
    # 2. 処理完了を待つ
    import time
    max_wait = 300  # 5分
    elapsed = 0
    while elapsed < max_wait:
        status_response = client.get(f"/api/status/{interview_id}")
        status = status_response.json()["status"]
        
        if status == "completed":
            break
        elif status == "failed":
            pytest.fail("処理が失敗しました")
        
        time.sleep(5)
        elapsed += 5
    
    assert status == "completed"
    
    # 3. レポート取得
    report_response = client.get(f"/api/report/{interview_id}")
    assert report_response.status_code == 200
    report = report_response.json()
    
    assert "transcription" in report
    assert "audio_analysis" in report
```

---

## 4. システムテスト

### 4.1 機能テスト

| テストID | テスト項目 | 操作手順 | 期待結果 |
|---------|----------|---------|---------|
| ST-001 | ファイルアップロード | ブラウザから音声ファイルをアップロード | アップロード成功メッセージ表示 |
| ST-002 | 処理状況確認 | ステータスページで進捗確認 | プログレスバー表示 |
| ST-003 | レポート閲覧 | 処理完了後にレポートページを開く | グラフ・文字起こし表示 |
| ST-004 | レポートダウンロード | PDFダウンロードボタンクリック | PDFファイルダウンロード |
| ST-005 | 履歴一覧 | 過去の面接一覧を表示 | 正しい順序で表示 |
| ST-006 | データ削除 | 特定の面接データを削除 | データとファイル削除 |

### 4.2 非機能テスト

#### 性能テスト

| テストID | テスト項目 | 条件 | 目標値 |
|---------|----------|------|-------|
| PT-001 | 文字起こし処理時間 | 5分の音声 | 2分以内 |
| PT-002 | メモリ使用量 | 10分の音声処理中 | 4GB以内 |
| PT-003 | レポート生成時間 | 標準的な面接データ | 10秒以内 |
| PT-004 | ファイルアップロード時間 | 50MBファイル | 3秒以内 |

#### 互換性テスト

| テストID | テスト項目 | 環境 | 期待結果 |
|---------|----------|------|---------|
| CT-001 | Windowsでの動作 | Windows 11 | 全機能動作 |
| CT-002 | macOSでの動作 | macOS 14 | 全機能動作 |
| CT-003 | Linuxでの動作 | Ubuntu 22.04 | 全機能動作 |
| CT-004 | Chromeでの動作 | Chrome 120+ | UI正常表示 |
| CT-005 | Firefoxでの動作 | Firefox 120+ | UI正常表示 |

#### セキュリティテスト

| テストID | テスト項目 | 攻撃方法 | 期待結果 |
|---------|----------|---------|---------|
| SEC-001 | SQLインジェクション | 特殊文字入力 | 適切にエスケープ |
| SEC-002 | パストラバーサル | ../../../etc/passwd | アクセス拒否 |
| SEC-003 | 大容量ファイル | 1GBファイルアップロード | 拒否（100MB制限） |
| SEC-004 | 外部アクセス | 他ホストからのアクセス | 拒否（127.0.0.1のみ） |

---

## 5. ユーザビリティテスト

### 5.1 評価項目

| 項目 | 評価基準 | 目標値 |
|-----|---------|-------|
| 学習コスト | 初回利用で操作方法を理解できる時間 | 5分以内 |
| 操作性 | ファイルアップロードまでのクリック数 | 2クリック以内 |
| 視認性 | レポートの重要情報を見つける時間 | 10秒以内 |
| エラー理解 | エラーメッセージの理解度 | 80%以上 |

### 5.2 テストシナリオ

**シナリオ1: 初めての利用**
1. アプリケーションを起動
2. 音声ファイルをアップロード
3. 処理完了を待つ
4. レポートを確認
5. 改善点を理解

**シナリオ2: 繰り返し利用**
1. 過去のレポートを確認
2. 新しい音声をアップロード
3. 前回との比較
4. 改善度を確認

---

## 6. テストデータ

### 6.1 テスト用音声ファイル

| ファイル名 | 内容 | 時間 | 話者数 |
|-----------|------|------|-------|
| sample_interview.wav | 標準的な面接練習 | 5分 | 2人 |
| short_audio.wav | 短い音声 | 10秒 | 1人 |
| long_audio.wav | 長時間音声 | 30分 | 2人 |
| noisy_audio.wav | 雑音あり | 5分 | 2人 |
| silent_audio.wav | 無音 | 1分 | 0人 |
| three_speakers.wav | 3人の会話 | 10分 | 3人 |

### 6.2 テスト用テキストデータ

```python
TEST_TEXTS = {
    "good_keigo": "本日はお忙しいところありがとうございます。",
    "bad_keigo": "今日は忙しいのにありがとうございます。",
    "casual": "ぶっちゃけ、御社に入りたいっす。",
    "formal": "貴社に入社させていただきたく存じます。",
}
```

---

## 7. バグ管理

### 7.1 バグ優先度

| 優先度 | 説明 | 対応期限 |
|-------|------|---------|
| P0 - Critical | システムが起動しない、データ損失 | 即時 |
| P1 - High | 主要機能が動作しない | 1日以内 |
| P2 - Medium | 一部機能に問題、回避策あり | 1週間以内 |
| P3 - Low | UI の軽微な問題 | 次回リリース |

### 7.2 バグレポートテンプレート

```markdown
## バグ報告

**バグID**: BUG-001
**発見日**: 2025-12-20
**報告者**: テスター名

### 概要
[バグの簡潔な説明]

### 再現手順
1. [ステップ1]
2. [ステップ2]
3. [ステップ3]

### 期待される動作
[正常動作の説明]

### 実際の動作
[実際に起きた問題]

### 環境
- OS: Windows 11
- Python: 3.11
- ブラウザ: Chrome 120

### スクリーンショット
[添付]

### ログ
```
[エラーログ]
```

### 優先度
P1 - High
```

---

## 8. 自動テスト実行

### 8.1 pytest設定

`pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=src
    --cov-report=html
    --cov-report=term-missing
```

### 8.2 テスト実行コマンド

```bash
# 全テスト実行
pytest

# 特定のテストファイル
pytest tests/test_transcriber.py

# 特定のテスト関数
pytest tests/test_transcriber.py::test_transcribe_valid_file

# カバレッジレポート生成
pytest --cov=src --cov-report=html

# 並列実行
pytest -n auto
```

### 8.3 CI/CD設定（GitHub Actions）

`.github/workflows/test.yml`:
```yaml
name: Test

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.9', '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run tests
      run: pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## 9. テストスケジュール

| フェーズ | 期間 | 実施内容 |
|---------|------|---------|
| 単体テスト | 開発中随時 | 各モジュール実装後に実施 |
| 統合テスト | 機能実装完了後 | モジュール統合後に実施 |
| システムテスト | リリース1週間前 | 全機能の動作確認 |
| 性能テスト | リリース3日前 | 負荷テスト実施 |
| ユーザビリティテスト | リリース前 | 実際のユーザーで評価 |
| リグレッションテスト | 修正後 | 既存機能の動作確認 |

---

## 10. テストカバレッジ目標

| レベル | 目標カバレッジ |
|-------|-------------|
| 行カバレッジ | 80%以上 |
| 分岐カバレッジ | 70%以上 |
| 関数カバレッジ | 90%以上 |

---

## 11. テスト完了基準

以下の条件をすべて満たした場合、テスト完了とみなす:

- [ ] 全単体テストが成功
- [ ] 全統合テストが成功
- [ ] P0, P1バグが0件
- [ ] テストカバレッジが目標値以上
- [ ] 性能要件を満たす
- [ ] 3つ以上のOSで動作確認
- [ ] ユーザビリティテストで目標値達成

---

## 12. 変更履歴

| バージョン | 日付 | 変更内容 |
|----------|------|---------|
| 1.0 | 2025-12-20 | 初版作成 |

---

## 13. 関連ドキュメント

- [開発設計書](./design_document.md)
- [システム仕様書](./system_specification.md)
- [API仕様書](./api_specification.md)
- [データベース設計書](./database_design.md)

---

**文書ステータス**: 承認済み
**次回レビュー日**: 2026-01-20
