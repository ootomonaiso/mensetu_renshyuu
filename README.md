# 面接練習レポート支援ツール

教師と生徒の面接練習を録音・分析し、フィードバックレポートを生成する完全無料のローカル実行ツールです。

## 機能

- 🎤 **音声録音**: ブラウザから直接録音
- 👥 **話者分離**: 教師と生徒の音声を自動識別
- 📝 **文字起こし**: 日本語音声をテキスト化
- ✍️ **日本語補正**: AI による文法・敬語のチェック
- 🎵 **音声分析**: ピッチ、音量、話速、声のトーンを分析
- 📊 **レポート生成**: 分析結果をHTML/PDFで出力

## 特徴

- ✅ **完全無料**: API料金ゼロ
- 🔒 **プライバシー保護**: 完全ローカル実行、データ外部送信なし
- 🌐 **オフライン動作**: 初回セットアップ後はインターネット不要

## 必要要件

### システム要件
- **OS**: Windows 10/11, macOS, Linux
- **CPU**: 4コア以上 (8コア推奨)
- **RAM**: 8GB以上 (16GB推奨)
- **ストレージ**: 10GB以上の空き容量

### ソフトウェア
- Python 3.9以上
- FFmpeg (音声処理用)
- Ollama (AI補正用)

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/ootomonaiso/mensetu_renshyuu.git
cd mensetu_renshyuu
```

### 2. 仮想環境の作成と有効化

#### Windows (PowerShell)

仮想環境の作成:
```powershell
python -m venv venv
```

仮想環境の有効化:
```powershell
.\venv\Scripts\Activate.ps1
```

> **注意**: PowerShellの実行ポリシーでエラーが出る場合:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

仮想環境の無効化（作業終了時）:
```powershell
deactivate
```

#### Windows (コマンドプロンプト)

仮想環境の作成:
```cmd
python -m venv venv
```

仮想環境の有効化:
```cmd
venv\Scripts\activate.bat
```

仮想環境の無効化（作業終了時）:
```cmd
deactivate
```

#### macOS/Linux

仮想環境の作成:
```bash
python3 -m venv venv
```

仮想環境の有効化:
```bash
source venv/bin/activate
```

仮想環境の無効化（作業終了時）:
```bash
deactivate
```

> **確認**: 仮想環境が有効化されると、プロンプトの先頭に `(venv)` が表示されます

### 3. 依存パッケージのインストール

仮想環境が有効化された状態で実行:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

インストールの確認:
```bash
pip list
```

### 4. FFmpegのインストール

**Windows**:
```powershell
# Chocolatey使用
choco install ffmpeg

# または https://ffmpeg.org/download.html からダウンロード
```

**macOS**:
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install ffmpeg
```

### 5. Ollamaのインストールと起動

公式サイトからダウンロード: https://ollama.ai/

インストール後、モデルをダウンロード:
```bash
ollama pull llama3.2
```

Ollamaを起動:
```bash
ollama serve
```

### 6. HuggingFace トークンの取得

1. https://huggingface.co/ でアカウント作成
2. https://huggingface.co/settings/tokens でトークン生成
3. `.env`ファイルを作成:

```bash
cp .env.example .env
```

`.env`ファイルを編集してトークンを設定:
```
HUGGINGFACE_TOKEN=your_actual_token_here
```

### 7. データディレクトリの作成

```bash
mkdir -p data/uploads data/reports
```

## 使い方

### サーバーの起動

```bash
python app.py
```

ブラウザで http://localhost:8000 を開く

### 面接練習の実施

1. **録音開始**: "録音開始"ボタンをクリック
2. **面接練習**: 教師役と生徒役で面接を実施
3. **録音停止**: "録音停止"ボタンをクリック
4. **分析実行**: "分析開始"ボタンをクリック
5. **レポート確認**: 分析完了後、レポートが表示されます

## プロジェクト構造

```
mensetu_renshyuu/
├── app.py                 # FastAPIメインアプリケーション
├── requirements.txt       # Python依存パッケージ
├── .env.example          # 環境変数テンプレート
├── README.md             # このファイル
├── src/
│   ├── audio/
│   │   ├── recorder.py       # 録音処理
│   │   ├── transcriber.py    # Whisper文字起こし
│   │   ├── diarization.py    # 話者分離
│   │   └── analyzer.py       # 音声分析
│   ├── ai/
│   │   └── corrector.py      # Ollama日本語補正
│   ├── report/
│   │   └── generator.py      # レポート生成
│   └── database/
│       └── models.py         # データベースモデル
├── static/
│   ├── css/
│   │   └── style.css        # スタイルシート
│   └── js/
│       └── app.js           # フロントエンドJS
├── templates/
│   └── index.html           # メインUI
└── data/
    ├── uploads/             # 録音ファイル保存先
    ├── reports/             # レポート保存先
    └── interviews.db        # SQLiteデータベース
```

## トラブルシューティング

### Whisperが遅い場合
`.env`ファイルで小さいモデルを選択:
```
WHISPER_MODEL=tiny  # または base
```

### GPU使用時のエラー
CUDA対応GPUがある場合、PyTorch GPU版をインストール:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Ollamaに接続できない
Ollamaが起動しているか確認:
```bash
ollama list
```

## リリース・タグ付け手順（開発者向け）

新しいバージョンをリリースする場合は、以下の手順でタグを作成します：

### 1. バージョンタグの作成

```bash
# バージョン番号を決定（例: v1.0.0）
git tag -a v1.0.0 -m "Release version 1.0.0"
```

### 2. タグをGitHubにプッシュ

```bash
git push origin v1.0.0
```

### 3. 自動リリース作成

タグをプッシュすると、GitHub Actionsが自動的に：
- リリースノートを生成
- ソースコードのアーカイブ（.tar.gz と .zip）を作成
- GitHubのReleasesページに公開

### バージョン番号の規則

セマンティックバージョニング（SemVer）に従います：

- **v1.0.0**: メジャーバージョン（互換性のない変更）
- **v1.1.0**: マイナーバージョン（後方互換性のある機能追加）
- **v1.0.1**: パッチバージョン（バグ修正）

### リリースの確認

リリース後は以下のURLで確認できます：
```
https://github.com/ootomonaiso/mensetu_renshyuu/releases
```

## ライセンス

MIT License

## 貢献

プルリクエストを歓迎します！

## 参考リンク

- [OpenAI Whisper](https://github.com/openai/whisper)
- [pyannote.audio](https://github.com/pyannote/pyannote-audio)
- [Ollama](https://ollama.ai/)
- [VoiceMind](https://voicemind.net/)
