"""テストユーザー作成スクリプト"""
import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv("backend/.env")

url = os.getenv("SUPABASE_URL")
service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not service_key:
    print("❌ 環境変数が設定されていません")
    exit(1)

supabase: Client = create_client(url, service_key)

print("👤 テストユーザー作成\n")

# テスト生徒ユーザー
test_student_email = "student@test.com"
test_student_password = "test123456"

# テスト教師ユーザー
test_teacher_email = "teacher@test.com"
test_teacher_password = "test123456"

print("1️⃣ 生徒ユーザー作成中...")
try:
    # Supabase Auth Admin APIでユーザー作成
    auth_response = supabase.auth.admin.create_user({
        "email": test_student_email,
        "password": test_student_password,
        "email_confirm": True
    })
    
    student_user_id = auth_response.user.id
    print(f"✅ 生徒ユーザー作成成功: {test_student_email}")
    print(f"   User ID: {student_user_id}")
    
    # user_profiles作成
    supabase.table("user_profiles").insert({
        "user_id": student_user_id,
        "role": "student",
        "name": "テスト 太郎",
        "school_name": "〇〇高校"
    }).execute()
    print("✅ user_profiles 作成成功")
    
    # student_profiles作成
    supabase.table("student_profiles").insert({
        "user_id": student_user_id,
        "grade": "高3",
        "class_name": "A組",
        "target_industry": "IT業界",
        "target_company": "株式会社Example",
        "target_position": "エンジニア職"
    }).execute()
    print("✅ student_profiles 作成成功")
    
except Exception as e:
    error_str = str(e)
    if "already registered" in error_str or "already exists" in error_str:
        print(f"⚠️  ユーザーは既に存在します: {test_student_email}")
    else:
        print(f"❌ エラー: {e}")

print("\n2️⃣ 教師ユーザー作成中...")
try:
    auth_response = supabase.auth.admin.create_user({
        "email": test_teacher_email,
        "password": test_teacher_password,
        "email_confirm": True
    })
    
    teacher_user_id = auth_response.user.id
    print(f"✅ 教師ユーザー作成成功: {test_teacher_email}")
    print(f"   User ID: {teacher_user_id}")
    
    # user_profiles作成
    supabase.table("user_profiles").insert({
        "user_id": teacher_user_id,
        "role": "teacher",
        "name": "山田 先生",
        "school_name": "〇〇高校"
    }).execute()
    print("✅ user_profiles 作成成功")
    
except Exception as e:
    error_str = str(e)
    if "already registered" in error_str or "already exists" in error_str:
        print(f"⚠️  ユーザーは既に存在します: {test_teacher_email}")
    else:
        print(f"❌ エラー: {e}")

print("\n" + "="*60)
print("📝 ログイン情報")
print("="*60)
print(f"生徒アカウント:")
print(f"  Email: {test_student_email}")
print(f"  Password: {test_student_password}")
print(f"\n教師アカウント:")
print(f"  Email: {test_teacher_email}")
print(f"  Password: {test_teacher_password}")
print("="*60)
print(f"\n🌐 フロントエンド: http://localhost:5173")
