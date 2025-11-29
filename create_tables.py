"""Supabase テーブル自動作成スクリプト"""
import os
import re
from dotenv import load_dotenv
from supabase import create_client, Client
import httpx

load_dotenv("backend/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ 環境変数が設定されていません")
    exit(1)

# SQLファイルを読み込み
with open("backend/init_supabase.sql", "r", encoding="utf-8") as f:
    sql_content = f.read()

print("📋 SQL実行準備...")
print(f"対象URL: {SUPABASE_URL}")
print(f"SQL行数: {len(sql_content.splitlines())}")

# プロジェクトIDを抽出
project_ref = SUPABASE_URL.split("//")[1].split(".")[0]
print(f"プロジェクトID: {project_ref}")

print("\n🚀 SQLを個別ステートメントに分割して実行中...\n")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# SQLを個別のステートメントに分割（簡易版）
statements = []
current = []
in_do_block = False

for line in sql_content.splitlines():
    stripped = line.strip()
    
    # DO $$ ブロックの開始
    if stripped.startswith("DO $$"):
        in_do_block = True
    
    current.append(line)
    
    # DO $$ ブロックの終了
    if in_do_block and "END $$;" in stripped:
        in_do_block = False
        statements.append("\n".join(current))
        current = []
    # 通常のステートメント終了
    elif not in_do_block and stripped.endswith(";") and not stripped.startswith("--"):
        statements.append("\n".join(current))
        current = []

# 残りを追加
if current:
    statements.append("\n".join(current))

# フィルタリング（空行とコメントのみの行を除外）
statements = [s.strip() for s in statements if s.strip() and not s.strip().startswith("--")]

print(f"分割されたSQL文: {len(statements)}個\n")

# Supabase Management API経由でSQL実行を試みる
print("⚠️  Python クライアント経由での自動実行はできません。")
print("\n以下の方法でテーブルを作成してください:\n")
print("=" * 70)
print("方法1: Supabase Dashboard (推奨)")
print("=" * 70)
print(f"1. https://supabase.com/dashboard/project/{project_ref}/sql/new を開く")
print("2. 以下のファイルの内容をコピー&ペースト:")
print(f"   {os.path.abspath('backend/init_supabase.sql')}")
print("3. Run をクリック\n")

print("=" * 70)
print("方法2: psql コマンド (WSL/Linux)")
print("=" * 70)
print(f"psql 'postgresql://postgres:[PASSWORD]@db.{project_ref}.supabase.co:5432/postgres' < backend/init_supabase.sql")
print("\n(PASSWORDはSupabase Dashboardのデータベース設定から取得)")

print("\n" + "=" * 70)
print("\n✅ テーブル作成後、以下のコマンドでテストユーザーを作成:")
print(r"   .\.venv\Scripts\python.exe create_test_users.py")

