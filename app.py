import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import feedparser

st.set_page_config(page_title="주식주신 PRO", layout="centered")

st.markdown("## 🔥 주식주신 PRO")

# =====================================================
# 🔥 안전 데이터 로딩 (핵심)
# =====================================================
@st.cache_data(ttl=3600)
def load_stock():
    try:
        df = fdr.StockListing("KRX")
        df = df.dropna()
        return df[["Code", "Name"]]
    except:
        return pd.DataFrame({"Code": [], "Name": []})

df_stock = load_stock()
names = df_stock["Name"].dropna().tolist()

def code(name):
    try:
        return df_stock[df_stock["Name"] == name]["Code"].values[0]
    except:
        return None

@st.cache_data(ttl=10)
def get_price(c):
    try:
        df = fdr.DataReader(str(c))
        return df.tail(120)
    except:
        return pd.DataFrame()

# =====================================================
# 🔥 지표 (안전버전)
# =====================================================
def ind(df):
    df = df.copy()

    if len(df) < 10:
        return df

    df["MA5"] = df["Close"].rolling(5).mean()

    vol = df["Volume"] / (df["Volume"].rolling(20).mean() + 1e-10)
    trend = (df["Close"] - df["MA5"]) / (df["MA5"] + 1e-10)
    power = (df["Close"] - df["Open"]) / (df["Open"] + 1e-10) * 100

    df["Whale"] = np.clip(vol * 40 + trend * 30 + power * 10, 0, 100)
    df["Pred"] = np.clip(df["Whale"] * 0.2, 0, 25)

    df["Volume"] = df["Volume"].fillna(0)

    return df.dropna()

# =====================================================
# 🧠 종합분석
# =====================================================
st.markdown("## 🧠 종합분석")

if len(names) == 0:
    st.error("종목 데이터 로딩 실패")
    st.stop()

name = st.selectbox("종목 선택", names)
c = code(name)

df = ind(get_price(c))

if not df.empty and len(df) > 2:

    l = df.iloc[-1]
    p = df.iloc[-2]

    price = int(l["Close"])
    pct = (price - p["Close"]) / (p["Close"] + 1e-10) * 100

    buy_price = int(price * 0.98)
    sell_price = int(price * 1.04)

    whale = float(l["Whale"])
    vol_pct = (l["Volume"] - p["Volume"]) / (p["Volume"] + 1e-10) * 100

    up_prob = np.clip(whale * 0.7, 0, 95)

    # 상태
    if whale >= 65 and vol_pct > 0:
        status = "🟥 매수구간"
        color = "#ff4d4d"
    elif whale < 35:
        status = "🟦 매도구간"
        color = "#4d79ff"
    else:
        status = "⚪ 관망"
        color = "#999"

    # =====================================================
    # 🔥 HTS 스타일 테이블
    # =====================================================
    st.markdown(f"""
    <div style="background:white;padding:12px;border-radius:12px;border:1px solid #ddd;">

    <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #eee;">
        <b>현재가</b>
        <div>{price:,}원 ({pct:+.2f}%)</div>
        <div style="color:{color};font-weight:900;">{status}</div>
    </div>

    <div style="display:flex;justify-content:space-between;padding:8px 0;">
        <b style="color:#ff4d4d;">매수</b>
        <div>{buy_price:,}원</div>
    </div>

    <div style="display:flex;justify-content:space-between;padding:8px 0;">
        <b style="color:#4d79ff;">매도</b>
        <div>{sell_price:,}원</div>
    </div>

    <div style="display:flex;justify-content:space-between;padding:8px 0;">
        <b>세력</b>
        <div>{whale:.1f}%</div>
    </div>

    <div style="display:flex;justify-content:space-between;padding:8px 0;">
        <b>예측</b>
        <div>{up_prob:.1f}%</div>
    </div>

    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # 🤖 AI 전략 (5줄)
    # =====================================================
    st.markdown("### 🤖 AI 전략")

    if whale >= 70:
        ai = """🚀 세력 강하게 유입된 구간
단기 급등 가능성 존재
눌림 매수 전략 유효
하지만 급락 리스크도 존재
단타 중심 대응 필요"""
    elif whale >= 60:
        ai = """📊 세력 유입 초기 구간
방향성 아직 불명확
추격 매수 위험 존재
지지 확인 필요
관망 전략 유효"""
    elif whale < 35:
        ai = """📉 약세 흐름 지속
매도 압력 우세
반등 신호 부족
손실 관리 필요
비중 축소 권장"""
    else:
        ai = """⚪ 횡보 구간
뚜렷한 방향 없음
거래량 중요 구간
돌파 여부 확인 필요
관망이 안전"""

    st.info(ai)

else:
    st.warning("데이터 부족")

# =====================================================
# ⚡ 단타 TOP5 (완전 안전 + 빠름)
# =====================================================
st.markdown("## ⚡ 단타 TOP5")

rows = []

sample = df_stock.sample(min(80, len(df_stock)))

for _, r in sample.iterrows():

    try:
        c = r["Code"]
        name = r["Name"]

        df2 = get_price(c)
        if df2.empty or len(df2) < 10:
            continue

        l = df2.iloc[-1]
        p = df2.iloc[-2]

        price = int(l["Close"])

        if price > 20000:
            continue

        vol_pct = (l["Volume"] - p["Volume"]) / (p["Volume"] + 1e-10) * 100
        chg = (l["Close"] - p["Close"]) / (p["Close"] + 1e-10) * 100
        whale = float(l.get("Whale", 0))

        score = whale * 0.5 + vol_pct * 0.3 + max(chg, 0) * 2

        rows.append({
            "종목": name,
            "현재가": f"{price:,}원",
            "등락률": round(chg, 2),
            "세력": round(whale, 1),
            "점수": round(score, 1)
        })

        if len(rows) >= 5:
            break

    except:
        continue

if rows:
    st.dataframe(pd.DataFrame(rows).sort_values("점수", ascending=False))
else:
    st.warning("단타 종목 없음")