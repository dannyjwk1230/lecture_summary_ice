from fastapi import FastAPI, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from database import get_db, Lecture
from services import LectureService
import shutil
import os

app = FastAPI()
service = LectureService()

@app.post("/api/summarize")
async def summarize(
    title: str = Form(...),
    audio: UploadFile = File(...),
    pdf: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 임시 저장
    audio_path = f"temp_{audio.filename}"
    pdf_path = f"temp_{pdf.filename}"
    
    with open(audio_path, "wb") as f: shutil.copyfileobj(audio.file, f)
    with open(pdf_path, "wb") as f: shutil.copyfileobj(pdf.file, f)

    try:
        # S3 업로드
        audio_key = service.upload_to_s3(audio_path, f"audio/{audio.filename}")
        pdf_key = service.upload_to_s3(pdf_path, f"pdf/{pdf.filename}")

        # Gemini 요약
        summary_text = service.process_with_gemini(audio_path, pdf_path)

        # DB 저장
        new_lecture = Lecture(
            title=title, audio_key=audio_key, 
            pdf_key=pdf_key, summary=summary_text
        )
        db.add(new_lecture)
        db.commit()

        return {"status": "success", "summary": summary_text}

    finally:
        # 로컬 파일 삭제
        if os.path.exists(audio_path): os.remove(audio_path)
        if os.path.exists(pdf_path): os.remove(pdf_path)

@app.get("/api/history")
async def get_history(db: Session = Depends(get_db)):
    return db.query(Lecture).order_by(Lecture.created_at.desc()).all()