# 話者分離機能 実装完了

## 実装内容

### 1. AudioProcessor に pyannote.audio を統合

**機能**:
- `diarize_speakers()`: 話者分離を実行し、各セグメントに話者ラベル (SPEAKER_00, SPEAKER_01...) を付与
- `transcribe()`: Whisper 文字起こし + pyannote 話者分離を統合し、「誰が何を言ったか」を出力
- `_assign_speakers()`: 文字起こしセグメントに話者を割り当て (中間時刻でマッチング)

**モデル**:
- `pyannote/speaker-diarization-3.1` (公開モデル、Hugging Face Hub からダウンロード)
- 初回起動時に自動ダウンロード (約1GB)

**出力例**:
```python
{
    "text": "全文字起こし",
    "segments": [
        {
            "start": 0.5,
            "end": 2.3,
            "text": "よろしくお願いします",
            "speaker": "SPEAKER_00"
        },
        {
            "start": 2.5,
            "end": 4.0,
            "text": "こちらこそ",
            "speaker": "SPEAKER_01"
        }
    ],
    "speakers": [
        {"start": 0.0, "end": 2.5, "speaker": "SPEAKER_00"},
        {"start": 2.5, "end": 5.0, "speaker": "SPEAKER_01"}
    ]
}
```

---

### 2. ReportGenerator に話者別発言表示を追加

**レポート構造**:
```markdown
## 📝 文字起こし

### 話者別発言

**SPEAKER_00** (0.5s - 2.3s)  
> よろしくお願いします

**SPEAKER_01** (2.5s - 4.0s)  
> こちらこそ

### 全文

よろしくお願いします こちらこそ
```

---

## 使い方

### 話者分離を有効化 (デフォルト)
```python
processor = AudioProcessor(model_size="base", enable_diarization=True)
result = processor.transcribe(audio_path)
```

### 話者分離を無効化
```python
processor = AudioProcessor(model_size="base", enable_diarization=False)
```

---

## 初回起動時の注意

1. **モデルダウンロード**: 初回起動時に `pyannote/speaker-diarization-3.1` が自動ダウンロードされます (約1GB、数分かかる場合があります)
2. **メモリ使用量**: 話者分離は CPU でも動作しますが、メモリを多く使用します (推奨: 8GB 以上)
3. **処理時間**: 1分の音声で約30秒~1分の処理時間

---

## WebSocket エラーについて

`flask-sock` は正常にインストールされています。エラーが出る場合:

1. **サーバー再起動**: 依存関係更新後は必ず再起動
2. **ブラウザキャッシュクリア**: Ctrl+Shift+R でハードリフレッシュ
3. **pyannote モデルダウンロード待機**: 初回起動時はモデルダウンロードが完了するまで待つ

---

## 次のステップ

- [x] 話者分離機能実装
- [x] レポートに話者別発言表示
- [ ] UI に話者数表示
- [ ] 話者ラベルを「生徒/面接官」に自動割り当て (Phase 2)
