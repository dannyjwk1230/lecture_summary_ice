import logging
import os
import shutil

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Header

from services import LectureService
from database import supabase

logger = logging.getLogger(__name__)

app = FastAPI()
service = LectureService()

# 대용량 파일 처리를 위한 임시 폴더 설정
UPLOAD_DIR = "temp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# [보안] Supabase Auth 토큰 검증 의존성
async def get_current_user(authorization: str = Header(None)):
    """
    프론트엔드에서 보낸 Bearer 토큰을 검증하여 
    허가된 사용자만 API를 쓸 수 있게 제한합니다.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 누락되었습니다.")
    
    token = authorization.split(" ")[1]
    try:
        # Supabase에 토큰을 보내 현재 사용자가 누구인지 확인
        user_res = supabase.auth.get_user(token)
        return user_res.user
    except Exception:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

@app.post("/api/v1/summarize")
async def summarize(
    title: str = Form(...),
    start_page: int = Form(...),
    end_page: int = Form(...),
    audio: UploadFile = File(...),
    pdf: UploadFile = File(...),
    user = Depends(get_current_user) # 로그인 안 하면 여기서 차단됨
):
    """
    1. 파일을 임시 저장 (500MB 대응)
    2. Cloudflare R2(10GB 무료)에 업로드
    3. Gemini로 멀티모달 분석
    4. Supabase DB에 최종 결과 저장
    """
    # 사용자별로 겹치지 않게 임시 파일명 설정
    temp_audio_path = os.path.join(UPLOAD_DIR, f"{user.id}_{audio.filename}")
    temp_pdf_path = os.path.join(UPLOAD_DIR, f"{user.id}_{pdf.filename}")

    try:
        # [1] 서버 로컬에 스트리밍 방식으로 임시 저장
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(pdf.file, buffer)

        # [2] Cloudflare R2 업로드 (10GB 무료 저장소 활용)
        # 파일 경로 예시: audio/user_uuid/lecture_name.mp3
        audio_key = f"audio/{user.id}/{audio.filename}"
        pdf_key = f"pdf/{user.id}/{pdf.filename}"
        
        audio_url = service.upload_to_r2(temp_audio_path, audio_key)
        pdf_url = service.upload_to_r2(temp_pdf_path, pdf_key)

        # [3] Gemini 3.1 Flash 멀티모달 분석 실행
        # 서버가 직접 Gemini API와 대화하여 요약본 생성
        summary_text = service.analyze_lecture(temp_audio_path, temp_pdf_path, start_page, end_page)

        # [4] Supabase DB에 메타데이터와 요약 결과 저장
        db_data = {
            "user_id": user.id,      # 어떤 사용자의 데이터인지 기록
            "title": title,
            "audio_url": audio_url,  # R2에 저장된 주소
            "pdf_url": pdf_url,      # R2에 저장된 주소
            "summary": summary_text,
            "start_page": start_page,
            "end_page": end_page
        }
        service.save_metadata(db_data)

        return {"status": "success", "summary": summary_text}

    except HTTPException:
        # 인증 실패 등 의도된 HTTP 응답은 그대로 전달
        raise
    except Exception as e:
        # 서버 로그에는 전체 스택 트레이스 기록 (원인 추적용)
        logger.exception(
            "summarize 실패: user_id=%s title=%s",
            getattr(user, "id", None),
            title,
        )
        # 클라이언트에는 일반적인 메시지 (내부 예외 문자열은 기본 비노출)
        detail = "요약 처리 중 서버 오류가 발생했습니다."
        if os.getenv("DEBUG", "").lower() in ("1", "true", "yes"):
            detail = f"{detail} ({e!s})"
        raise HTTPException(status_code=500, detail=detail)

    finally:
        # [5] 서버 용량 확보를 위해 임시 파일은 즉시 삭제
        if os.path.exists(temp_audio_path): os.remove(temp_audio_path)
        if os.path.exists(temp_pdf_path): os.remove(temp_pdf_path)

@app.get("/api/v1/history")
async def get_history(user = Depends(get_current_user)):
    """사용자 본인이 요약한 내역만 DB에서 불러오기"""
    # RLS가 켜져 있어도 서버(service_role)는 user_id로 필터링하여 안전하게 조회
    response = supabase.table("lectures") \
        .select("*") \
        .eq("user_id", user.id) \
        .order("created_at", desc=True).execute()
    return response.data