from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Header
import shutil
import os
from services import LectureService
from database import supabase

app = FastAPI()
service = LectureService()

# 대용량 파일 임시 폴더
UPLOAD_DIR = "temp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Supabase Auth 토큰 검증 의존성
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 없습니다.")
    token = authorization.split(" ")[1]
    try:
        # JWT 토큰을 Supabase에 던져 사용자 정보 확인
        user = supabase.auth.get_user(token)
        return user.user
    except Exception:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

@app.post("/api/v1/summarize")
async def summarize(
    title: str = Form(...),
    start_page: int = Form(...),
    end_page: int = Form(...),
    audio: UploadFile = File(...),
    pdf: UploadFile = File(...),
    user = Depends(get_current_user) # 인증된 사용자만 허용
):
    # 1. 서버에 임시 저장 (500MB 스트리밍 대응)
    temp_audio = os.path.join(UPLOAD_DIR, f"{user.id}_{audio.filename}")
    temp_pdf = os.path.join(UPLOAD_DIR, f"{user.id}_{pdf.filename}")
    
    try:
        with open(temp_audio, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        with open(temp_pdf, "wb") as buffer:
            shutil.copyfileobj(pdf.file, buffer)

        # 2. GCS 영구 저장소 업로드
        audio_uri = service.upload_to_gcs(temp_audio, f"audio/{user.id}/{audio.filename}")
        pdf_uri = service.upload_to_gcs(temp_pdf, f"pdf/{user.id}/{pdf.filename}")

        # 3. Gemini 분석 (서버가 중개)
        summary = service.analyze_lecture(temp_audio, temp_pdf, start_page, end_page)

        # 4. Supabase DB에 메타데이터 저장
        supabase.table("lectures").insert({
            "user_id": user.id,
            "title": title,
            "audio_url": audio_uri,
            "pdf_url": pdf_uri,
            "summary": summary,
            "start_page": start_page,
            "end_page": end_page
        }).execute()

        return {"status": "success", "summary": summary}

    finally:
        # 서버 용량 관리를 위해 임시 파일 즉시 삭제
        for p in [temp_audio, temp_pdf]:
            if os.path.exists(p): os.remove(p)

@app.get("/api/v1/history")
async def get_history(user = Depends(get_current_user)):
    # 로그인한 사용자의 데이터만 조회
    response = supabase.table("lectures") \
        .select("*") \
        .eq("user_id", user.id) \
        .order("created_at", desc=True).execute()
    return response.data