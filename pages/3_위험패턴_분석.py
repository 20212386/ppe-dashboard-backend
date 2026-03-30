import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 설정 및 전역 변수 ---
st.set_page_config(page_title="PPE Dashboard", layout="wide")
API_BASE_URL = "http://localhost:8000" # FastAPI 주소

# --- 공통 UI 스타일링 ---
def apply_toss_style(fig):
    """Toss/Apple 감성의 깔끔한 그래프 스타일 적용"""
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#333333"),
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified"
    )
    fig.update_xaxes(showgrid=False, linecolor="#E0E0E0")
    fig.update_yaxes(showgrid=True, gridcolor="#F0F0F0", zeroline=False, dtick=1) # 소수점 방지(dtick=1)
    return fig

# --- 사이드바 네비게이션 ---
st.sidebar.title("PPE Dashboard 🛡️")
page = st.sidebar.radio(
    "메뉴 이동", 
    ["Page 1: 실시간 모니터링", "Page 2: 요약 통계", "Page 3: 위험패턴 분석"]
)

# -----------------------------------------
# Page 1 & 2 (더미 처리)
# -----------------------------------------
if page == "Page 1: 실시간 모니터링":
    st.title("📹 실시간 PPE 모니터링")
    st.info("여기에 실시간 CCTV 화면 및 탐지 로그가 들어갑니다.")

elif page == "Page 2: 요약 통계":
    st.title("📊 요약 통계")
    st.info("여기에 주간/월간 요약 통계 데이터가 들어갑니다.")

# -----------------------------------------
# Page 3 (메인 로직)
# -----------------------------------------
elif page == "Page 3: 위험패턴 분석":
    st.title("🔍 위험패턴 분석")
    st.markdown("필터 조건에 따른 상세 위반 패턴을 분석합니다.")
    
    # --- 상단 필터부 ---
    with st.expander("필터 설정", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            start_date = st.date_input("시작일", datetime.today() - timedelta(days=7))
        with col2:
            end_date = st.date_input("종료일", datetime.today())
        with col3:
            zone_filter = st.selectbox("구역", ["전체", "A구역", "B구역", "C구역"])
        with col4:
            ppe_filter = st.selectbox("PPE 종류", ["전체", "안전모", "안전조끼", "안전화"])

    # --- 데이터 Fetch ---
    # 실제 연동 시 주석 해제하고 사용
    '''
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "zone": None if zone_filter == "전체" else zone_filter,
        "ppe_type": None if ppe_filter == "전체" else ppe_filter
    }
    response = requests.get(f"{API_BASE_URL}/analysis/detail", params=params)
    data = response.json()
    '''
    
    # 테스트용 Mock 데이터 (API 연동 전 뷰 확인용)
    data = {
        "time_series": [{"time": "08:00", "violations": 2}, {"time": "10:00", "violations": 5}, {"time": "14:00", "violations": 8}, {"time": "16:00", "violations": 3}],
        "ppe_violations": [{"ppe": "안전모", "count": 12}, {"ppe": "안전조끼", "count": 8}, {"ppe": "안전화", "count": 4}],
        "zone_compliance": [{"zone": "A구역", "rate": 85}, {"zone": "B구역", "rate": 45}, {"zone": "C구역", "rate": 92}],
        "work_type_repetitions": [{"work_type": "고소작업", "repetitions": 15}, {"work_type": "용접작업", "repetitions": 7}, {"work_type": "밀폐공간", "repetitions": 3}]
    }

    # --- 그래프 렌더링 ---
    col1, col2 = st.columns(2)
    
    # 1. 시간대별 위반 건수 (Line/Bar)
    with col1:
        st.subheader("⏰ 시간대별 위반 건수")
        df_time = pd.DataFrame(data["time_series"])
        fig_time = px.bar(df_time, x="time", y="violations")
        fig_time.update_traces(width=0.3, marker_color="#4F8BFF", marker_line_radius=10) # 얇은 막대(width)
        st.plotly_chart(apply_toss_style(fig_time), use_container_width=True)

    # 2. PPE별 위반 건수
    with col2:
        st.subheader("🦺 PPE별 위반 건수")
        df_ppe = pd.DataFrame(data["ppe_violations"])
        fig_ppe = px.bar(df_ppe, x="ppe", y="count")
        fig_ppe.update_traces(width=0.3, marker_color="#FF6B6B")
        st.plotly_chart(apply_toss_style(fig_ppe), use_container_width=True)

    col3, col4 = st.columns(2)
    
    # 3. 구역별 위험노출 준수율 (초록/빨강 조건부 색상)
    with col3:
        st.subheader("📍 구역별 준수율")
        df_zone = pd.DataFrame(data["zone_compliance"])
        # 50% 미만은 빨간색, 이상은 초록색
        df_zone["color"] = df_zone["rate"].apply(lambda x: "#FF4B4B" if x < 50 else "#28A745") 
        
        fig_zone = go.Figure(data=[
            go.Bar(
                x=df_zone["zone"], 
                y=df_zone["rate"], 
                marker_color=df_zone["color"],
                width=0.3 # 얇은 막대
            )
        ])
        fig_zone.update_yaxes(range=[0, 100], dtick=20) # 퍼센트니까 예외적으로 간격 지정
        st.plotly_chart(apply_toss_style(fig_zone), use_container_width=True)

    # 4. 작업유형별 반복 횟수
    with col4:
        st.subheader("🔄 작업유형별 반복 횟수")
        df_work = pd.DataFrame(data["work_type_repetitions"])
        fig_work = px.bar(df_work, x="work_type", y="repetitions")
        fig_work.update_traces(width=0.3, marker_color="#8A2BE2")
        st.plotly_chart(apply_toss_style(fig_work), use_container_width=True)