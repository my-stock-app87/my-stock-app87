import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 페이지 넓게 쓰기 설정
st.set_page_config(layout="wide")

# =========================
# [한국 주식] 이름/코드 통합 검색 시스템
# =========================
@st.cache_data(ttl=86400)  # 하루에 한 번만 KRX에서 종목 정보 동기화
def load_krx_tickers():
    try:
        # 상장법인목록 데이터를 가공하여 활용
        df_kospi = pd.read_html('https://krx.co.kr', header=0)[0]
        df_kospi = df_kospi[['회사명', '종목코드']].copy()
        df_kospi['종목코드'] = df_kospi['종목코드'].astype(str).str.zfill(6)
        
        # 딕셔너리 형태로 변환 (키: 회사명, 값: 종목코드)
        ticker_dict = pd.Series(df_kospi.종목코드.values, index=df_kospi.회사명).to_dict()
        return ticker_dict
    except:
        # 비상용 기본 우량주 리스트
        return {"삼성전자": "005930", "SK하이닉스": "000660", "현대차": "005380", "네이버": "035420", "카카오": "035720"}

def search_korean_code(query, ticker_dict):
    query = str(query).strip()
    if not query:
        return None, None
        
    # Case 1: 숫자로만 된 코드를 입력했을 때 (예: 005930)
    if query.isdigit():
        code = query.zfill(6)
        name = next((k for k, v in ticker_dict.items() if v == code), "알 수 없는 종목")
        return code, name
        
    # Case 2: 한글/영문 종목명을 입력했을 때 정확히 일치하는지 확인
    if query in ticker_dict:
        return ticker_dict[query], query
        
    # 포함하는 글자가 있는지 부분 검색 (예: '삼성' -> '삼성전자')
    matched_names = [k for k in ticker_dict.keys() if query.lower() in k.lower()]
    if matched_names:
        best_match = matched_names[0]
        return ticker_dict[best_match], best_match
        
    # 미국 주식 티커 형태일 가능성이 있는 경우 (예: AAPL)
    if query.isalpha():
        return query.upper(), query.upper()
        
    return None, None


# =========================
# [글로벌] 전 세계 증시 흐름 가져오기
# =========================
@st.cache_data(ttl=3600)
def load_global_markets():
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
            df = yf.download(ticker, period="5d", interval="1d", auto_adjust=True)
            if df is None or df.empty: continue
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
# 데이터 로딩 시스템 (종목 자동 검증)
# =========================
def load_korean_data(final_code):
    try:
        if final_code.isdigit() and len(final_code) == 6:
            full_code = f"{final_code}.KS"
        else:
            full_code = final_code

        df = yf.download(full_code, period="6mo", interval="1d", auto_adjust=True)

        if (df is None or df.empty) and f"{final_code}.KS" == full_code:
            full_code = f"{final_code}.KQ"
            df = yf.download(full_code, period="6mo", interval="1d", auto_adjust=True)

        if df is None or df.empty:
            full_code = final_code
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
        return None, final_code


# =========================
# 특징 계산 및 핵심 알고리즘
# =========================
def build_features(df):
    try:
        close_series = df["Close"].values.flatten().astype(float)
        volume_series = df["Volume"].values.flatten().astype(float)

        close = pd.Series(close_series)
        volume = pd.Series(volume_series)
        returns = close.pct_change().dropna()

        if len(returns) == 0: return None

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
            "momentum": momentum, "volatility": volatility, "volume_z": volume_z,
            "support_dist": support_dist, "resistance_dist": resistance_dist,
            "trend": trend, "price": price
        }
    except Exception as e:
        st.error(f"특징 계산 중 에러 발생: {e}")
        return None

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

def run_analysis(code, name, df):
    if df is None: return {"error": "데이터 없음"}
    features = build_features(df)
    if features is None: return {"error": "특징 계산 실패"}
    scores = score(features)
    if scores is None: return {"error": "점수 계산 실패"}
    label, color = explain(scores["final_score"])
    return {"종목명": name, "티커": code, "현재가": features["price"], **features, **scores, "상태": label, "color": color}


# =========================
# UI 레이아웃 구성
# =========================
st.title("📊 AI 주식 분석 엔진 (글로벌 매크로 + 한국 대시보드)")

# 상단 글로벌 지수 전광판
st.subheader("🌐 글로벌 시장 주요 지수 흐름")
markets = load_global_markets()

if markets:
    cols = st.columns(len(markets))
    for i, m in enumerate(markets):
        with cols[i]:
            color = "#FF1744" if m["등락률"] >= 0 else "#2979FF"
            sign = "+" if m["등락률"] >= 0 else ""
            st.metric(
                label=m["시장"], 
                value=f"{m['현재가']:.2f}", 
                delta=f"{sign}{m['등락률']:.2f}%"
            )

st.markdown("---")

# 하단 스마트 통합 검색기
st.subheader("🇰🇷 한국 주식 통합 검색 및 AI 분석")
krx_dict = load_krx_tickers()

search_input = st.text_input("종목명 또는 종목코드 6자리를 입력하세요 (예: 삼성전자 / 현대차 / 000660)")

if st.button("분석하기"):
    if not search_input:
        st.warning("검색어를 입력해 주세요.")
    else:
        with st.spinner("KRX 매핑 테이블 대조 및 주가 수집 중..."):
            target_code, target_name = search_korean_code(search_input, krx_dict)
            
            if not target_code:
                st.error(f"'{search_input}'에 해당하는 종목을 국내 상장 목록에서 찾을 수 없습니다.")
            else:
                df, final_ticker = load_korean_data(target_code)

                if df is None:
                    st.error(f"'{target_name}({target_code})' 데이터를 불러오지 못했습니다. 시장 포맷을 확인하세요.")
                else:
                    result = run_analysis(final_ticker, target_name, df)

                    if "error" in result:
                        st.error(result["error"])
                    else:
                        res_col1, res_col2 = st.columns(2)
                        
                        with res_col1:
                            st.write(f"### 📈 {target_name} 상세 지표")
                            st.dataframe(pd.DataFrame([result]).T.rename(columns={0: "수치값"}))
                        
                        with res_col2:
                            st.write("### 🤖 AI 최종 진단 결과")
                            
                            # 통화 단위 예외 처리
                            currency_unit = "원" if ".K" in str(result['티ker']) or str(result['티커']).isdigit() else "\$"
                            price_val = f"{int(result['현재가']):,}원" if currency_unit == "원" else f"\${result['현재가']:.2f}"
                            
                            # ⚠️ 괄호 누락 오류를 수정한 레이아웃 코드 영역
                            st.markdown(
                                f"""
                                <div style='padding:20px; border-radius:10px; background-color:#f0f2f6; text-align:center;'>
