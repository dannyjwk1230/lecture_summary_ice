import os
import boto3
import google.generativeai as genai
from dotenv import load_dotenv
import time

load_dotenv()

class LectureService:
    def __init__(self):
        # Gemini 설정
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-3.1-flash")
        
        # AWS S3 설정
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
            region_name="ap-northeast-2"
        )
        self.bucket = os.getenv("S3_BUCKET_NAME")

    def upload_to_s3(self, file_path, object_name):
        self.s3.upload_file(file_path, self.bucket, object_name)
        return object_name

    def process_with_gemini(self, audio_path, pdf_path):
        # 1. Gemini Files API로 업로드 (Gemini는 자신의 스토리지에서 직접 읽어야 성능이 가장 좋음)
        g_audio = genai.upload_file(path=audio_path)
        g_pdf = genai.upload_file(path=pdf_path)

        # 2. 오디오 처리 대기
        while g_audio.state.name == "PROCESSING":
            time.sleep(2)
            g_audio = genai.get_file(g_audio.name)

        # 3. 요약 생성 프롬프트
        prompt = """
        당신은 수업 요약 전문가입니다. 오디오와 PDF를 바탕으로 요약하세요.
        - PDF 페이지 번호를 언급하며 설명할 것.
        - 교수님이 강조한 실습 내용이나 퀴즈 정보를 포함할 것.
        - 마크다운 형식으로 보기 좋게 정리할 것.
        """
        
        response = self.model.generate_content([prompt, g_audio, g_pdf])
        return response.text