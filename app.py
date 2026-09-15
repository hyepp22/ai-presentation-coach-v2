import streamlit as st
import requests
import json
import base64
import os

st.set_page_config(
    page_title="AI 말하기 수행평가 코치",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for polished dashboard look
st.markdown("""
    <style>
    .main-header {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
    }
    .stAlert {
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("⚙️ 발표 및 API 설정")

# Retrieve API key from secrets or user input
api_key_input = st.sidebar.text_input(
    "Google Gemini API Key",
    type="password",
    value=st.secrets.get("GEMINI_API_KEY", ""),
    help="Google AI Studio에서 무료로 발급받은 API 키를 입력하세요."
)

st.sidebar.markdown("---")
st.sidebar.subheader("📋 수행평가 기준 정보")
grade_level = st.sidebar.selectbox("발표자 학년", ["초등학생", "중학생", "고등학생", "대학생/일반"], index=2)
purpose = st.sidebar.selectbox("발표 목적", ["수행평가 발표", "공모전/경진대회", "동아리/연구 발표", "입학/면접 발표"], index=0)

st.sidebar.info("💡 **안내:** 모든 학생은 '큐레이터' 컨셉으로 동일하게 발표하므로, 큐레이터 컨셉에 대한 지적/칭찬은 피드백에서 자동 제외됩니다.")

st.markdown('<div class="main-header">🎙️ AI 말하기 수행평가 코치 (Streamlit)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">아이패드/갤럭시탭 화면녹화(.mov, .mp4) 및 음성 파일 지원 & 말하기 채점기준 맞춤 AI 피드백</div>', unsafe_allow_html=True)

tab_input, tab_config_guide = st.tabs(["📤 발표 자료 제출 및 분석", "⚙️ 대용량 용량 설정 가이드"])

with tab_input:
    col_upload, col_preview = st.columns([3, 2])
    
    with col_upload:
        input_mode = st.radio("제출 방식 선택", ["태블릿 녹화/음성 파일 업로드", "발표 대본 직접 입력"], horizontal=True)
        
        uploaded_file = None
        script_text = ""
        
        if input_mode == "태블릿 녹화/음성 파일 업로드":
            st.markdown("##### 📹 녹화 영상 또는 음성 파일 업로드")
            
            # Expanded file extensions list including .mov for iPad screen recordings
            uploaded_file = st.file_uploader(
                "아이패드/갤럭시탭 화면녹화(.mov, .mp4) 및 음성 파일(.mp3, .m4a 등)을 선택하세요.",
                type=["mp4", "mov", "avi", "webm", "m4a", "mp3", "wav"],
                help="캔바 녹화 파일 또는 태블릿 화면 녹화 동영상/음성 파일 지원"
            )
            
            if uploaded_file is not None:
                file_size_mb = uploaded_file.size / (1024 * 1024)
                st.info(f"📁 선택된 파일: **{uploaded_file.name}** ({file_size_mb:.1f} MB)")
                
                if file_size_mb > 500:
                    st.warning("⚠️ 파일 크기가 500MB를 초과합니다. Streamlit Cloud 메모리 제한으로 인해 분석 중 끊길 수 있으니 500MB 이하 파일이나 음성 추출 업로드를 권장합니다.")
        else:
            st.markdown("##### 📝 발표 대본 직접 입력")
            script_text = st.text_area(
                "발표 대본 전체 내용을 입력하세요.",
                rows=10,
                placeholder="여기에 발표할 대본 전체 내용을 붙여넣으세요. (습관어 '어..', '음..' 등을 포함하면 더 정확히 분석됩니다)"
            )
            
            if st.button("💡 샘플 대본 로드하기"):
                script_text = """안녕하세요! 오늘 명화 해설을 맡은 미술관 큐레이터입니다. 
어... 여러분은 빈센트 반 고흐의 '별이 빛나는 밤'을 보면서 어떤 감정을 느끼시나요? 
음... 저는 밤하늘의 역동적인 소용돌이 형태가 고흐의 불안하면서도 열정적인 내면세계를 잘 표현했다고 생각합니다. 
예를 들어, 어... 그림 중앙의 강렬한 달빛과 별빛은 절망 속에서도 희망을 찾고자했던 그의 의지를 보여줍니다. 
따라서 이 작품은 단순한 풍경화가 아닌, 작가의 영혼을 담은 서사시라고 할 수 있습니다. 
음... 이상으로 큐레이팅을 마치겠습니다. 경청해 주셔서 감사합니다!"""
                st.experimental_rerun()

    with col_preview:
        st.markdown("##### 📌 말하기 수행평가 4대 채점 영역")
        st.markdown("""
        - **1. 발음, 성량 및 속도**: 명확한 전달력과 알맞은 완급 조절
        - **2. 시선 처리 및 발표 태도**: 바른 자세 및 청중과의 교감
        - **3. 내용의 적절성 및 구성력**: 논리적 흐름과 메시지 명확성
        - **4. 시간 및 습관어 관리**: '어...', '음...' 등의 습관어 통제
        """)

def analyze_presentation(api_key, file_data, text_data, grade, target_purpose):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    system_instruction = f"""당신은 대한민국 학교 수행평가 전문 피드백 AI 코치입니다.
[중요 조건]
1. 모든 학생은 '미술관/박물관 큐레이터' 컨셉으로 동일하게 발표합니다. 따라서 "큐레이터 컨셉을 추천한다"거나 "큐레이터처럼 하라"는 식의 컨셉에 대한 지적/칭찬/언급은 피드백에서 완전히 제외하세요.
2. 수행평가 '말하기' 채점 기준에 따라 실용적이고 세부적인 피드백을 제공해야 합니다.

대상 학년: {grade}, 발표 목적: {target_purpose}.

다음 JSON 구조에 맞춰 엄격하게 결과를 생성하십시오:
1. overallScore (0~100)
2. scores: {{ structure (내용 구성), delivery (발음/성량/어조), clarity (전달력/명확성), engagement (청중 태도/시선) }}
3. summary: 말하기 수행평가 전체 한줄평 및 종합 소평
4. speakingCriteria: 말하기 수행평가 4대 필수 평가 항목별 상세 평가 배열
   [
     {{ criteriaName: "발음, 성량 및 속도", score: "상/중/하 또는 점수", feedback: "상세 피드백" }},
     {{ criteriaName: "시선 처리 및 발표 태도", score: "상/중/하 또는 점수", feedback: "상세 피드백" }},
     {{ criteriaName: "내용의 적절성 및 구성력", score: "상/중/하 또는 점수", feedback: "상세 피드백" }},
     {{ criteriaName: "제한시간 및 습관어/추임새 관리", score: "상/중/하 또는 점수", feedback: "상세 피드백" }}
   ]
5. strengths: 말하기 수행평가 기준 잘한 점 3가지 (배열)
6. improvements: 말하기 수행평가 감점 방지를 위한 보완점 3가지 (배열)
7. fillerWordCount: {{ eoh: '어' 횟수, eum: '음' 횟수, total: 전체 습관어 횟수 }}
8. scriptImprovements: 대본 전달력 향상 교정 목록 [{{ original: "기존 문장", suggested: "교정 문장", reason: "교정 이유" }}]
9. expectedQuestions: 예상 청중/교사 질의응답 3개 [{{ id: 1, question: "질문 내용", tip: "답변 팁", sampleAnswer: "모범 답변" }}]"""

    contents = []
    if file_data is not None:
        file_bytes = file_data.read()
        base64_file = base64.b64encode(file_bytes).decode('utf-8')
        mime_type = file_data.type if file_data.type else "audio/mp3"
        
        contents.append({
            "role": "user",
            "parts": [
                {"text": "학생의 말하기 수행평가 발표 파일입니다. 발음, 속도, 습관어, 전달력 등 말하기 채점 기준에 따라 피드백해 주세요."},
                {"inlineData": {"mimeType": mime_type, "data": base64_file}}
            ]
        })
    else:
        contents.append({
            "role": "user",
            "parts": [{"text": f"다음은 학생의 말하기 수행평가 제출 대본입니다. 말하기 평가 기준에 맞춰 피드백해 주세요:\n\n{text_data}"}]
        })

    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "overallScore": {"type": "NUMBER"},
                    "scores": {
                        "type": "OBJECT",
                        "properties": {
                            "structure": {"type": "NUMBER"},
                            "delivery": {"type": "NUMBER"},
                            "clarity": {"type": "NUMBER"},
                            "engagement": {"type": "NUMBER"}
                        },
                        "required": ["structure", "delivery", "clarity", "engagement"]
                    },
                    "summary": {"type": "STRING"},
                    "speakingCriteria": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "criteriaName": {"type": "STRING"},
                                "score": {"type": "STRING"},
                                "feedback": {"type": "STRING"}
                            },
                            "required": ["criteriaName", "score", "feedback"]
                        }
                    },
                    "strengths": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "improvements": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "fillerWordCount": {
                        "type": "OBJECT",
                        "properties": {
                            "eoh": {"type": "NUMBER"},
                            "eum": {"type": "NUMBER"},
                            "total": {"type": "NUMBER"}
                        },
                        "required": ["eoh", "eum", "total"]
                    },
                    "scriptImprovements": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "original": {"type": "STRING"},
                                "suggested": {"type": "STRING"},
                                "reason": {"type": "STRING"}
                            },
                            "required": ["original", "suggested", "reason"]
                        }
                    },
                    "expectedQuestions": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "id": {"type": "NUMBER"},
                                "question": {"type": "STRING"},
                                "tip": {"type": "STRING"},
                                "sampleAnswer": {"type": "STRING"}
                            },
                            "required": ["id", "question", "tip", "sampleAnswer"]
                        }
                    }
                },
                "required": ["overallScore", "scores", "summary", "speakingCriteria", "strengths", "improvements", "fillerWordCount", "scriptImprovements", "expectedQuestions"]
            }
        }
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    
    if response.status_code != 200:
        raise Exception(f"API 호출 오류 ({response.status_code}): {response.text}")

    result = response.json()
    json_text = result["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(json_text)

st.markdown("---")
btn_col1, btn_col2 = st.columns([1, 4])

with btn_col1:
    start_analysis = st.button("🚀 AI 피드백 분석 시작", type="primary", use_container_width=True)

if start_analysis:
    if not api_key_input.strip():
        st.error("🔑 사이드바에 Gemini API Key를 입력해 주세요.")
    elif input_mode == "태블릿 녹화/음성 파일 업로드" and uploaded_file is None:
        st.error("📁 분석할 녹화 영상 또는 음성 파일을 업로드해 주세요.")
    elif input_mode == "발표 대본 직접 입력" and not script_text.strip():
        st.error("📝 분석할 발표 대본을 입력해 주세요.")
    else:
        with st.spinner("🤖 제미나이 AI가 말하기 수행평가 채점 기준을 적용하여 피드백을 생성 중입니다..."):
            try:
                res = analyze_presentation(
                    api_key=api_key_input.strip(),
                    file_data=uploaded_file,
                    text_data=script_text,
                    grade=grade_level,
                    target_purpose=purpose
                )
                st.session_state["analysis_result"] = res
                st.success("✅ 발표 분석 완료!")
            except Exception as e:
                st.error(f"❌ 분석 실패: {str(e)}")

if "analysis_result" in st.session_state:
    data = st.session_state["analysis_result"]
    
    st.markdown("## 📊 말하기 수행평가 AI 피드백 리포트")
    
    # Score Summary Banner
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("총점", f"{data.get('overallScore', 0)} 점")
    m2.metric("내용 구성", f"{data['scores'].get('structure', 0)}점")
    m3.metric("발음/어조", f"{data['scores'].get('delivery', 0)}점")
    m4.metric("전달력", f"{data['scores'].get('clarity', 0)}점")
    m5.metric("발표 태도", f"{data['scores'].get('engagement', 0)}점")
    
    st.info(f"💬 **종합 한줄평:** {data.get('summary', '')}")
    
    st.markdown("### 🏆 항목별 필수 채점 기준 피드백")
    criteria_list = data.get("speakingCriteria", [])
    
    if criteria_list:
        cols = st.columns(len(criteria_list))
        for idx, crit in enumerate(criteria_list):
            with cols[idx % len(cols)]:
                st.markdown(f"**{crit.get('criteriaName')}**")
                st.markdown(f"`평가: {crit.get('score')}`")
                st.caption(crit.get('feedback'))

    st.markdown("---")
    
    # Strengths and Weaknesses
    col_str, col_imp = st.columns(2)
    with col_str:
        st.markdown("### 👍 잘한 점 (우수 항목)")
        for item in data.get("strengths", []):
            st.success(f"• {item}")
            
    with col_imp:
        st.markdown("### 🎯 감점 방지를 위한 보완점")
        for item in data.get("improvements", []):
            st.warning(f"• {item}")
            
    st.markdown("---")
    
    st.markdown("### ✏️ 말하기 전달력 향상을 위한 문장 교정")
    for script_item in data.get("scriptImprovements", []):
        with st.expander(f"🔴 기존: {script_item.get('original')[:30]}..."):
            st.error(f"**기존:** {script_item.get('original')}")
            st.success(f"**추천:** {script_item.get('suggested')}")
            st.caption(f"💡 이유: {script_item.get('reason')}")
            
    st.markdown("---")
    st.markdown("### ❓ 예상 질의응답 (Q&A) 훈련")
    for q in data.get("expectedQuestions", []):
        st.markdown(f"**Q{q.get('id')}. {q.get('question')}**")
        st.caption(f"💡 답변 팁: {q.get('tip')}")
        st.info(f"🗣️ 모범 답변: {q.get('sampleAnswer')}")

with tab_config_guide:
    st.markdown("""
    ### ⚙️ Streamlit 200MB 이상 대용량 업로드 설정 안내
    
    Streamlit 기본 업로드 제한은 200MB입니다. 아이패드 고화질 녹화 영상 등 대용량 파일 업로드를 허용하려면 GitHub 저장소 루트에 아래 설정 파일을 추가하세요.
    
    **`.streamlit/config.toml` 파일 내용:**
    ```toml
    [server]
    maxUploadSize = 1000  # 업로드 허용 용량을 1000MB(1GB)로 확장
    ```
    """)
