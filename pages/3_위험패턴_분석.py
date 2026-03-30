import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 백엔드 API 주소 (환경에 맞게 수정 필요) ---
API_BASE_URL = "http://localhost:8000"

# --- 공통 UI 스타일링 ---
def apply_toss_style(fig):
    """Toss/Apple 감성의 깔끔하고 둥근 그래프 스타일 적용"""
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#333333"),
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified"
    )
    fig.update_xaxes(showgrid=False, linecolor="#E0E0E0")
    fig.update_yaxes(showgrid=True, gridcolor="#F0F0F0", zeroline=False, dtick=1)
    return fig

# --- 화면 렌더링 ---
st.title("🔍 위험패턴 분석")
st.markdown("필터 조건에 따른 상세 위반 패턴을 분석합니다.")

# 1. 상단 필터부
with st.expander("필터 설정", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1: start_date = st.date_input("시작일", datetime.today() - timedelta(days=7))
    with col2: end_date = st.date_input("종료일", datetime.today())
    # API에서 필터 목록을 가져올 수도 있지만, 일단 임의로 고정
    with col3: zone_filter = st.selectbox("구역", ["전체", "A구역", "B구역", "C구역"])
    with col4: ppe_filter = st.selectbox("PPE 종류", ["전체", "안전모", "안전조끼", "안전화"])

# 2. 백엔드 API 호출해서 데이터 가져오기
try:
    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "zone": None if zone_filter == "전체" else zone_filter,
        "ppe_type": None if ppe_filter == "전체" else ppe_filter
    }
    # FastAPI 백엔드의 /analysis/detail 엔드포인트 호출
    response = requests.get(f"{API_BASE_URL}/analysis/detail", params=params)
    response.raise_for_status() # HTTP 에러 발생 시 예외 처리
    api_data = response.json()
    
    # API 응답에서 차트 데이터 추출
    charts_data = api_data.get("charts", {})
    
    # 3. 차트 그리기
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⏰ 시간대별 위반 건수")
        df_time = pd.DataFrame(charts_data.get("time_chart", []))
        if not df_time.empty and df_time.get('count', pd.Series([0])).sum() > 0:
            fig_time = px.bar(df_time, x="label", y="count")
            fig_time.update_traces(width=0.3, marker_color="#4F8BFF", marker_line_radius=10) 
            st.plotly_chart(apply_toss_style(fig_time), use_container_width=True)
        else: st.warning("해당 조건의 데이터가 없습니다.")

    with col2:
        st.subheader("🦺 PPE별 위반 건수")
        df_ppe = pd.DataFrame(charts_data.get("ppe_chart", []))
        if not df_ppe.empty and df_ppe.get('count', pd.Series([0])).sum() > 0:
            fig_ppe = px.bar(df_ppe, x="label", y="count")
            fig_ppe.update_traces(width=0.3, marker_color="#FF6B6B")
            st.plotly_chart(apply_toss_style(fig_ppe), use_container_width=True)
        else: st.warning("해당 조건의 데이터가 없습니다.")

    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("📍 구역별 준수율")
        df_zone = pd.DataFrame(charts_data.get("zone_chart", []))
        if not df_zone.empty and df_zone.get('compliance_rate', pd.Series([0])).sum() > 0:
            df_zone["color"] = df_zone["compliance_rate"].apply(lambda x: "#FF4B4B" if x < 50 else "#28A745") 
            fig_zone = go.Figure(data=[go.Bar(x=df_zone["label"], y=df_zone["compliance_rate"], marker_color=df_zone["color"], width=0.3)])
            fig_zone.update_yaxes(range=[0, 100], dtick=20)
            st.plotly_chart(apply_toss_style(fig_zone), use_container_width=True)
        else: st.warning("해당 조건의 데이터가 없습니다.")

    with col4:
        st.subheader("👥 팀별 위반 횟수")
        df_team = pd.DataFrame(charts_data.get("team_chart", []))
        # 만약 백엔드에서 아직 팀 차트를 안 넘겨준다면, 에러 방지를 위해 빈 df 처리
        if not df_team.empty and df_team.get('count', pd.Series([0])).sum() > 0:
            fig_team = px.bar(df_team, x="label", y="count")
            fig_team.update_traces(width=0.3, marker_color="#8A2BE2")
            st.plotly_chart(apply_toss_style(fig_team), use_container_width=True)
        else: st.warning("팀별 분석 데이터가 없습니다.")

except requests.exceptions.RequestException as e:
    st.error(f"백엔드 서버와 통신 중 에러가 발생했습니다. FastAPI 서버가 실행 중인지 확인해주세요.\n\n에러 상세: {e}")