"""
開発サーバー起動スクリプト
"""
import uvicorn
import sys
from pathlib import Path

# backend ディレクトリを Python パスに追加
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    print("=" * 60)
    print("圧勝面接練習システム - 開発サーバー")
    print("=" * 60)
    print()
    print("サーバー起動中...")
    print("URL: http://127.0.0.1:8000")
    print("API ドキュメント: http://127.0.0.1:8000/docs")
    print()
    print("終了するには Ctrl+C を押してください")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
