import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

st.set_page_config(page_title="주식 AI", page_icon="📈")
st.title("📊 나만의 주식 AI 분석기")

# 네이버 검색을 통해 종목코드를 찾아오는 안전한 함수
def get_stock_code(search_input):
    search_input = search_input.strip()
    if search_input.isdigit() and len(search_input) == 6:
        return search_input
        
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://naver.com{requests.utils.quote(search_input)}&q_enc=utf-8&st=1&frm=stock&r_format=json"
        res = requests.get(url, headers=headers, timeout=5).json()
        items = res.get('items', [])
        if items and len(items) > 0:
            code = items[0][0][0]
            name = items[0][1][0]
            st.success(f"🔍 '{name}' ({code}) 종목을 찾았습니다!")
            return code
    except Exception:
        pass
    return None

# 사용자 입력창
user_search = st.text_input("종목명 또는 코드 6자리 입력 (예: 삼성전자, 에코프로, 005930)", "삼성전자")

if st.button("실시간 분석 실행"):
    with st.spinner("네이버 증권에서 주가 데이터 분석 중..."):
        real_code = get_stock_code(user_search)
        
        if not real_code:
            st.error("❌ 종목을 찾을 수 없습니다. 이름이 정확한지 확인해 주세요.")
        else:
            try:
                # [🚨핵심 변경] 야후 서버를 버리고 네이버 증권 일봉 데이터를 직접 가져옵니다.
                headers = {"User-Agent": "Mozilla/5.0"}
                # 최근 약 100일간의 일봉 데이터를 가져오는 네이버 주소
                url = f"https://naver.com{real_code}&timeframe=day&count=100&requestType=0"
                res = requests.get(url, headers=headers, timeout=5)
                
                # 네이버 XML 데이터를 파이썬 데이터로 파싱
                lines = res.text.split('\n')
                data_list = []
                for line in lines:
                    if 'data' in line:
                        clean_line = line.split('"')[1]
                        parts = clean_line.split('|')
                        # 날짜, 시가, 고가, 저가, 종가, 거래량
                        data_list.append([parts[0], float(parts[4])])
                
                df = pd.DataFrame(data_list, columns=['Date', 'Close'])
                
                if df.empty:
                    st.error("❌ 주가 데이터를 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.")
                else:
                    close_series = df['Close']
                    
                    # 기술적 지표 계산 (5일선, 20일선)
                    df['MA5'] = close_series.rolling(window=5).mean()
                    df['MA20'] = close_series.rolling(window=20).mean()
                    
                    # RSI 지표 자동 계산
                    delta = close_series.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / (loss + 1e-9)
                    df['RSI'] = 100 - (100 / (1 + rs))

                    latest = df.iloc[-1]
                    prev = df.iloc[-2]
                    
                    current_price = float(latest['Close'])
                    rsi_val = float(latest['RSI'])
                    
                    # 화면 가격 출력
                    st.metric(label="현재 가격 (네이버 증권 기준)", value=f"{current_price:,.0f} 원")
                    
                    # AI 매매 알고리즘 결과 리포트
                    if float(latest['MA5']) > float(latest['MA20']) and float(prev['MA5']) <= float(prev['MA20']):
                        st.success("🔮 내일 예측: 상승 가능성 높음! (🚀 골든크로스 매수 타이밍)")
                    elif rsi_val < 30:
                        st.success("🔮 내일 예측: 과매도 상태로 반등 가능! (🛒 저점 매수 찬스)")
                    elif float(latest['MA5']) < float(latest['MA20']) and float(prev['MA5']) >= float(prev['MA20']):
                        st.error("🔮 내일 예측: 하락 위험 높음! (🚨 데드크로스 매도 타이밍)")
                    elif rsi_val > 70:
                        st.error("🔮 내일 예측: 과열 상태로 조정 가능! (💰 익절 분할 매도)")
                    else:
                        st.warning("🔮 내일 예측: 현재 힘겨루기 중 (당분간 관망 추천)")

                    # 주가 그래프 그리기 (날짜를 인덱스로 지정하여 깔끔하게 출력)
                    df.set_index('Date', inplace=True)
                    st.line_chart(df['Close'])
                    
                    st.subheader("🤖 AI에게 물어볼 프롬프트")
                    st.code(f"대한민국 {user_search} 종목의 최근 테마주 엮임 현황과 대장주 추천해줘.", language="text")
            except Exception as e:
                st.error(f"⚠️ 시스템 데이터 연동 오류 발생: {e}")
