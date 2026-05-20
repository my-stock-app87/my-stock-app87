import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import FinanceDataReader as fdr

# =====================================================
# 설정
# =====================================================
st.set_page_config(page_title="AI STOCK MASTER PRO", layout="wide")

today = "2026년 5월 21일"

st.title("🔥 AI STOCK MASTER PRO")
st.caption(f"실시간 트레이딩 분석 시스템 | {today}")

# =====================================================
# 데이터 로드 및 관리
# =====================================================
@st.cache_data(ttl=300)
def stock_list():
    # 시가총액 상위 일부 종목만 샘플링하거나, KRX 전체를 활용합니다.
    # 추천주 탐색 속도를 위해 상위 종목만 필터링해서 쓰시는 것을 권장합니다.
    df = fdr.StockListing("KRX")[["Code", "Name"]]
    return df

df_stock = stock_list()
names = df_stock["Name"].tolist()

def code(name):
    row = df_stock[df_stock["Name"] == name]
    return row.iloc[0]["Code"] if not row.empty else None

@st.cache_data(ttl=60)
def price(c):
    df = fdr.DataReader(c)
    return df

# =====================================================
# 지표 계산 (전체 데이터 계산 후 마지막 120일 슬라이싱)
# =====================================================
def ind(df):
    if len(df) < 30: # 5일전 데이터 확보 및 인디케이터 안정성을 위해 최소 데이터 검증
        return pd.DataFrame()
        
    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    # 계산 후 결측치 제거하고 마지막 120거래일 추출
    return df.dropna().tail(120).reset_index()

# =====================================================
# 매수 / 매도 / 세력 로직
# =====================================================
def buy_price(df):
    l = df.iloc[-1]
    if l["RSI"] < 30:
        return int(l["Close"] * 0.99), "과매도 반등"
    if l["Close"] > l["MA5"]:
        return int(l["Close"]), "상승 추세 눌림"
    return int(l["MA20"] * 1.01), "MA20 지지 매수"

def sell_price(df):
    l = df.iloc[-1]
    return int(l["Close"] * 1.08)

def power(df):
    l = df.iloc[-1]
    s = 0
    if l["Volume"] > l["VOL20"] * 2:
        s += 40
    if l["Close"] > l["MA20"]:
        s += 25
    if l["RSI"] < 70:
        s += 20
    if l["Close"] > l["MA5"]:
        s += 15
    return min(s, 100)

# =====================================================
# 🚀 테이블 생성 데이터 매핑
# =====================================================
def make_table(df, name):
    l = df.iloc[-1]
    
    # 5거래일 전 데이터 추출 (뒤에서 6번째 행)
    # 데이터가 부족할 경우 첫 행을 기본값으로 방어 코드 작성
    prev_5d = df.iloc[-6] if len(df) >= 6 else df.iloc[0]
    
    bp, reason = buy_price(df)
    sp = sell_price(df)
    p = power(df)

    return {
        "종목": name,
        "현재가": int(l["Close"]),
        "RSI": round(l["RSI"], 1),
        "거래량": int(l["Volume"]),
        "5일전 시가": int(prev_5d["Open"]),
        "5일전 최고가": int(prev_5d["High"]),
        "5일전 최저가": int(prev_5d["Low"]),
        "세력확률(%)": p,
        "추천매수가": bp,
        "목표매도가": sp,
        "매수이유": reason
    }

# =====================================================
# 🤖 AI 실시간 추천주 추출 함수
# =====================================================
@st.cache_data(ttl=600) # 연산 속도를 위해 10분 캐싱
def get_ai_recommendations():
    recommend_list = []
    
    # 분석 속도를 위해 시가총액 상위 50개 코스피/코스닥 종목이나 주요 종목 타겟팅 권장
    # 여기서는 빠른 테스트를 위해 리스트 내 앞선 30개 종목을 탐색하는 예시입니다.
    # 전체를 돌리려면 샘플링 범위를 넓히시면 됩니다.
    target_names = names[:40] 
    
    for name in target_names:
        c = code(name)
        if not c: continue
        raw_df = price(c)
        if raw_df.empty: continue
        
        df_ind = ind(raw_df)
        if df_ind.empty: continue
        
        p_score = power(df_ind)
        rsi_val = df_ind.iloc[-1]["RSI"]
        
        # 조건: 세력 확률이 높고 고점 과열(RSI 70이상)이 아닌 종목 탐색
        if p_score >= 60 and rsi_val < 70:
            recommend_list.append({
                "종목": name,
                "세력확률": p_score,
                "현재가": int(df_ind.iloc[-1]["Close"]),
                "목표가": int(df_ind.iloc[-1]["Close"] * 1.08),
                "RSI": round(rsi_val, 1)
            })
            
    # 세력확률이 높은 순서대로 상위 3개 정렬
    df_rec = pd.DataFrame(recommend_list)
    if not df_rec.empty:
        return df_rec.sort_values(by="세력확률", ascending=False).head(3)
    return pd.DataFrame()

# =====================================================
# UI 레이아웃
# =====================================================

# 1. AI 추천주 섹션을 상단에 대시보드 형태로 배치
st.subheader("🤖 AI 실시간 스포트라이트 추천주 (Top 3)")
with st.spinner("전체 시장을 분석하여 세력 매집주를 발굴 중입니다..."):
    df_ai = get_ai_recommendations()
    
if not df_ai.empty:
    cols = st.columns(3)
    for idx, row in enumerate(df_ai.to_dict(orient="records")):
        with cols[idx]:
            st.metric(
                label=f"🔥 추천 {idx+1}위 : {row['종목']}", 
                value=f"{row['현재가']:,} 원", 
                delta=f"목표가 {row['목표가']:,} 원 (+8%)"
            )
            st.caption(f"세력포착 확률: **{row['세력확률']}%** | RSI: {row['RSI']}")
else:
    st.info("현재 기준 조건(세력점수 고득점 및 RSI 안정권)을 만족하는 추천주가 없습니다.")

st.divider()

# 2. 개별 종목 단일 분석 테이블
st.subheader("📊 개별 종목 실시간 트레이딩 분석")

col1, col2 = st.columns([3, 1])

with col1:
    selected = st.selectbox("종목 선택", names)

with col2:
    st.write("") # 간격 정렬용
    st.write("")
    refresh = st.button("🔄 실시간 업데이트", use_container_width=True)

if refresh:
    st.cache_data.clear() # 실시간 강제 새로고침
    st.rerun()

# 3. 분석 실행
if st.button("📌 분석 실행", type="primary"):
    raw_data = price(code(selected))

    if raw_data.empty:
        st.error("데이터가 존재하지 않습니다.")
    else:
        df_final = ind(raw_data)

        if df_final.empty:
            st.error("지표를 계산하기 위한 데이터 기간이 부족합니다.")
        else:
            table = make_table(df_final, selected)

            st.success("📊 AI 트레이딩 결과 분석 성공")
            
            # 컬럼 순서를 보기 편하게 재배치하여 테이블 출력
            show_df = pd.DataFrame([table])[[
                "종목", "현재가", "RSI", "거래량", 
                "5일전 시가", "5일전 최고가", "5일전 최저가", 
                "세력확률(%)", "추천매수가", "목표매도가", "매수이유"
            ]]
            st.dataframe(show_df, hide_index=True, use_container_width=True)

            st.markdown("### 📌 투자 전략 브리핑")
            st.write(f"""
- 현재 **{selected}** 종목은 **RSI {table['RSI']}**의 흐름을 보이고 있습니다.
- 대량 거래량 및 이동평균 정배열을 연산한 결과, **세력 개입 확률은 {table['세력확률(%)']}%** 입니다.
- 5거래일 전 시장의 시가는 **{table['5일전 시가']:,}원**, 최고가는 **{table['5일전 최고가']:,}원**이었습니다.
- AI 가 제안하는 최적 진입가는 **{table['추천매수가']:,}원** 밴드이며, 단기 목표가는 **{table['목표매도가']:,}원**입니다.

👉 **결론:** 현재 주가 위치는 **[{table['매수이유']}]** 전술에 최적화되어 있습니다.
""")
