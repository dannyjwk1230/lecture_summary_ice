import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Lecture Mint", layout="wide")
st.title("🎙️ Lecture Mint: 수업 요약 비서")

tab1, tab2 = st.tabs(["새 요약 만들기", "과거 기록"])

with tab1:
    title = st.text_input("수업 제목 (예: 운영체제 3강)")
    col1, col2 = st.columns(2)
    with col1: audio = st.file_uploader("녹음본 (.mp3, .m4a)", type=['mp3', 'm4a'])
    with col2: pdf = st.file_uploader("수업 PDF", type=['pdf'])
    
    if st.button("AI 요약 생성 시작 ✨"):
        if title and audio and pdf:
            with st.spinner("Gemini가 수업을 듣고 분석 중입니다..."):
                files = {"audio": audio, "pdf": pdf}
                data = {"title": title}
                res = requests.post(f"{BACKEND_URL}/api/summarize", files=files, data=data)
                
                if res.status_code == 200:
                    st.markdown("### 📝 요약 결과")
                    st.write(res.json()["summary"])
                else: st.error("요약 실패!")

with tab2:
    if st.button("목록 새로고침 🔄"):
        history = requests.get(f"{BACKEND_URL}/api/history").json()
        for item in history:
            with st.expander(f"{item['title']} ({item['created_at'][:10]})"):
                st.markdown(item['summary'])