import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr

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

@st.cache_data(ttl=60) # 지표 캐싱 최적화 (10초 -> 60초로 트래픽 보호)
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
    if df.empty or len(df) < 20: # 최소 20일 이동평균을 위해 조건 변경
        return pd.DataFrame()
        
    df = df.copy()
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20_Vol"] = df["Volume"].rolling(20).mean()

    vol = df["Volume"] / (df["MA20_Vol"] + 1e-10)
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

    # 상태 결정
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
    # 🔥 HTS 스타일 테이블 (Flex 구조 최적화)
    # =====================================================
    st.markdown(f"""
    <div style="background:white;padding:16px;border-radius:12px;border:1px solid #ddd;box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #eee;">
            <span style="font-weight:bold;color:#333;">현재가</span>
            <div style="display:flex;gap:10px;">
                <span style="font-weight:bold;">{price:,}원 ({pct:+.2f}%)</span>
                <span style="color:{color};font-weight:900;">{status}</span>
            </div>
        </div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f9f9f9;">
            <span style="color:#ff4d4d;font-weight:bold;">매수추천가</span>
            <span style="font-weight:bold;color:#ff4d4d;">{buy_price:,}원</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f9f9f9;">
            <span style="color:#4d79ff;font-weight:bold;">매도추천가</span>
            <span style="font-weight:bold;color:#4d79ff;">{sell_price:,}원</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f9f9f9;">
            <span style="font-weight:bold;color:#333;">세력점수</span>
            <span style="font-weight:bold;">{whale:.1f}%</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;">
            <span style="font-weight:bold;color:#333;">상승예측</span>
            <span style="font-weight:bold;color:#e67e22;">{up_prob:.1f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # 🤖 AI 전략
    # =====================================================
    st.markdown("### 🤖 AI 전략")
    if whale >= 70:
        ai = "🚀 세력 강하게 유입된 구간\n단기 급등 가능성 존재\n눌림 매수 전략 유효\n하지만 급락 리스크도 존재\n단타 중심 대응 필요"
    elif whale >= 60:
        ai = "📊 세력 유입 초기 구간\n방향성 아직 불명확\n추격 매수 위험 존재\n지지 확인 필요\n관망 전략 유효"
    elif whale < 35:
        ai = "📉 약세 흐름 지속\n매도 압력 우세\n반등 신호 부족\n손실 관리 필요\n비중 축소 권장"
    else:
        ai = "⚪ 횡보 구간\n뚜렷한 방향 없음\n거래량 중요 구간\n돌파 여부 확인 필요\n관망이 안전"

    st.info(ai)
else:
    st.warning("데이터 부족 또는 분석 불가능한 종목입니다.")

# =====================================================
# ⚡ 단타 TOP5 (오류 수정 및 성능 개선)
# =====================================================
st.markdown("## ⚡ 단타 TOP5")

rows = []
# 중복 연산을 줄이고 속도를 높이기 위해 샘플 수 조절
sample = df_stock.sample(min(50, len(df_stock)))

for _, r in sample.iterrows():
    try:
        c = r["Code"]
        name = r["Name"]

        # [핵심 수정] ind() 함수를 통과시켜 Whale 컬럼을 생성해야 합니다.
        df_target = ind(get_price(c))
        if df_target.empty or len(df_target) < 2:
            continue

        l = df_target.iloc[-1]
        p = df_target.iloc[-2]

        price = int(l["Close"])
        if price > 20000: # 2만 원 이하 동전주/가벼운 주식 타겟 필터
            continue

        vol_pct = (l["Volume"] - p["Volume"]) / (p["Volume"] + 1e-10) * 100
        chg = (l["Close"] - p["Close"]) / (p["Close"] + 1e-10) * 100
        whale = float(l["Whale"]) # 이제 정상적으로 작동합니다.

        # 점수 알고리즘 가중치 적용
        score = (whale * 0.5) + (min(vol_pct, 500) * 0.1) + (max(chg, 0) * 2)

        rows.append({
            "종목": name,
            "현재가": f"{price:,}원",
            "등락률(%)": round(chg, 2),
            "세력점수(%)": round(whale, 1),
            "종합점수": round(score, 1)
        })
    except:
        continue

if rows:
    # 데이터프레임으로 변환 후 종합점수 순으로 정렬하여 상위 5개만 슬라이싱
    df_top5 = pd.DataFrame(rows).sort_values("종합점수", ascending=False).head(5)
    st.dataframe(df_top5, use_container_width=True, hide_index=True)
else:
    st.warning("조건에 맞는 단타 종목을 찾지 못했습니다. 잠시 후 다시 시도해 주세요.")
