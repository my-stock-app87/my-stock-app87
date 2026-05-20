import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="주식 AI", page_icon="📈")
st.title("📊 나만의 주식 AI 분석기")

# 한글 주식명을 코드로 완벽하게 바꿔주는 시스템
def get_stock_code(search_input):
    search_input = search_input.strip()
    
    # 숫자 6자리를 그냥 입력했다면 그대로 반환
    if search_input.isdigit() and len(search_input) == 6:
        return search_input
        
    # 한글 이름을 입력했을 때 실시간 검색
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        url = f"https://naver.com{requests.utils.quote(search_input)}&q_enc=utf-8&st=1&frm=stock&r_format=json"
        
        response = requests.get(url, headers=headers).json()
        items = response.get('items', [])
        
        if items and len(items) > 0:
            sub_items = items[0]
            if len(sub_items) > 0:
                code = sub_items[0][0]
                name = sub_items[0][1]
                st.success(f"🔍 '{name}' ({code}) 종목을 찾았습니다!")
                return code
    except Exception:
        pass
    return None

# 사용자 입력창
user_search = st.text_input("종목명 또는 코드 6자리 입력 (예: 삼성전자, 에코프로, 005930)", "삼성전자")
market_type = st.selectbox("시장 선택 (이름 검색 시에도 맞춰주세요)", ["코스피 (KS)", "코스닥 (KQ)"])

suffix = ".KS" if market_type == "코스피 (KS)" else ".KQ"

if st.button("실시간 분석 실행"):
    with st.spinner("종목 검색 및 분석 중..."):
        real_code = get_stock_code(user_search)
        
        if not real_code:
            st.error("❌ 종목을 찾을 수 없습니다. 이름이 정확한지 확인해 주세요.")
        else:
            ticker_code = real_code + suffix
            
            # 주가 데이터 다운로드
            df = yf.download(ticker_code, period="3m", interval="1d", multi_level_index=False)
            
            if df.empty:
                st.error("❌ 데이터를 가져오지 못했습니다. 시장 선택(코스피/코스닥)이 종목과 맞는지 확인해 주세요.")
            else:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

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

                st.metric(label="현재 가격", value=f"{current_price:,.0f} 원")
                
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
                st.code(f"대한민국 {user_search} 종목의 최근 테마주 엮임 현황과 대장주 추천해줘.", language="text")
