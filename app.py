import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
from datetime import datetime, timedelta

st.set_page_config(page_title="주식 AI", page_icon="📈")
st.title("📊 나만의 주식 AI 분석기")

# 내부 한국 주식 리스트 변환기
@st.cache_data
def load_korean_stocks():
    try:
        df_krx = fdr.StockListing('KRX')
        return df_krx[['Code', 'Name']].to_dict('records')
    except Exception:
        return []

def get_stock_code(search_input):
    search_input = search_input.strip()
    
    if search_input.isdigit() and len(search_input) == 6:
        return search_input
        
    stocks = load_korean_stocks()
    for stock in stocks:
        if stock['Name'] == search_input:
            st.success(f"🔍 '{stock['Name']}' ({stock['Code']}) 종목을 매칭했습니다!")
            return stock['Code']
    return None

# 사용자 입력창 (이제 시장 선택 메뉴는 필요 없어졌습니다!)
user_search = st.text_input("종목명 또는 코드 6자리 입력 (예: 삼성전자, 에코프로, 005930)", "삼성전자")

if st.button("실시간 분석 실행"):
    with st.spinner("종목 검색 및 주가 데이터 분석 중..."):
        real_code = get_stock_code(user_search)
        
        if not real_code:
            st.error("❌ 종목을 찾을 수 없습니다. 이름이 정확한지 확인해 주세요. (예: 삼성전자)")
        else:
            try:
                # [핵심 수정] 해외 야후 서버 대신, 한국 주식 데이터를 가장 안전하게 가져오는 정식 코드로 전면 교체
                end_date = datetime.today().strftime('%Y-%m-%d')
                start_date = (datetime.today() - timedelta(days=120)).strftime('%Y-%m-%d')
                
                df = fdr.DataReader(real_code, start_date, end_date) [1]
                
                if df.empty:
                    st.error("❌ 주가 데이터를 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.")
                else:
                    df = df.copy()
                    # 컬럼 이름을 대문자로 통일 (Close, Open 등)
                    if 'Close' not in df.columns and 'Close' in df.columns:
                        pass
                    else:
                        # FinanceDataReader는 한글 또는 대문자로 주기 때문에 강제 지정
                        if 'Close' not in df.columns:
                            df['Close'] = df['종가'] if '종가' in df.columns else df.iloc[:, 3]

                    close_series = pd.to_numeric(df['Close'], errors='coerce')
                    
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
                    st.metric(label="현재 가격", value=f"{current_price:,.0f} 원")
                    
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

                    # 주가 그래프 그리기
                    st.line_chart(close_series)
                    
                    st.subheader("🤖 AI에게 물어볼 프롬프트")
                    st.code(f"대한민국 {user_search} 종목의 최근 테마주 엮임 현황과 대장주 추천해줘.", language="text")
            except Exception as e:
                st.error(f"⚠️ 시스템 데이터 연동 오류 발생: {e}")
