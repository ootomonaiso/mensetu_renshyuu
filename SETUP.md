# 面接練習レポート支援ツール - セットアップガイド

## 📋 必要なもの

### 1. Python 環境
```powershell
python --version  # 3.9以上であることを確認
```

### 2. FFmpegのインストール

**Chocolateyを使う場合**:
```powershell
choco install ffmpeg
```

**手動インストールの場合**:
1. https://ffmpeg.org/download.html からダウンロード
2. 環境変数PATHに追加

### 3. Ollamaのインストール

1. https://ollama.ai/ からダウンロード・インストール
2. PowerShellで以下を実行:

```powershell
# Ollamaモデルをダウンロード
ollama pull llama3.2

# Ollamaを起動（別ウィンドウで実行し続ける）
ollama serve
```

## 🚀 セットアップ手順

### ステップ1: 仮想環境作成

```powershell
cd c:\00pro\mensetu_renshyuu
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### ステップ2: 依存パッケージインストール

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

**注意**: インストールには5-10分かかる場合があります。

### ステップ3: 環境変数設定

1. HuggingFaceアカウント作成: https://huggingface.co/join
2. トークン取得: https://huggingface.co/settings/tokens
3. `.env`ファイル作成:

```powershell
cp .env.example .env
```

4. `.env`ファイルを編集してトークンを設定:

```
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxxxxxxx
```

### ステップ4: データディレクトリ確認

```powershell
# すでに作成済みですが、念のため確認
if (!(Test-Path "data\uploads")) { New-Item -ItemType Directory -Path "data\uploads" }
if (!(Test-Path "data\reports")) { New-Item -ItemType Directory -Path "data\reports" }
```

## ▶️ 起動方法

### 1. Ollamaを起動（別ウィンドウ）

```powershell
ollama serve
```

### 2. アプリケーション起動

```powershell
.\venv\Scripts\Activate.ps1
python app.py
```

### 3. ブラウザでアクセス

http://localhost:8000 を開く

## 🧪 動作確認

### 最小構成でのテスト

Ollamaなしでテストする場合（文字起こしと音声分析のみ）:

1. `.env`の`OLLAMA_HOST`をコメントアウト
2. `app.py`を起動
3. 録音または音声ファイルをアップロード

## ❗ トラブルシューティング

### エラー: "HUGGINGFACE_TOKEN is required"

→ `.env`ファイルにトークンを設定してください

### エラー: "Ollama connection failed"

→ 別ウィンドウで `ollama serve` を実行してください

### 処理が遅い

→ `.env`で小さいモデルに変更:
```
WHISPER_MODEL=tiny
```

### GPU使用したい

PyTorch GPU版をインストール:
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 📦 初回実行時のダウンロード

初回実行時、以下のモデルが自動ダウンロードされます（合計約2-5GB）:
- Whisper model (base: ~140MB)
- pyannote.audio models (~1GB)
- Ollama model (llama3.2: ~2GB)

## 🎯 使い方

1. **録音**: 「録音開始」ボタンをクリック
2. **面接実施**: 教師役と生徒役で会話
3. **停止**: 「録音停止」ボタンをクリック
4. **アップロード**: 「アップロード & 分析」をクリック
5. **待機**: 処理完了まで待つ（10分の音声で約10分）
6. **確認**: レポートを表示

## 💡 ヒント

- 静かな環境で録音すると精度が上がります
- マイクは口から20-30cm離すと良いです
- 処理中はブラウザを閉じないでください

## 🔄 停止方法

1. Ctrl+C でアプリケーション停止
2. Ollama起動ウィンドウもCtrl+Cで停止

## 📝 ログ確認

処理状況はターミナルに表示されます。エラーが発生した場合、ここを確認してください。
