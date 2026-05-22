import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 페이지 넓게 쓰기 설정
st.set_page_config(layout="wide")

# =========================
# [글로벌] 전 세계 증시 흐름 가져오기
# =========================
@st.cache_data(ttl=3600)  # 1시간 동안 글로벌 데이터 캐싱 (속도 향상)
def load_global_markets():
    # 전 세계 대표 지수 목록 (미국, 한국, 일본, 대만, 독일)
    indices = {
        "🇺🇸 나스닥 (NASDAQ)": "^IXIC",
        "🇺🇸 S&P 500": "^GSPC",
        "🇰🇷 코스피 (KOSPI)": "^KS11",
        "🇰🇷 코스닥 (KOSDAQ)": "^KQ11",
        "🇯🇵 닛케이 225": "^N225",
        "🇹🇼 대만 가권": "^TWII",
        "🇩🇪 독일 DAX": "^GDAXI"
    }
    
    market_summary = []
    
    for name, ticker in indices.items():
        try:
            # 최근 5일치 데이터를 가져와서 전일 대비 등락률 계산
            df = yf.download(ticker, period="5d", interval="1d", auto_adjust=True)
            if df is None or df.empty:
                continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[-1] for col in df.columns]
                
            close_series = df["Close"].values.flatten()
            
            if len(close_series) >= 2:
                current_price = float(close_series[-1])
                prev_price = float(close_series[-2])
                change_rate = ((current_price - prev_price) / prev_price) * 100
                market_summary.append({"시장": name, "현재가": current_price, "등락률": change_rate})
        except:
            continue
            
    return market_summary


# =========================
# [한국 주식] 전용 데이터 로딩 (종목코드 보완)
# =========================
def load_korean_data(code):
    try:
        # 사용자가 숫지만 입력했을 경우 (예: 005930 -> 005930.KS 자동 변환)
        code = str(code).strip()
        if code.isdigit():
            if len(code) == 6:
                # 일반적인 코스피/코스닥은 야후 파이낸스에서 .KS로 먼저 시도 후 없으면 .KQ 시도
                full_code = f"{code}.KS"
            else:
                full_code = code
        else:
            full_code = code

        df = yf.download(full_code, period="6mo", interval="1d", auto_adjust=True)

        # .KS로 안 불려오면 .KQ(코스닥)로 재시도
        if (df is None or df.empty) and f"{code}.KS" == full_code:
            full_code = f"{code}.KQ"
            df = yf.download(full_code, period="6mo", interval="1d", auto_adjust=True)

        if df is None or df.empty:
            return None, full_code

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[-1] for col in df.columns]

        df.columns = [str(col).capitalize() for col in df.columns]
        
        if "Close" not in df.columns or "Volume" not in df.columns:
            if "Price" in df.columns:
                df = df.rename(columns={"Price": "Close"})
            else:
                return None, full_code

        df = df.dropna(subset=["Close", "Volume"])
        df = df.sort_index()

        return df, full_code

    except Exception as e:
        st.error(f"데이터 로드 중 에러 발생: {e}")
        return None, code


# =========================
# 특징 계산
# =========================
def build_features(df):
    try:
        close_series = df["Close"].values.flatten().astype(float)
        volume_series = df["Volume"].values.flatten().astype(float)

        close = pd.Series(close_series)
        volume = pd.Series(volume_series)

        returns = close.pct_change().dropna()

        if len(returns) == 0:
            return None

        pos_count = int((returns.values > 0.02).sum())
        neg_count = int((returns.values < -0.02).sum())
        momentum = float(pos_count - neg_count)

        volatility = float(returns.std()) if not np.isnan(returns.std()) else 0.0

        vol_mean = float(volume.rolling(20).mean().iloc[-1])
        vol_std = float(volume.rolling(20).std().iloc[-1])

        volume_z = 0.0
        if vol_std > 0 and not np.isnan(vol_std):
            last_vol = float(volume.iloc[-1])
            volume_z = (last_vol - vol_mean) / (vol_std + 1e-9)

        support = float(close.rolling(20).min().iloc[-1])
        resistance = float(close.rolling(20).max().iloc[-1])
        price = float(close.iloc[-1])

        support_dist = float((price - support) / price) if price > 0 else 0.0
        resistance_dist = float((resistance - price) / price) if price > 0 else 0.0

        trend = float(returns.mean())

        return {
            "momentum": momentum,
            "volatility": volatility,
            "volume_z": volume_z,
            "support_dist": support_dist,
            "resistance_dist": resistance_dist,
            "trend": trend,
            "price": price
        }
    except Exception as e:
        st.error(f"특징 계산 중 에러 발생: {e}")
        return None


# =========================
# 점수 및 해석 시스템 (기존 로직 유지)
# =========================
def score(features):
    if features is None: return None
    vol = features["volatility"]
    compression = max(0.0, 1 - vol * 10)
    volume_score = min(100.0, abs(features["volume_z"]) * 20)
    structure_score = (max(0.0, 1 - features["support_dist"]) * 50 + max(0.0, 1 - features["resistance_dist"]) * 50)
    momentum_score = features["momentum"] * 10
    trend_score = features["trend"] * 1000

    final_score = (compression * 30 + volume_score * 0.25 + structure_score * 0.2 + momentum_score * 0.15 + trend_score * 0.1)
    return {
        "compression": round(compression, 3), "volume_score": round(volume_score, 2),
        "structure_score": round(structure_score, 2), "momentum_score": round(momentum_score, 2),
        "trend_score": round(trend_score, 2), "final_score": round(final_score, 2)
    }

def explain(s):
    if s > 70: return "🟢 강세 구간", "#00C853"
    elif s > 45: return "🟡 관찰 구간", "#FFD600"
    else: return "🔴 약세 구간", "#D50000"

def run_analysis(code, df):
    if df is None: return {"error": "데이터 없음"}
    features = build_features(df)
    if features is None: return {"error": "특징 계산 실패"}
    scores = score(features)
    if scores is None: return {"error": "점수 계산 실패"}
    label, color = explain(scores["final_score"])
    return {"종목": code, "현재가": features["price"], **features, **scores, "상태": label, "color": color}


# =========================
# UI 레이아웃 구성
# =========================
st.title("📊 AI 주식 분석 엔진 (글로벌 매크로 + 한국 대시보드)")

# 1단: 글로벌 전 세계 증시 실시간 흐름 전광판
st.subheader("🌐 글로벌 시장 주요 지수 흐름")
markets = load_global_markets()

if markets:
    cols = st.columns(len(markets))
    for i, m in enumerate(markets):
        with cols[i]:
            # 상승일 때 빨간색(한국 기준), 하락일 때 파란색 글씨 처리
            color = "#FF1744" if m["등락률"] >= 0 else "#2979FF"
            sign = "+" if m["등락률"] >= 0 else ""
            st.metric(
                label=m["시장"], 
                value=f"{m['현재가']:.2f}", 
                delta=f"{sign}{m['등락률']:.2f}%",
                delta_color="normal"
            )
else:
    st.info("글로벌 시장 지수를 불러오는 중입니다...")

st.markdown("---")

# 2단: 한국 주식 전용 종목 분석기
st.subheader("🇰🇷 한국 주식 정밀 분석 시스템")
code_input = st.text_input("한국 주식 종목코드 6자리 또는 티커 입력 (예: 삼성전자 005930 / SK하이닉스 000660)")

if st.button("분석하기"):
    if not code_input:
        st.warning("종목 코드를 입력하세요")
    else:
        with st.spinner("야후 파이낸스 인덱싱 및 AI 분석 연산 중..."):
            df, final_code = load_korean_data(code_input)

            if df is None:
                st.error(f"데이터를 불러올 수 없습니다. 종목 코드({code_input})를 다시 확인하세요.")
            else:
                result = run_analysis(final_code, df)

                if "error" in result:
                    st.error(result["error"])
                else:
                    # 결과 보기 좋게 레이아웃 분할
                    res_col1, res_col2 = st.columns(2)
                    
                    with res_col1:
                        st.write("### 📈 종합 분석 결과")
                        st.dataframe(pd.DataFrame([result]).T.rename(columns={0: "수치값"}))
                    
                    with res_col2:
                        st.write("### 🤖 AI 최종 진단")
                        st.markdown(
                            f"<div style='padding:20px; border-radius:10px; background-color:#f0f2f6; text-align:center;'>"
                            f"<h4>확정 분석 티커: <span style='color:#333;'>{result['종목']}</span></h4>"
                            f"<h1>현재가: <span style='color:#333;'>{int(result['현재가']):,}원</span></h1>"
                            f"<h2 style='color:{result['color']}; font-size:40px; font-weight:bold;'>{result['상태']}</h2>"
                            f"<h3>최종 AI 스코어: <span style='color:{result['color']};'>{result['final_score']}점</span></h3>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
