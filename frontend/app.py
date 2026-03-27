import streamlit as st
import requests
from supabase import create_client

# 설정
BACKEND_URL = "http://localhost:8000"
SUPABASE_URL = "https://rgbgbowxnawjfraqwkwf.supabase.co"
SUPABASE_KEY = "sb_publishable_3vRSaYFY9o47nxqPTUxPag_G1uPqjXI"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Lecture Mint", layout="wide")

# 세션 상태 관리 (Auth)
if "token" not in st.session_state:
    st.session_state.token = None

# --- 로그인/회원가입 로직 ---
if not st.session_state.token:
    st.title("🔐 접근 권한 필요")
    mode = st.radio("선택", ["로그인", "회원가입"])
    email = st.text_input("이메일")
    pw = st.text_input("비밀번호", type="password")
    
    if st.button("확인"):
        try:
            if mode == "회원가입":
                supabase.auth.sign_up({"email": email, "password": pw})
                st.info("이메일을 확인하거나 가입 승인을 기다려주세요.")
            else:
                res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                st.session_state.token = res.session.access_token
                st.rerun()
        except Exception as e:
            st.error(f"실패: {str(e)}")
    st.stop()

# --- 메인 앱 UI ---
st.sidebar.button("로그아웃", on_click=lambda: st.session_state.update({"token": None}))
st.title("🎓 Lecture Mint: 수업 요약 서비스")

tab1, tab2 = st.tabs(["🚀 분석 요청", "📚 지난 요약"])

with tab1:
    with st.form("lecture_form"):
        title = st.text_input("수업 명")
        c1, c2 = st.columns(2)
        start_p = c1.number_input("시작 페이지", min_value=1, value=1)
        end_p = c2.number_input("종료 페이지", min_value=1, value=10)
        audio = st.file_uploader("녹음본 (최대 500MB)", type=['mp3', 'm4a', 'wav'])
        pdf = st.file_uploader("PDF 교재", type=['pdf'])
        submit = st.form_submit_button("AI 분석 시작")

    if submit and audio and pdf:
        with st.spinner("서버에서 분석 중... (대용량 파일은 시간이 걸립니다)"):
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            files = {"audio": audio, "pdf": pdf}
            data = {"title": title, "start_page": start_p, "end_page": end_p}
            
            res = requests.post(f"{BACKEND_URL}/api/v1/summarize", 
                                headers=headers, files=files, data=data)
            
            result = res.json()

            if res.status_code == 200:
                # 성공했을 때만 요약본 출력
                st.success("분석 완료!")
                st.markdown(result["summary"])
            else:
                # 실패(422 등)했을 때 서버가 보낸 구체적인 이유 출력
                st.error(f"서버 오류 발생 (상태 코드: {res.status_code})")
                st.write("상세 에러 내용:")
                st.json(result)

with tab2:
    if st.button("내 기록 불러오기 🔄"):
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        history = requests.get(f"{BACKEND_URL}/api/v1/history", headers=headers).json()
        for item in history:
            with st.expander(f"{item['title']} ({item['created_at'][:10]})"):
                st.caption(f"범위: {item['start_page']}p ~ {item['end_page']}p")
                st.markdown(item['summary'])