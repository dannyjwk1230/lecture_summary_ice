import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase 설정 정보 로드
SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").strip()
SUPABASE_KEY = (os.getenv("SUPABASE_KEY") or "").strip()

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL과 SUPABASE_KEY 환경 변수가 필요합니다. "
        "backend/.env에 설정했는지 확인하세요."
    )

# 서버 전체에서 공유할 DB 클라이언트 생성
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)