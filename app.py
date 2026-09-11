import os
import time
import tempfile
import streamlit as st
from google import genai

st.set_page_config(page_title="AI 학생 발표 코치", page_icon="🎤")

# 서버에 저장된 비밀 API 키 불러오기 (학생들에게 노출 안 됨)
api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("서버에 GEMINI_API_KEY 설정이 안 되어 있습니다.")
    st.stop()

client = genai.Client(api_key=api_key)

st.title("🎤 AI 발표 피드백 시스템")
st.write("발표 연습 영상을 올리면 AI 코치가 시각적/청각적 요소를 분석해 드립니다.")

uploaded_file = st.file_uploader("발표 영상 업로드 (MP4, MOV 등)", type=["mp4", "mov", "avi", "mkv"])

if uploaded_file is not None:
    st.video(uploaded_file)

    if st.button("AI 분석 요청하기", type="primary"):
        status = st.empty()
        progress = st.progress(0)

        try:
            # 1. 서버 임시 파일 저장 (대용량 메모리 에러 방지)
            status.info("1/4: 영상 파일을 준비 중입니다...")
            progress.progress(20)
            suffix = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_file_path = tmp_file.name

            # 2. Google File API 업로드 (대용량 지원 핵심)
            status.info("2/4: 구글 AI 서버로 안전하게 인코딩 전송 중...")
            progress.progress(50)
            video_file = client.files.upload(file=tmp_file_path)

            # 3. 비디오 처리 완료 대기
            status.info("3/4: 영상 프레임 및 음성을 분석하고 있습니다...")
            progress.progress(75)
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = client.files.get(name=video_file.name)

            # 4. Gemini 모델 분석 호출
            status.info("4/4: 피드백 리포트를 생성하는 중입니다...")
            progress.progress(90)

            prompt = """
            당신은 전문 스피치 코치입니다. 업로드된 영상을 바탕으로 아래 항목을 상세히 피드백하세요.
            1. 🌟 전체 총평
            2. 👁️ 시각적 요소 (시선, 제스처, 자세)
            3. 🗣️ 청각/내용 요소 (속도, 발음, 습관어)
            4. 🚀 핵심 개선 팁 3가지
            """

            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=[video_file, prompt]
)


            progress.progress(100)
            status.success("분석 완료!")
            st.markdown("---")
            st.markdown(response.text)

            # 임시 파일 삭제
            os.remove(tmp_file_path)
            client.files.delete(name=video_file.name)

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
