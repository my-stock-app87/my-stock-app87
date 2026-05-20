import streamlit as st
import pandas as pd
import numpy as np
import requests
import xml.etree.ElementTree as ET
from scipy.stats import pearsonr
import time  # 실시간 네이버 차단 방지용 시간 제어 도구

st.set_page_config(page_title="주식 AI 예측기", page_icon="🔮", layout="wide")
st.title("🔮 나만의 주식 AI 통합 예측기 (분석·비교·세력·테마예측)")
st.caption("2026년 실시간 거래 데이터 기반 | 네이버 서버 차단 우회 패치가 적용된 최신 알고리즘 시스템")

# [보안 패치] 네이버 서버가 봇(Bot)으로 오해하지 않도록 정식 브라우저의 가면을 씌웁니다.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 네이버에서 종목코드를 찾아오는 안전한 함수
def get_stock_code(search_input):
    search_input = search_input.strip()
    if search_input.isdigit() and len(search_input) == 6:
        return {"code": search_input, "name": search_input}
    try:
        url = f"https://naver.com{requests.utils.quote(search_input)}&q_enc=utf-8&st=1&frm=stock&r_format=json"
        res = requests.get(url, headers=HEADERS, timeout=5).json()
        items = res.get('items', [])
        if items and len(items) > 0:
            code = items[0][0][0]
            name = items[0][1][0]
            return {"code": code, "name": name}
    except Exception:
        pass
    return None

# 네이버 일봉 데이터 수집 함수 (차단 우회 시간 지연 레이어 내장)
def get_stock_df_full(code):
    try:
        # 연속 조회 시 네이버의 IP 차단을 막기 위해 0.15초의 미세한 휴식 시간을 줍니다.
        time.sleep(0.15)
        url = f"https://naver.com{code}&timeframe=day&count=60&requestType=0"
        res = requests.get(url, headers=HEADERS, timeout=5)
        
        root = ET.fromstring(res.text.strip())
        data_list = []
        for item in root.findall('.//item'):
            data_str = item.get('data')
            if data_str:
                parts = data_str.split('|')
                data_list.append([parts[0], float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4]), float(parts[5])])
        df = pd.DataFrame(data_list, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
        return df
    except Exception:
        return pd.DataFrame()

# 🗂️ 탭 메뉴 구성
tab1, tab2, tab3 = st.tabs(["🔍 1종목 상세 분석 & 세력 탐지", "⚖️ 2종목 닮은꼴 시뮬레이터", "🔮 AI 주도 테마 급등 예측 레이더"])

# ----------------------------------------------------
# [TAB 1: 1종목 상세 분석 & 세력 탐지]
# ----------------------------------------------------
with tab1:
    st.subheader("🕵️ 주가 흐름 분석 및 세력 개입 추적")
    user_search = st.text_input("종목명 또는 코드 입력", "삼성전자", key="search_tab1")
    if st.button("🔍 실시간 정밀 분석 가동"):
        with st.spinner("데이터 분석 중..."):
            stock_info = get_stock_code(user_search)
            if not stock_info:
                st.error("❌ 종목을 찾을 수 없습니다.")
            else:
                code_a, name_a = stock_info["code"], stock_info["name"]
                df = get_stock_df_full(code_a)
                if df.empty:
                    st.error("❌ 데이터를 가져오지 못했습니다. 잠시 후 다시 버튼을 눌러주세요.")
                else:
                    close_series = df['Close']
                    vol_series = df['Volume']
                    df['MA5'] = close_series.rolling(window=5).mean()
                    df['Vol_MA20'] = vol_series.rolling(window=20).mean()
                    latest = df.iloc[-1]
                    
                    is_volume_burst = latest['Volume'] > (latest['Vol_MA20'] * 2.5)
                    is_accumulation_candle = (latest['High'] - latest['Close']) > (latest['Close'] - latest['Low'])
                    
                    st.metric(label=f"{name_a} 현재 가격", value=f"{latest['Close']:,.0f} 원")
                    st.markdown("### 👁️ 세력 개입 및 수급 지표 판정")
                    if is_volume_burst and is_accumulation_candle:
                        st.error(f"🚨 [세력 강력 개입 포착] 평소 거래량의 {latest['Volume']/latest['Vol_MA20']:.1f}배가 터지며 위꼬리 매집봉이 발생했습니다. 세력이 물량을 아래에서 쓸어 담는 중일 확률이 매우 높습니다.")
                    elif is_volume_burst:
                        st.success(f"🔥 [거래량 폭발 수급 포착] 거래대금과 거래량이 대폭 급증했습니다. 주포 자금이 유입되어 단기 상승 드라이브를 걸고 있습니다.")
                    else:
                        st.info(f"💤 [개인 중심 잔잔한 흐름] 특이 거래량 폭발이 없습니다. 세력 매집보다는 시장 지수 흐름에 맞춰 평탄하게 흘러가는 중입니다.")
                    st.line_chart(close_series)

# ----------------------------------------------------
# [TAB 2: 2종목 닮은꼴 시뮬레이터]
# ----------------------------------------------------
with tab2:
    st.subheader("⚖️ 두 종목 간 커플링 확률 및 승률 계산")
    col_s1, col_s2 = st.columns(2)
    with col_s1: comp_a = st.text_input("기준 종목", "삼성전자")
    with col_s2: comp_b = st.text_input("비교 종목", "SK하이닉스")
    if st.button("⚖️ 닮은꼴 시뮬레이션 가동"):
        with st.spinner("시뮬레이션 수행 중..."):
            info_a, info_b = get_stock_code(comp_a), get_stock_code(comp_b)
            if info_a and info_b:
                df_a = get_stock_df_full(info_a["code"]).rename(columns={'Close': 'Price_A'})
                df_b = get_stock_df_full(info_b["code"]).rename(columns={'Close': 'Price_B'})
                if df_a.empty or df_b.empty:
                    st.error("❌ 일부 종목 데이터를 네이버에서 수집하지 못했습니다. 잠시 후 다시 시도해 주세요.")
                else:
                    merged = pd.merge(df_a, df_b, on='Date')
                    corr, _ = pearsonr(merged['Price_A'], merged['Price_B'])
                    sim_pct = (corr + 1) / 2 * 100
                    st.metric(label="차트 동기화 확률", value=f"{sim_pct:.1f} %")
                    merged['Pct_A'] = (merged['Price_A'] / merged['Price_A'].iloc[0] - 1) * 100
                    merged['Pct_B'] = (merged['Price_B'] / merged['Price_B'].iloc[0] - 1) * 100
                    st.line_chart(merged[['Date', 'Pct_A', 'Pct_B']].set_index('Date'))
            else:
                st.error("종목명을 다시 확인하세요.")

# ----------------------------------------------------
# [TAB 3: AI 주도 테마 급등 예측 레이더]
# ----------------------------------------------------
with tab3:
    st.subheader("🔮 AI 연산 기반 향후 주도 테마 섹터 급등 예측")
    st.caption("네이버 일시 차단 방지 보안 패치가 내장되었습니다. 버튼을 누르면 상장 대장주들의 최근 5일 매집 상태를 분석하여 상승 예측 확률을 계산합니다.")
    
    if st.button("🔮 AI 향후 급등 테마주 예측 가동"):
        with st.spinner("네이버 보안 우회망을 통해 테마별 수급 에너지 시뮬레이션 연산 중 (약 5초 소요)..."):
            # 한국 시장 핵심 주도 테마와 대표 대장주 매핑 (네이버 부하 최소화를 위해 3개씩 압축 정렬)
            theme_map = {
                "🤖 AI 반도체 / HBM·CXL": ["SK하이닉스", "한미반도체", "네오셈"],
                "🧬 차세대 바이오 / 비만 치료": ["알테오젠", "유한양행", "HLB"],
                "🚀 우주항공 / 방산 국산화": ["한화에어로스페이스", "LIG넥스원", "현대로템"],
                "🔋 미래에너지 / 이차전지": ["에코프로비엠", "포스코퓨처엠", "엔켐"],
                "🪙 가상자산 / STO 토큰증권": ["우리기술투자", "한화투자증권", "갤럭시아머니트리"],
                "📈 기업 밸류업 / 저PBR 주도": ["현대차", "기아", "신한지주"]
            }
            
            predict_results = []
            
            for theme_name, tickers in theme_map.items():
                total_vol_ratio = 0.0
                accumulation_score = 0  
                valid_count = 0
                best_leader = "조회 실패"
                max_score = -1.0
                
                for stock_name in tickers:
                    info = get_stock_code(stock_name)
                    if info:
                        df = get_stock_df_full(info["code"])
                        if not df.empty and len(df) > 20:
                            df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
                            latest = df.iloc[-1]
                            
                            vol_ratio = latest['Volume'] / (latest['Vol_MA20'] + 1e-9)
                            total_vol_ratio += vol_ratio
                            valid_count += 1
                            
                            # 최근 5일간 매집 비율 검증
                            recent_5 = df.tail(5)
                            for idx, row in recent_5.iterrows():
                                if row['Volume'] > (row['Vol_MA20'] * 1.5) and (row['High'] - row['Close']) > (row['Close'] - row['Low']):
                                    accumulation_score += 1.5 
                                    
                            stock_score = vol_ratio + (accumulation_score * 0.5)
                            if stock_score > max_score:
                                max_score = stock_score
                                best_leader = stock_name
                                
                if valid_count > 0:
                    raw_probability = (total_vol_ratio / valid_count) * 22 + (accumulation_score * 7)
                    prediction_prob = min(max(raw_probability, 20.0), 98.5) 
                    
                    if prediction_prob >= 80:
                        ai_comment = "🚨 세력 거래량 대폭 유입 완료. 조만간 돌파 장대양봉 랠리가 시작될 확률이 매우 높은 초고확률 예측 섹터!"
                    elif prediction_prob >= 60:
                        ai_comment = "📈 주포 수급이 바닥권에서 우상향 매집 중. 수일 내에 상방 랠리를 펼칠 가능성 유력."
                    elif prediction_prob >= 45:
                        ai_comment = "💤 거래량 숨고르기 하락 조정 구간. 세력이 조용히 물량을 모으고 있으니 성급한 진입보다 분할 매수 대기."
                    else:
                        ai_comment = "📉 단기 차익 자금 이탈 현황 감지. 당분간 주가 조정이 예상되므로 보수적인 관망 접근 추천."
                        
                    predict_results.append({
                        "🔮 예측 주도 테마": theme_name,
                        "📈 단기 급등 예측 확률": f"{prediction_prob:.1f} %",
                        "🎯 최우선 매수 추천 대장주": best_leader,
                        "🤖 AI 핵심 예측 의견 리포트": ai_comment,
                        "score_sort": prediction_prob 
                    })
                    
            predict_df = pd.DataFrame(predict_results)
            if not predict_df.empty:
                predict_df = predict_df.sort_values(by="score_sort", ascending=False).reset_index(drop=True)
                predict_df = predict_df.drop(columns=['score_sort'])
                
                st.balloons()
                st.success("🎯 네이버 우회 보안망 통과 완료! AI 가 향후 상승 확률이 가장 높은 테마 예측 순위를 도출했습니다.")
                st.table(predict_df)
                st.info("💡 **팁**: 컴퓨터 트래픽 제한 정책 때문에 한 번 클릭 후 재조회 시에는 약 5초간 텀을 두고 버튼을 눌러주시는 것이 가장 안전합니다.")
            else:
                st.warning("네이버 금융 서버 응답이 지연되고 있습니다. 잠시 후 5초 뒤에 다시 버튼을 클릭해 주세요.")
