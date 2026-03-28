import streamlit as st
import requests
from supabase import create_client

# 설정 (secrets에 key와 url 등록 요망)
BACKEND_URL = st.secrets["BACKEND_URL"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Lecture Mint", layout="wide")

# 세션 상태 관리 (Auth)
# API 요청용 토큰
if "token" not in st.session_state:
    st.session_state.token = None
# 재발급용 토큰
if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None

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
                st.session_state.refresh_token = res.session.refresh_token
                st.rerun()
        except Exception as e:
            st.error(f"실패: {str(e)}")
    st.stop()

# 로그아웃
def logout():
    st.session_state.token = None
    st.session_state.refresh_token = None
    st.rerun()
    
# --- 메인 앱 UI ---
st.sidebar.button("로그아웃", on_click=logout)
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
    # 페이지 설정 오류
    if submit and start_p > end_p:
        st.warning("시작 페이지가 종료 페이지보다 클 수 없습니다.")
    # 정상 작동
    elif submit and audio and pdf:
        with st.spinner("서버에서 분석 중... (대용량 파일은 시간이 걸립니다)"):
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            files = {"audio": audio, "pdf": pdf}
            data = {"title": title, "start_page": start_p, "end_page": end_p}
            # 타임아웃 설정
        try:  
            res = requests.post(f"{BACKEND_URL}/api/v1/summarize", 
                                headers=headers, files=files, data=data, timeout=3600)
            
            result = res.json()
            if result["status"] == "success":
                st.success("분석 완료!")
                st.markdown(result["summary"])
            else:
                st.error(f"오류: {result['message']}")

        except requests.exceptions.Timeout:
            st.error("요청 시간이 초과됐어요. 잠시 후 다시 시도해주세요.")
        except Exception as e:
            st.error(f"연결 오류: {str(e)}")
           
            
     # 파일 업로드 오류         
    elif submit:
            if not audio:
                st.warning("녹음 파일을 업로드해주세요.")
            if not pdf:
                st.warning("PDF 파일을 업로드해주세요.")


with tab2:
    if st.button("내 기록 불러오기 🔄"):
        try:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            history = requests.get(f"{BACKEND_URL}/api/v1/history", headers=headers).json()
            if not history:
                st.info("아직 요약한 강의가 없어요.")
            else:
            for item in history:
                with st.expander(
                    f"{item['title']} ({item['created_at'][:10]})"):
                    st.caption(f"범위: {item['start_page']}p ~ {item['end_page']}p")
                    st.markdown(item['summary'])
        except Exception as e:
            st.error(f"불러오기 실패: {str(e)}")
