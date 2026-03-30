import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# 💡 [최종 필살기] Streamlit Cloud에서 경로 절대 못 잃어버리게 만들기!
# 1. 현재 파일(3_위험패턴_분석.py) 기준 부모 폴더(루트) 찾기
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

# 2. 클라우드 실행 디렉토리와 루트 폴더를 둘 다 강제 주입 (최우선순위 0번)
for path in [root_dir, os.getcwd()]:
    if path not in sys.path:
        sys.path.insert(0, path)

import logic # 이제 1000% 찾습니다!

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

# --- 데이터 로드 ---
@st.cache_data(ttl=60)
def load_data():
    return logic.load_input_logs()

# --- 화면 렌더링 ---
st.title("🔍 위험패턴 분석")
st.markdown("필터 조건에 따른 상세 위반 패턴을 분석합니다.")

# 1. 전체 데이터 불러오기
df = load_data()

# 2. 상단 필터부 (UI)
with st.expander("필터 설정", expanded=True):
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: start_date = st.date_input("시작일", datetime.today() - timedelta(days=7))
    with col2: end_date = st.date_input("종료일", datetime.today())
    with col3: 
        zone_list = ["전체"] + list(df['zone'].dropna().unique()) if not df.empty and 'zone' in df.columns else ["전체"]
        zone_filter = st.selectbox("구역", zone_list)
    with col4: 
        ppe_list = ["전체"] + list(df['missed_ppe'].dropna().unique()) if not df.empty and 'missed_ppe' in df.columns else ["전체"]
        ppe_filter = st.selectbox("PPE 종류", ppe_list)
    with col5:
        # 위험 여부 필터 (여기에 따라 그래프가 변신합니다!)
        risk_filter = st.selectbox("위험 여부", ["전체", "위험(미착용)", "정상(착용)"])

# 3. 데이터 필터링 (위험 여부 포함)
if risk_filter == "위험(미착용)":
    risk_val = "O"
elif risk_filter == "정상(착용)":
    risk_val = "X"
else:
    risk_val = None

filtered_df = logic.filter_input_data(
    df, 
    start_date=start_date.strftime("%Y-%m-%d"), 
    end_date=end_date.strftime("%Y-%m-%d"), 
    zone=None if zone_filter == "전체" else zone_filter,
    ppe_type=None if ppe_filter == "전체" else ppe_filter,
    risk_exposure=risk_val # 여기서 logic.py로 값을 넘겨 필터링
)

charts_data = logic.get_analysis_charts(filtered_df)

# 4. 차트 그리기
col1, col2 = st.columns(2)

# [차트 1] 시간대별 위반 건수
with col1:
    st.subheader("⏰ 시간대별 위반 건수")
    df_time = pd.DataFrame(charts_data.get("time_chart", []))
    if not df_time.empty and 'count' in df_time.columns and df_time['count'].sum() > 0:
        fig_time = px.bar(df_time, x="label", y="count")
        fig_time.update_traces(width=0.3, marker_color="#4F8BFF", marker_line_radius=10) 
        st.plotly_chart(apply_toss_style(fig_time), use_container_width=True)
    else: st.warning("데이터가 없습니다.")

# [차트 2] PPE별 위반 건수
with col2:
    st.subheader("🦺 PPE별 위반 건수")
    df_ppe = pd.DataFrame(charts_data.get("ppe_chart", []))
    if not df_ppe.empty and 'count' in df_ppe.columns and df_ppe['count'].sum() > 0:
        fig_ppe = px.bar(df_ppe, x="label", y="count")
        fig_ppe.update_traces(width=0.3, marker_color="#FF6B6B")
        st.plotly_chart(apply_toss_style(fig_ppe), use_container_width=True)
    else: st.warning("데이터가 없습니다.")

col3, col4 = st.columns(2)

# [차트 3] 구역별 준수율
with col3:
    st.subheader("📍 구역별 준수율")
    df_zone = pd.DataFrame(charts_data.get("zone_chart", []))
    if not df_zone.empty and 'compliance_rate' in df_zone.columns and df_zone['compliance_rate'].sum() > 0:
        df_zone["color"] = df_zone["compliance_rate"].apply(lambda x: "#FF4B4B" if x < 50 else "#28A745") 
        fig_zone = go.Figure(data=[go.Bar(x=df_zone["label"], y=df_zone["compliance_rate"], marker_color=df_zone["color"], width=0.3)])
        fig_zone.update_yaxes(range=[0, 100], dtick=20)
        st.plotly_chart(apply_toss_style(fig_zone), use_container_width=True)
    else: st.warning("데이터가 없습니다.")

# [차트 4] 팀별/작업유형별 위반 횟수
with col4:
    chart_key = "team_chart" if "team_chart" in charts_data else "work_type_chart"
    title_text = "👥 팀별 분석" if chart_key == "team_chart" else "🔄 작업유형별 분석"
    
    st.subheader(title_text)
    df_extra = pd.DataFrame(charts_data.get(chart_key, []))
    
    if not df_extra.empty and 'count' in df_extra.columns and df_extra['count'].sum() > 0:
        fig_extra = px.bar(df_extra, x="label", y="count")
        fig_extra.update_traces(width=0.3, marker_color="#8A2BE2")
        st.plotly_chart(apply_toss_style(fig_extra), use_container_width=True)
    else: 
        st.warning("분석 데이터가 없습니다.")