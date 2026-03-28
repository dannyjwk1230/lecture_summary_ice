import os
import boto3
import google.generativeai as genai
from database import supabase # DB는 여전히 슈파베이스
from dotenv import load_dotenv
import time

load_dotenv()

class LectureService:
    def __init__(self):
        # 1. Cloudflare R2 설정 (S3 호환 API 사용)
        self.s3_client = boto3.client(
            service_name="s3",
            endpoint_url=os.getenv("R2_ENDPOINT_URL"), # R2 고유 엔드포인트
            aws_access_key_id=os.getenv("R2_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("R2_SECRET_KEY"),
            region_name="auto" # R2는 보통 auto로 설정
        )
        self.bucket_name = os.getenv("R2_BUCKET_NAME")

        # 2. Gemini 설정
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("models/gemini-3-flash-preview")

    def upload_to_r2(self, local_path, file_key):
        """10GB 무료 R2 저장소에 파일 업로드"""
        self.s3_client.upload_file(local_path, self.bucket_name, file_key)
        # R2의 파일 주소 반환
        return f"{os.getenv('R2_PUBLIC_URL')}/{file_key}"

    def analyze_lecture(self, audio_path, pdf_path, start_pg, end_pg):
        """Gemini 멀티모달 분석 (코드 동일)"""
        g_audio = genai.upload_file(path=audio_path)
        g_pdf = genai.upload_file(path=pdf_path)

        while g_audio.state.name == "PROCESSING":
            time.sleep(2)
            g_audio = genai.get_file(g_audio.name)

        prompt = f"{start_pg}p ~ {end_pg}p 사이의 PDF 내용을 기반으로 오디오를 요약해줘."
        response = self.model.generate_content([prompt, g_audio, g_pdf])
        return response.text
    
    def save_metadata(self, db_data):   #db_data의 형식에 맞춰 수정
        """분석 결과와 R2 URL을 Supabase DB에 저장"""
        try:
            # data = {
            #     "file_name": db_data.file_key,
            #     "file_url": db_data.r2_url,
            #     "summary": db_data.summary_text,
            #     "created_at": "now()" # Supabase에서 자동 생성 설정 가능
            # }
            if "created_at" not in db_data:
                db_data["created_at"] = "now()"
            # 'lectures'는 Supabase에 생성한 테이블 이름입니다.
            response = supabase.table("lectures").insert(db_data).execute()
            return response
        except Exception as e:
            print(f"데이터베이스 저장 중 오류 발생: {e}")
            return None