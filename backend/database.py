import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase 설정 정보 로드
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 서버 전체에서 공유할 DB 클라이언트 생성
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)