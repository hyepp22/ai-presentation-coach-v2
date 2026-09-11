import os
import time
import tempfile
import streamlit as st
import markdown
from google import genai
from html2image import Html2Image

st.set_page_config(page_title="AI 학생 발표 코치", page_icon="🎤", layout="wide")

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
        
        tmp_file_path = None
        video_file = None
        
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
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[video_file, prompt]
            )

            progress.progress(100)
            status.success("분석 완료!")
            
            st.session_state["feedback_result"] = response.text

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
            
        finally:
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
            if video_file:
                try:
                    client.files.delete(name=video_file.name)
                except Exception:
                    pass

# 분석 결과가 세션에 저장되어 있으면 리포트 표시 및 이미지 다운로드 기능 추가
if "feedback_result" in st.session_state:
    st.markdown("---")
    st.markdown("### 📊 AI 발표 피드백 리포트")
    st.markdown(st.session_state["feedback_result"])
    
    # 마크다운 피드백을 HTML로 변환
    html_body = markdown.markdown(st.session_state["feedback_result"])
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
                background-color: #ffffff;
                color: #222222;
                padding: 30px;
                line-height: 1.6;
            }}
            h1, h2, h3 {{ color: #1e3a8a; }}
            ul, ol {{ padding-left: 20px; }}
            li {{ margin-bottom: 8px; }}
            .container {{
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 25px;
                background-color: #f8fafc;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🎤 AI 발표 피드백 리포트</h2>
            <hr>
            {html_body}
        </div>
    </body>
    </html>
    """
    
    try:
        hti = Html2Image()
        with tempfile.TemporaryDirectory() as tmp_dir:
            img_path = os.path.join(tmp_dir, "feedback.png")
            hti.screenshot(html_str=full_html, save_as="feedback.png", size=(800, 1000))
            generated_img = os.path.join(os.getcwd(), "feedback.png")
            
            if os.path.exists(generated_img):
                with open(generated_img, "rb") as file:
                    img_bytes = file.read()
                
                st.download_button(
                    label="📷 피드백 결과 이미지 파일(PNG)로 다운로드",
                    data=img_bytes,
                    file_name="presentation_feedback.png",
                    mime="image/png"
                )
                os.remove(generated_img)
    except Exception as img_err:
        st.warning("이미지 변환 중 오류가 발생했습니다. (텍스트 복사 기능을 활용해 주세요)")
