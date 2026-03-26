import os
import time
from google.cloud import storage
import google.generativeai as genai
from database import supabase

class LectureService:
    def __init__(self):
        # 1. Google Cloud Storage 설정 (JSON 키 파일 필요)
        self.gcs_client = storage.Client.from_service_account_json("google-key.json")
        self.bucket = self.gcs_client.bucket(os.getenv("GCS_BUCKET_NAME"))
        
        # 2. Gemini API 설정
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-3.1-flash")

    def upload_to_gcs(self, local_path, blob_name):
        """파일을 GCS로 업로드하고 gs:// 경로를 반환"""
        blob = self.bucket.blob(blob_name)
        blob.upload_from_filename(local_path)
        return f"gs://{self.bucket.name}/{blob_name}"

    def analyze_lecture(self, audio_path, pdf_path, start_pg, end_pg):
        """Gemini 멀티모달 분석: 오디오 + PDF(범위 지정)"""
        # Gemini 전용 임시 저장소에 파일 업로드
        g_audio = genai.upload_file(path=audio_path)
        g_pdf = genai.upload_file(path=pdf_path)

        # 오디오 분석 준비 대기
        while g_audio.state.name == "PROCESSING":
            time.sleep(2)
            g_audio = genai.get_file(g_audio.name)

        # 페이지 범위를 명시한 맞춤형 프롬프트
        prompt = f"""
        강의 녹음본과 PDF 교안을 비교하여 요약해주세요.
        
        [제약 사항]
        - PDF 자료 중 {start_pg}페이지부터 {end_pg}페이지 사이의 내용에 집중할 것.
        - 교수님의 설명과 PDF의 시각 자료(도표, 그림)를 연결하여 정리할 것.
        - 중요 키워드와 타임스탬프를 포함한 마크다운 형식으로 작성할 것.
        """

        response = self.model.generate_content([prompt, g_audio, g_pdf])
        return response.text