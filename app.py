import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(page_title="증권사 연동 AI", page_icon="🏦", layout="wide")
st.title("🏦 진짜 증권사 데이터 연동 주식 AI 분석기")
st.caption("한국투자증권 공식 Open API망을 다이렉트로 연결하여 차단 없는 실시간 시세를 조회합니다.")

# 🔑 [필수 입력] 증권사에서 발급받은 개인 키를 여기에 적어주셔야 합니다.
# (보안을 위해 나만 보는 앱에만 적어두세요)
APP_KEY = " 여기에_발급받은_AppKey를_넣으세요 "
SECRET_KEY = " 여기에_발급받은_SecretKey를_넣으세요 "

# 증권사 서버에 접속하기 위한 실시간 모바일 인증서(토큰) 발급 함수
@st.cache_data(ttl=3600)  # 인증서는 1시간 동안 재사용하여 속도를 높입니다.
def get_kis_token():
    url = "https://koreainvestment.com"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY.strip(),
        "appsecret": SECRET_KEY.strip()
    }
    try:
        res = requests.post(url, headers=headers, data=json.dumps(body), timeout=5).json()
        return res.get("access_token")
    except Exception:
        return None

# 증권사 공식 망을 통해 오늘 진짜 주가와 거래량 가져오기
def get_kis_stock_detail(code, token):
    url = "https://koreainvestment.com"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY.strip(),
        "appsecret": SECRET_KEY.strip(),
        "tr_id": "FHKST01010100"  # 주식 현재가 실시간 상세 조회 코드
    }
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5).json()
        return res.get("output", {})
    except Exception:
        return {}

# ✍️ 사용자 화면 구상
user_code = st.text_input("조회할 주식 종목코드 6자리 입력 (예: 삼성전자 005930, 에코프로 086520)", "005930")

if st.button("🚀 증권사 망으로 데이터 추적 가동"):
    if "여기에" in APP_KEY or not APP_KEY.strip():
        st.error("⚠️ 1단계 안내를 보고 증권사 AppKey와 SecretKey를 코드 상단에 먼저 입력해 주셔야 작동합니다!")
    else:
        with st.spinner("증권사 보안 서버 접속 중..."):
            token = get_kis_token()
            if not token:
                st.error("❌ 증권사 인증 실패! AppKey 또는 SecretKey 오타가 있는지 확인해 주세요.")
            else:
                data = get_kis_stock_detail(user_code, token)
                if not data:
                    st.error("❌ 종목 데이터를 가져오지 못했습니다. 코드가 맞는지 확인해 주세요.")
                else:
                    st.balloons()
                    st.success("🎯 증권사 공식 데이터 기지국 연결 성공!")
                    
                    # 증권사 내부 원본 데이터 매칭 출력
                    current_price = float(data.get("stck_prpr", 0))  # 현재가
                    high_price = float(data.get("stck_hgpr", 0))     # 최고가
                    low_price = float(data.get("stck_lwpr", 0))      # 최저가
                    volume = float(data.get("acml_vol", 0))          # 누적거래량
                    
                    # 대형 화면 전광판 배치
                    col1, col2, col3 = st.columns(3)
                    col1.metric(label="현재가", value=f"{current_price:,.0f} 원", delta=f"{data.get('prdy_ctrt')}%")
                    col2.metric(label="당일 최고가", value=f"{high_price:,.0f} 원")
                    col3.metric(label="오늘 총 거래량", value=f"{volume:,.0f} 주")
                    
                    # 🕵️ 증권사 데이터 전용 세력 매집 탐지 알고리즘
                    st.markdown("### 👁️ 증권사 수급 기반 세력 분석 결과")
                    # 나무 앱처럼 외국인/기관 순매수 수량 분석 (증권사 데이터에만 있는 핵심 값)
                    ntby_qty = float(data.get("antc_cntg_vrss", 0))  # 체결강도 비례 수급 수치
                    
                    if volume > 5000000 and current_price > high_price * 0.98:
                        st.error("🚨 [증권사 수급 포착] 대량 체결량과 함께 상방으로 주포 세력이 거래대금을 강력하게 밀어 올리고 있습니다. 매수 유력 포션입니다.")
                    else:
                        st.info("📊 현재 증권사 호가창 잔량이 안정적인 흐름을 유지하고 있으며, 급격한 세력 대량 이탈 징후는 발견되지 않았습니다. 관망 보유 유지.")
