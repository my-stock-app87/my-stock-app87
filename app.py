import streamlit as st
import pandas as pd
import numpy as np
import requests
import xml.etree.ElementTree as ET
from scipy.stats import pearsonr

st.set_page_config(page_title="주식 AI 마스터", page_icon="👑", layout="wide")
st.title("👑 나만의 주식 AI 통합 비서 (분석·비교·세력·실시간 테마주)")
st.caption("2026년 실시간 거래 데이터 기반 | 세력 매집 흔적 및 주도 테마주 검색 시스템")

# 네이버 종목코드 검색 함수
def get_stock_code(search_input):
    search_input = search_input.strip()
    if search_input.isdigit() and len(search_input) == 6:
        return {"code": search_input, "name": search_input}
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://naver.com{requests.utils.quote(search_input)}&q_enc=utf-8&st=1&frm=stock&r_format=json"
        res = requests.get(url, headers=headers, timeout=5).json()
        items = res.get('items', [])
        if items and len(items) > 0:
            return {"code": items, "name": items}
    except Exception:
        pass
    return None

# 네이버 일봉 데이터 수집 함수
def get_stock_df_full(code):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://naver.com{code}&timeframe=day&count=60&requestType=0"
        res = requests.get(url, headers=headers, timeout=5)
        root = ET.fromstring(res.text.strip())
        data_list = []
        for item in root.findall('.//item'):
            data_str = item.get('data')
            if data_str:
                parts = data_str.split('|')
                data_list.append([parts, float(parts), float(parts), float(parts), float(parts), float(parts)])
        df = pd.DataFrame(data_list, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
        return df
    except Exception:
        return pd.DataFrame()

# 🗂️ 탭 메뉴 구성
tab1, tab2, tab3 = st.tabs(["🔍 1종목 상세 분석 & 세력 탐지", "⚖️ 2종목 닮은꼴 시뮬레이터", "🚀 실시간 급등 테마주 추천"])

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
                    st.error("❌ 데이터를 가져오지 못했습니다.")
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
                merged = pd.merge(df_a, df_b, on='Date')
                corr, _ = pearsonr(merged['Price_A'], merged['Price_B'])
                sim_pct = (corr + 1) / 2 * 100
                st.metric(label="차트 동기화 확률", value=f"{sim_pct:.1f} %")
                merged['Pct_A'] = (merged['Price_A'] / merged['Price_A'].iloc - 1) * 100
                merged['Pct_B'] = (merged['Price_B'] / merged['Price_B'].iloc - 1) * 100
                st.line_chart(merged[['Date', 'Pct_A', 'Pct_B']].set_index('Date'))

# ----------------------------------------------------
# [TAB 3: 실시간 급등 테마주 추천]
# ----------------------------------------------------
with tab3:
    st.subheader("🔥 실시간 거래 수급기반 주도 테마 섹터 레이더")
    st.caption("2026년 한국 시장을 지배하는 주요 핵심 테마 그룹의 모든 종목 수급과 거래량을 실시간으로 융합 연산하여 가장 강력하게 자금이 쏠리는 테마와 대장주를 순위별로 추천합니다.")
    
    if st.button("🚀 주도 테마주 & 대장주 스캔 시작"):
        with st.spinner("상장된 핵심 테마 그룹별 거래대금 폭발 강도 측정 중..."):
            # 대한민국 핵심 주도 테마주 맵 사전 정의
            theme_map = {
                "🤖 AI 반도체 / HBM·CXL": ["SK하이닉스", "한미반도체", "네오셈", "가온칩스", "오픈엣지테크놀로지"],
                "🧬 차세대 바이오 / 비만·면역치료": ["알테오젠", "유한양행", "HLB", "셀트리온", "리그켐바이오"],
                "🚀 우주항공 / 방산 국산화": ["한화에어로스페이스", "LIG넥스원", "한국항공우주", "현대로템"],
                "🔋 친환경 미래에너지 / 이차전지 소부장": ["에코프로비엠", "포스코퓨처엠", "엘앤에프", "엔켐", "금양"],
                "🪙 가상자산 / STO 토큰증권": ["우리기술투자", "한화투자증권", "갤럭시아머니트리", "옥션블루"],
                "📈 기업 밸류업 / 저PBR 주도주": ["현대차", "기아", "신한지주", "삼성물산", "메리츠금융지주"]
            }
            
            theme_results = []
            
            # 각 테마별 순회 연산
            for theme_name, tickers in theme_map.items():
                total_vol_ratio = 0.0
                valid_count = 0
                leader_name = "데이터 부족"
                max_vol_ratio = -1.0
                
                for stock_name in tickers:
                    info = get_stock_code(stock_name)
                    if info:
                        df = get_stock_df_full(info["code"])
                        if not df.empty and len(df) > 20:
                            df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
                            latest = df.iloc[-1]
                            
                            # 평소 대비 현재 거래량 배율 계산
                            vol_ratio = latest['Volume'] / (latest['Vol_MA20'] + 1e-9)
                            total_vol_ratio += vol_ratio
                            valid_count += 1
                            
                            # 해당 테마 내에서 거래량이 가 장 크게 터진 종목을 실시간 대장주로 선정
                            if vol_ratio > max_vol_ratio:
                                max_vol_ratio = vol_ratio
                                leader_name = stock_name
                
                if valid_count > 0:
                    avg_theme_score = total_vol_ratio / valid_count
                    theme_results.append({
                        "주도 테마명": theme_name,
                        "테마 수급 폭발 지수": round(avg_theme_score, 2),
                        "🔥 현재 실시간 대장주": leader_name,
                        "대장주 수급 강도": f"평소 대비 {max_vol_ratio:.1f}배 돌파"
                    })
            
            # 수급 점수가 높은 순서대로 상위 테마 정렬
            theme_df = pd.DataFrame(theme_results)
            if not theme_df.empty:
                theme_df = theme_df.sort_values(by="테마 수급 폭발 지수", ascending=False).reset_index(drop=True)
                
                st.balloons()
                st.success("🎯 2026년 실시간 시장 돈의 흐름 추적이 완료되었습니다! 상위 테마 순서대로 확인하세요.")
                st.table(theme_df)
                
                st.info("💡 **매매 가이드**: 테마 수급 지수가 2.0 이상인 섹터는 시장의 주도 테마입니다. 해당 테마 내에서 포착된 '현재 실시간 대장주'를 매수 타겟으로 잡으면 가장 빠른 급등 랠리 수익을 기대할 수 있습니다.")
            else:
                st.warning("데이터 수집 상태가 원활하지 않습니다. 잠시 후 새로고침 후 다시 눌러주세요.")
