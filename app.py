import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
from streamlit_autorefresh import st_autorefresh

# =====================================================
# 설정 (레이아웃을 wide로 변경하여 대시보드 시각화 최적화)
# =====================================================
st.set_page_config(page_title="AI STOCK MASTER PRO", layout="wide")
st.title("🔥 AI STOCK MASTER PRO")

# 🔥 5초마다 자동 새로고침 활성화 (메트릭과 데이터 실시간 반영)
st_autorefresh(interval=5000, key="global_refresh")

# =====================================================
# 데이터 로드 및 최적화 캐싱
# =====================================================
@st.cache_data(ttl=3600)  # 종목 리스트는 하루에 한 번 혹은 드물게 변경되므로 캐시 주기 확장
def stock_list():
    try:
        df = fdr.StockListing("KRX")[["Code", "Name"]]
        # 무효 데이터나 인덱스 중복 방지
        return df.dropna().drop_duplicates(subset=["Name"])
    except:
        # 대비용 하드코딩 샘플 데이터셋
        return pd.DataFrame({"Code": ["005930", "000660"], "Name": ["삼성전자", "SK하이닉스"]})

df_stock = stock_list()
names = df_stock["Name"].tolist()

def code(name):
    row = df_stock[df_stock["Name"] == name]
    if row.empty:
        return None
    return row.iloc[0]["Code"]

@st.cache_data(ttl=10)  # 실시간 데이터 인식을 위해 캐시 생존 주기(TTL) 단축
def get_price(c):
    try:
        if not c:
            return pd.DataFrame()
        df = fdr.DataReader(c)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except:
        return pd.DataFrame()

# =====================================================
# 지표 연산공학
# =====================================================
def ind(df):
    if df is None or df.empty or len(df) < 25:
        return pd.DataFrame()

    df = df.copy()
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # 웰스 와일더(Wells Wilder) 방식 공식 RSI 최적화 구현
    rs = gain.ewm(alpha=1/14, adjust=False).mean() / (loss.ewm(alpha=1/14, adjust=False).mean() + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    return df.dropna().tail(120)

# =====================================================
# 스코어링 시스템 엔진
# =====================================================
def recommendation_score(df):
    if df.empty: return 0
    l = df.iloc[-1]
    s = 0
    if l["Close"] > l["MA5"]: s += 20
    if l["Close"] > l["MA20"]: s += 20
    if l["Volume"] > l["VOL20"] * 2: s += 30
    if 40 < l["RSI"] < 70: s += 20
    return min(s, 100)

def tomorrow_up_probability(df):
    if df.empty: return 0
    l = df.iloc[-1]
    s = 0
    if l["Close"] > l["MA5"]: s += 25
    if l["Close"] > l["MA20"]: s += 20
    if l["Volume"] > l["VOL20"] * 1.5: s += 20
    if 40 < l["RSI"] < 70: s += 20
    if len(df) > 1 and df["Close"].iloc[-1] > df["Close"].iloc[-2]: s += 15
    return min(s, 95)

def power(df):
    if df.empty: return 0
    l = df.iloc[-1]
    s = 0
    if l["Volume"] > l["VOL20"] * 2: s += 40
    if l["Close"] > l["MA20"]: s += 25
    if l["RSI"] < 70: s += 20
    if l["Close"] > l["MA5"]: s += 15
    return min(s, 100)

def buy_price(df):
    if df.empty: return 0, "데이터 없음"
    l = df.iloc[-1]
    if l["RSI"] < 30: return int(l["Close"] * 0.99), "과매도 반등 매수"
    if l["Close"] > l["MA5"]: return int(l["Close"]), "상승 추세 눌림목"
    return int(l["MA20"] * 1.01), "MA20 생명선 지지 매수"

def sell_price(df):
    if df.empty: return 0
    return int(df.iloc[-1]["Close"] * 1.08)

def five_day(df):
    if df is None or df.empty: return pd.DataFrame()
    d = df.tail(5).copy()
    return pd.DataFrame({
        "날짜": d.index.strftime("%Y-%m-%d"),
        "시가": d["Open"].astype(int),
        "고가": d["High"].astype(int),
        "저가": d["Low"].astype(int),
        "종가": d["Close"].astype(int),
        "거래량": d["Volume"].astype(int)
    }).reset_index(drop=True)

# =====================================================
# ⚡ 고속 시장 스캔 연산 엔진 (캐싱을 통한 지연 제거)
# =====================================================
@st.cache_data(ttl=120)  # 무거운 전체 스캔 연산은 2분간 캐싱하여 속도 저하 방지
def scan_market_cached():
    res = []
    # 연산 부하 분산을 위해 시가총액 상위 위주 코스피/코스닥 주요 종목 스캔 (상위 50개 국한)
    target_pool = names[:50]
    
    for n in target_pool:
        c = code(n)
        if not c: continue
        df_raw = get_price(c)
        if df_raw.empty: continue
        df_ind = ind(df_raw)
        if df_ind.empty: continue
        
        res.append({
            "종목": n,
            "현재가": int(df_raw["Close"].iloc[-1]),
            "추천점수": recommendation_score(df_ind),
            "상승확률(%)": tomorrow_up_probability(df_ind),
            "세력점수(%)": power(df_ind)
        })
    
    out_df = pd.DataFrame(res)
    if out_df.empty:
        return pd.DataFrame(columns=["종목", "현재가", "추천점수", "상승확률(%)", "세력점수(%)"])
    return out_df.sort_values("추천점수", ascending=False).reset_index(drop=True)

# =====================================================
# 테마주 사전 매핑 최적화
# =====================================================
theme_map = {
    "AI / 인공지능": ["NAVER", "카카오", "이수페타시스", "솔트룩스"],
    "2차전지 / 배터리": ["에코프로", "포스코홀딩스", "LG에너지솔루션", "삼성SDI"],
    "반도체 소부장": ["삼성전자", "SK하이닉스", "한미반도체", "신성델타테크"],
    "로보틱스 / 자동화": ["레인보우로보틱스", "두산로보틱스", "로보스타"]
}

@st.cache_data(ttl=3600)
def theme_list():
    out = []
    for t, keys in theme_map.items():
        for n in names:
            if any(k in n for k in keys):
                out.append({"테마 매핑": t, "종목명": n, "종목코드": code(n)})
    return pd.DataFrame(out).drop_duplicates().reset_index(drop=True)

# =====================================================
# UI 레이아웃 및 탭 엔진 구동
# =====================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 실시간 종목 분석",
    "🚀 실시간 급등주 TOP 10",
    "🧬 테마별 클러스터링",
    "🧠 AI 내일의 마스터 추천주"
])

# -----------------------------------------------------
# 탭 1: 종목분석
# -----------------------------------------------------
with tab1:
    # 버그 수정: 세션 스테이트를 활용하여 자동 새로고침 시 셀렉트박스가 풀리는 현상 차단
    if "selected_stock" not in st.session_state:
        st.session_state.selected_stock = "삼성전자" if "삼성전자" in names else names[0]

    selected = st.selectbox(
        "분석 대상 종목 선택", 
        names, 
        index=names.index(st.session_state.selected_stock) if st.session_state.selected_stock in names else 0,
        key="stock_selector"
    )
    st.session_state.selected_stock = selected

    stock_code = code(selected)
    if stock_code:
        df_raw = get_price(stock_code)
        
        if not df_raw.empty:
            df = ind(df_raw)
            
            if not df.empty:
                # 최신 현재가 동적 추출
                realtime_price = df_raw["Close"].iloc[-1]
                prev_price = df_raw["Close"].iloc[-2] if len(df_raw) > 1 else realtime_price
                price_delta = int(realtime_price - prev_price)

                # 메트릭 레이아웃 그리드
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("실시간 현재가", f"{int(realtime_price):,} 원", delta=f"{price_delta:,} 원")
                with m2:
                    st.metric("AI 추천 마스터 점수", f"{recommendation_score(df)} / 100 점")
                with m3:
                    prob = tomorrow_up_probability(df)
                    st.metric("내일 자 상승 확률", f"{prob} %")
                with m4:
                    st.metric("세력 수급 평점", f"{power(df)} 점")

                # 경보 알림창
                if prob >= 75:
                    st.success("🔥 시스템 시그널: 고확률 상승 트렌드 포착 단계입니다. 적극 대응을 권장합니다.")
                elif prob >= 50:
                    st.info("📈 시스템 시그널: 완만한 상승 모멘텀 유지 중입니다.")
                else:
                    st.warning("⚠️ 시스템 시그널: 변동성 둔화 또는 단기 매도 흐름 관측. 관망 및 분할 접근 유효.")

                # 상세 테이블 배치
                st.write("#### 📈 최근 5거래일 상세 추이")
                st.dataframe(five_day(df_raw), use_container_width=True, hide_index=True)

                # 가격 전략 카드화 배치
                st.write("#### 💰 AI 최적 타겟 트레이딩 전략")
                bp, reason = buy_price(df)
                sp = sell_price(df)
                
                c1, c2, c3 = st.columns(3)
                c1.info(f"**적정 매수 추천가:** {bp:,} 원")
                c2.success(f"**단기 목표 매도가:** {sp:,} 원")
                c3.light(f"**분석 전략 근거:** {reason}")
            else:
                st.error("보조지표 연산에 필요한 충분한 거래 데이터 일수가 부족합니다.")
        else:
            st.error("데이터 서버로부터 시세 내역을 동기화하지 못했습니다.")

# -----------------------------------------------------
# 탭 2: 급등주 TOP 10
# -----------------------------------------------------
with tab2:
    st.write("#### 🚀 실시간 마스터 추천 점수 기반 가치 급등주 TOP 10")
    with st.spinner("전체 시장 데이터를 연산 및 정렬 중입니다..."):
        market_data = scan_market_cached()
        if not market_data.empty:
            st.dataframe(market_data.head(10), use_container_width=True, hide_index=True)
        else:
            st.info("조건을 충족하는 실시간 수급 종목이 없습니다.")

# -----------------------------------------------------
# 탭 3: 테마주
# -----------------------------------------------------
with tab3:
    st.write("#### 🧬 주요 핵심 시장 주도 테마 구성 정보")
    st.dataframe(theme_list(), use_container_width=True, hide_index=True)

# -----------------------------------------------------
# 탭 4: AI 추천 TOP 5
# -----------------------------------------------------
with tab4:
    st.write("#### 🧠 AI 모델 복합 연산 기준 내일의 베스트 픽 TOP 5")
    with st.spinner("알고리즘 필터 가동 중..."):
        rec_data = scan_market_cached()
        if not rec_data.empty:
            top_5 = rec_data.head(5).copy()
            top_5["포지션 가이드라인"] = "거래량 대폭증 + RSI 추세 수렴에 따른 단기 돌파 매매 대상"
            st.dataframe(top_5, use_container_width=True, hide_index=True)
        else:
            st.info("스캔 데이터가 존재하지 않습니다.")
