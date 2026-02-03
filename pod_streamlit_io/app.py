import streamlit as st
import requests
import json

st.title("Knowledge API 테스트")
st.write("Amazon S3에 대해 질문하는 API를 테스트합니다.")

# 베이스 URL 입력
base_url = st.text_input(
    "API 베이스 URL",
    placeholder="예: http://your-api-endpoint.com",
    help="프로토콜(http://)을 포함한 베이스 URL을 입력하세요",
)

# 엔드포인트 경로 선택
endpoint_options = ["/knowledge"]
endpoint_choice = st.selectbox("엔드포인트 경로", endpoint_options)

if endpoint_choice == "커스텀 경로":
    endpoint = st.text_input("커스텀 경로 입력", value="/knowledge")
else:
    endpoint = endpoint_choice

# 프롬프트 입력
prompt = st.text_area(
    "질문 입력",
    value="Amazon S3가 뭐야?",
    height=100,
    help="API에 전송할 질문을 입력하세요",
)

# 요청 버튼
if st.button("요청 보내기", type="primary"):
    if not base_url:
        st.error("베이스 URL을 입력해주세요!")
    elif not prompt:
        st.error("질문을 입력해주세요!")
    else:
        try:
            # API 엔드포인트 구성
            api_url = f"{base_url.rstrip('/')}{endpoint}"

            # 요청 데이터
            payload = {"prompt": prompt}

            # 요청 정보 표시
            with st.expander("요청 정보", expanded=True):
                st.code(f"POST {api_url}", language="bash")
                st.code(
                    f"curl -X POST {api_url} -H \"Content-Type: application/json\" -d '{json.dumps(payload, ensure_ascii=False)}'",
                    language="bash",
                )
                st.json(payload)

            # POST 요청 보내기
            with st.spinner("요청 중..."):
                response = requests.post(
                    api_url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=30,
                )

            # 응답 표시
            if response.status_code == 200:
                st.success(f"✅ 응답 코드: {response.status_code}")
            elif response.status_code == 404:
                st.error(
                    f"❌ 404 Not Found - 엔드포인트를 찾을 수 없습니다. 다른 경로를 시도해보세요."
                )
            else:
                st.warning(f"⚠️ 응답 코드: {response.status_code}")

            with st.expander("응답 내용", expanded=True):
                try:
                    # JSON 응답인 경우
                    response_json = response.json()
                    st.json(response_json)
                except:
                    # 텍스트 응답인 경우
                    st.text(response.text)

            # 응답 헤더 표시
            with st.expander("응답 헤더"):
                st.json(dict(response.headers))

        except requests.exceptions.ConnectionError:
            st.error(f"❌ 연결 실패: {api_url}에 연결할 수 없습니다.")
        except requests.exceptions.Timeout:
            st.error("❌ 요청 시간 초과: 서버 응답이 너무 오래 걸립니다.")
        except Exception as e:
            st.error(f"❌ 오류 발생: {str(e)}")

# 엔드포인트 테스트 버튼
st.divider()
st.subheader("🔍 엔드포인트 탐색")

col1, col2 = st.columns(2)

with col1:
    if st.button("루트 경로 테스트 (GET)"):
        try:
            test_url = base_url.rstrip("/")
            with st.spinner(f"테스트 중: {test_url}"):
                response = requests.get(test_url, timeout=10)
            st.info(f"GET {test_url} → {response.status_code}")
            st.text(response.text[:500])
        except Exception as e:
            st.error(f"오류: {str(e)}")

with col2:
    if st.button("/docs 경로 테스트 (GET)"):
        try:
            test_url = f"{base_url.rstrip('/')}/docs"
            with st.spinner(f"테스트 중: {test_url}"):
                response = requests.get(test_url, timeout=10)
            st.info(f"GET {test_url} → {response.status_code}")
            if response.status_code == 200:
                st.success("API 문서가 있을 수 있습니다. 브라우저에서 확인해보세요!")
        except Exception as e:
            st.error(f"오류: {str(e)}")

# 사용 예시
with st.sidebar:
    st.header("사용 방법")
    st.markdown(
        """
    1. API 베이스 URL을 입력하세요
    2. 엔드포인트 경로를 선택하세요
    3. 질문을 입력하세요
    4. '요청 보내기' 버튼을 클릭하세요
    

    """
    )

    st.divider()
    st.caption("💡 팁: 엔드포인트 탐색 기능으로 올바른 경로를 찾아보세요!")


# ## 로컬 컴퓨터에서 실행하는 방법

# 1. 필요한 패키지 설치:
#    ```bash
#    pip install -r requirements.txt
#    ```

# 2. Streamlit 앱 실행:
#    ```bash
#    streamlit run app.py
#    ```

# 3. 브라우저가 자동으로 열리며 앱이 실행됩니다.
#    (기본 주소: http://localhost:8501)
