import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="주식 AI", page_icon="📈")
st.title("📊 나만의 주식 AI 분석기")

# 종목 입력 받기
ticker_input = st.text_input("종목코드 6자리 입력 (예: 삼성전자 005930, 에코프로 086520)", "005930")
market_type = st.selectbox("시장 선택", ["코스피 (KS)", "코스닥 (KQ)"])

suffix = ".KS" if market_type == "코스피 (KS)" else ".KQ"
ticker_code = ticker_input.strip() + suffix

if st.button("실시간 분석 실행"):
    with st.spinner("분석 중..."):
        df = yf.download(ticker_code, period="3m", interval="1d")
        
        if df.empty:
            st.error("❌ 종목 코드를 다시 확인해 주세요.")
        else:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # 기술적 지표 계산
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-9)
            df['RSI'] = 100 - (100 / (1 + rs))

            latest = df.iloc[-1]
            prev = df.iloc[-2]
            current_price = float(latest['Close'])
            rsi_val = float(latest['RSI'])

            # 화면 출력
            st.metric(label="현재 가격", value=f"{current_price:,.0f} 원")
            
            # 예측 로직
            if latest['MA5'] > latest['MA20'] and prev['MA5'] <= prev['MA20']:
                st.success("🔮 내일 예측: 상승 가능성 높음! (🚀 매수 타이밍)")
            elif rsi_val < 30:
                st.success("🔮 내일 예측: 과매도 상태로 반등 가능! (🛒 저점 매수)")
            elif latest['MA5'] < latest['MA20'] and prev['MA5'] >= prev['MA20']:
                st.error("🔮 내일 예측: 하락 위험 높음! (🚨 매도 타이밍)")
            elif rsi_val > 70:
                st.error("🔮 내일 예측: 과열 상태로 조정 가능! (💰 익절 검토)")
            else:
                st.warning("🔮 내일 예측: 현재 횡보 구간 (관망 추천)")

            st.line_chart(df['Close'])
            
            st.subheader("🤖 AI에게 물어볼 프롬프트")
            st.code(f"대한민국 {ticker_input} 종목의 최근 테마주 엮임 현황과 대장주 추천해줘.", language="text")
