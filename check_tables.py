"""Supabase テーブル存在確認スクリプト"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv("backend/.env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("❌ SUPABASE_URL または SUPABASE_SERVICE_ROLE_KEY が設定されていません")
    exit(1)

supabase: Client = create_client(url, key)

tables_to_check = [
    "user_profiles",
    "student_profiles", 
    "interview_sessions",
    "audio_analysis",
    "evaluations",
    "ai_analysis_cache"
]

print("🔍 Supabase テーブル存在確認...\n")

for table in tables_to_check:
    try:
        result = supabase.table(table).select("id").limit(1).execute()
        print(f"✅ {table}: 存在します (レコード数確認可)")
    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg or "relation" in error_msg:
            print(f"❌ {table}: テーブルが存在しません")
        else:
            print(f"⚠️  {table}: エラー - {error_msg}")

print("\n次のステップ:")
print("1. Supabase Dashboard (https://supabase.com/dashboard) にログイン")
print("2. SQL Editor を開く")
print("3. backend/init_supabase.sql の内容を実行")
