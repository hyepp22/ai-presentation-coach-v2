import os
import time
import random
import tempfile
import streamlit as st
import streamlit.components.v1 as components
import markdown
from google import genai

st.set_page_config(page_title="AI 학생 발표 코치", page_icon="🎤", layout="wide")

# Secrets 또는 환경 변수에서 API 키 불러오기
raw_api_keys = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if not raw_api_keys:
    st.error("서버에 GEMINI_API_KEY 설정이 안 되어 있습니다.")
    st.stop()

# 쉼표(,)로 구분된 키들을 리스트로 분리
api_key_list = [k.strip() for k in raw_api_keys.split(",") if k.strip()]

st.title("🎤 AI 발표 피드백 시스템")
st.write("발표 연습 영상을 올리면 AI 코치가 시각적/청각적 요소를 분석해 드립니다.")

uploaded_file = st.file_uploader("발표 영상 업로드 (MP4, MOV 등)", type=["mp4", "mov", "avi", "mkv"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
    if st.button("AI 분석 요청하기", type="primary"):
        status = st.empty()
        progress = st.progress(0)
        
        tmp_file_path = None
        video_file = None
        
        # 호출할 때마다 등록된 API 키 중 하나를 무작위로 선택 (부하 분산)
        selected_key = random.choice(api_key_list)
        client = genai.Client(api_key=selected_key)
        
        try:
            status.info("1/4: 영상 파일을 준비 중입니다...")
            progress.progress(20)
            suffix = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_file_path = tmp_file.name

            status.info("2/4: 구글 AI 서버로 안전하게 인코딩 전송 중...")
            progress.progress(50)
            video_file = client.files.upload(file=tmp_file_path)

            status.info("3/4: 영상 프레임 및 음성을 분석하고 있습니다...")
            progress.progress(75)
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = client.files.get(name=video_file.name)

            if video_file.state.name == "FAILED":
                raise Exception("Google 서버에서 비디오 변환에 실패했습니다.")

            status.info("4/4: 피드백 리포트를 생성하는 중입니다...")
            progress.progress(90)
            
            prompt = """
            당신은 전문 스피치 코치입니다. 업로드된 영상을 바탕으로 아래 항목을 상세히 피드백하세요.
            1. 🌟 전체 총평
            2. 👁️ 시각적 요소 (시선, 제스처, 자세)
            3. 🗣️ 청각/내용 요소 (속도, 발음, 습관어)
            4. 🚀 핵심 개선 팁 3가지
            """
            
            # 과부하 에러 대비 자동 재시도 로직 & 최신 gemini-3.6-flash 모델
            max_retries = 3
            response = None
            
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[video_file, prompt]
                    )
                    break
                except Exception as api_err:
                    if any(err_code in str(api_err) for err_code in ["503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED"]):
                        if attempt < max_retries - 1:
                            # 실패 시 다른 API 키로 교체하여 재시도
                            alt_key = random.choice(api_key_list)
                            client = genai.Client(api_key=alt_key)
                            status.warning(f"서버 요청을 재조정 중입니다... ({attempt + 1}/{max_retries})")
                            time.sleep(3)
                        else:
                            raise api_err
                    else:
                        raise api_err

            progress.progress(100)
            status.success("분석 완료!")
            
            if response:
                st.session_state["feedback_result"] = response.text

        except Exception as e:
            if any(err_code in str(e) for err_code in ["503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED"]):
                st.error("현재 순간적인 트래픽이 많습니다. 약 30초 후 [AI 분석 요청하기]를 다시 눌러주세요.")
            else:
                st.error(f"오류가 발생했습니다: {e}")
            
        finally:
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
            if video_file:
                try:
                    client.files.delete(name=video_file.name)
                except Exception:
                    pass

# 피드백 리포트 및 인쇄 영역
if "feedback_result" in st.session_state:
    st.markdown("---")
    st.markdown("### 📊 AI 발표 피드백 리포트")
    
    st.markdown(st.session_state["feedback_result"])
    
    html_content = markdown.markdown(st.session_state["feedback_result"])
    
    report_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
                background-color: #f8fafc;
                padding: 20px;
                color: #1e293b;
            }}
            .card {{
                background-color: #ffffff;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            }}
            h1, h2, h3 {{ color: #1e3a8a; }}
            button {{
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 6px;
                cursor: pointer;
                margin-bottom: 20px;
            }}
            button:hover {{ background-color: #1d4ed8; }}
            @media print {{
                button {{ display: none; }}
                body {{ background-color: white; padding: 0; }}
                .card {{ border: none; box-shadow: none; }}
            }}
        </style>
    </head>
    <body>
        <button onclick="window.print()">🖨️ 리포트 인쇄 / PDF 및 이미지로 저장하기</button>
        <div class="card">
            <h2>🎤 AI 발표 피드백 리포트</h2>
            <hr>
            {html_content}
        </div>
    </body>
    </html>
    """
    
    st.markdown("#### 🖨️ 피드백 결과 저장하기")
    components.html(report_html, height=600, scrolling=True)
