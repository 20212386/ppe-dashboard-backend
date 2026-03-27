import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

st.set_page_config(
    page_title="위험패턴 분석",
    layout="wide"
)

API_BASE_URL = "https://ppe-dashboard-backend.onrender.com"


# =========================
# 상태
# =========================
if "p3_analysis_data" not in st.session_state:
    st.session_state["p3_analysis_data"] = None


# =========================
# API
# =========================
def fetch_analysis_data(params: dict):
    try:
        clean_params = {k: v for k, v in params.items() if v not in [None, ""]}
        res = requests.get(f"{API_BASE_URL}/analysis/detail", params=clean_params, timeout=8)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"분석 데이터 조회 실패: {e}")
        return None


# =========================
# 스타일
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 2.5rem;
    padding-bottom: 2rem;
    max-width: 1480px;
}

.main-title {
    font-size: 2.15rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 0.25rem;
    letter-spacing: -0.03em;
}

.sub-title {
    color: #64748b;
    font-size: 1rem;
    margin-bottom: 1.1rem;
}

.filter-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 24px;
    padding: 22px 22px 18px 22px;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
    margin-bottom: 1rem;
}

.section-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 22px;
    padding: 20px 20px 18px 20px;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
    margin-bottom: 1rem;
}

.section-title {
    font-size: 1.12rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 0.4rem;
}

.section-sub {
    color: #64748b;
    font-size: 0.86rem;
    margin-bottom: 0.95rem;
}

.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 18px 20px;
    min-height: 138px;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
}

.metric-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
}

.metric-label {
    color: #64748b;
    font-size: 0.9rem;
    margin-bottom: 10px;
    font-weight: 700;
}

.metric-value {
    color: #0f172a;
    font-size: 1.55rem;
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 10px;
    letter-spacing: -0.02em;
    word-break: keep-all;
}

.metric-badge {
    display: inline-block;
    padding: 6px 11px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 800;
}

.metric-icon {
    width: 50px;
    height: 50px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    flex-shrink: 0;
}

.insight-box {
    border-radius: 14px;
    padding: 11px 13px;
    margin-top: 0.85rem;
    font-size: 0.87rem;
    line-height: 1.55;
    border: 1px solid;
}

.recommend-box {
    background: linear-gradient(135deg, #eef4ff 0%, #dbeafe 100%);
    border: 1px solid #bfdbfe;
    border-radius: 18px;
    padding: 18px;
    color: #1e3a8a;
    font-size: 0.96rem;
    line-height: 1.7;
    font-weight: 700;
}

.analysis-guide {
    background: #f8fafc;
    border: 1px dashed #cbd5e1;
    border-radius: 18px;
    padding: 18px;
    color: #475569;
    font-size: 0.92rem;
    line-height: 1.7;
}

.small-stat {
    color: #64748b;
    font-size: 0.9rem;
    margin: 0.2rem 0 0.9rem 0;
}

.stButton > button {
    border-radius: 14px;
    font-weight: 800;
    min-height: 46px;
}

div[data-testid="stDownloadButton"] > button {
    border-radius: 14px;
    font-weight: 800;
    min-height: 44px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# 렌더 함수
# =========================
def render_metric_card(title, value, badge_text, accent, badge_bg, badge_fg, icon_bg, icon_fg, icon_symbol):
    st.markdown(
        f"""
        <div class="metric-card" style="border-left:6px solid {accent};">
            <div class="metric-top">
                <div>
                    <div class="metric-label">{title}</div>
                    <div class="metric-value">{value}</div>
                    <span class="metric-badge" style="background:{badge_bg}; color:{badge_fg};">{badge_text}</span>
                </div>
                <div class="metric-icon" style="background:{icon_bg}; color:{icon_fg};">{icon_symbol}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_empty_chart_message(message: str):
    st.markdown(
        f"""
        <div class="analysis-guide">
            {message}
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# 헤더
# =========================
st.markdown('<div class="main-title">위험패턴 분석</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">필터 조건에 맞는 반복 위반 패턴을 분석하고 개입 우선순위를 확인합니다</div>',
    unsafe_allow_html=True
)

# =========================
# 필터 카드
# =========================
st.markdown('<div class="filter-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">분석 필터</div>', unsafe_allow_html=True)
st.markdown('<div class="section-sub">현장, 날짜, 작업 조건에 따라 반복 위험 패턴을 좁혀서 볼 수 있습니다</div>', unsafe_allow_html=True)

f1, f2, f3 = st.columns(3)
f4, f5, f6 = st.columns(3)
f7, f8 = st.columns([1, 2])

with f1:
    start_date = st.text_input("시작 날짜", placeholder="예: 2026-03-01")
with f2:
    end_date = st.text_input("종료 날짜", placeholder="예: 2026-03-31")
with f3:
    site = st.selectbox("현장", ["", "현장1", "현장2", "현장3"])

with f4:
    zone = st.selectbox("작업구역", ["", "고소작업구역", "절단작업구역", "자재운반구역", "설비점검구역"])
with f5:
    task_type = st.selectbox("작업유형", ["", "고소작업", "절단작업", "자재운반", "설비점검"])
with f6:
    ppe_type = st.selectbox("PPE 종류", ["", "장갑", "안전모", "랜야드"])

with f7:
    risk_exposure = st.selectbox("위험노출 여부", ["", "O", "X"])
with f8:
    st.markdown("<div style='margin-top: 28.5px;'></div>", unsafe_allow_html=True)
    run_analysis = st.button("분석 실행", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

params = {
    "start_date": start_date or None,
    "end_date": end_date or None,
    "site": site or None,
    "zone": zone or None,
    "task_type": task_type or None,
    "ppe_type": ppe_type or None,
    "risk_exposure": risk_exposure or None,
}

if run_analysis:
    st.session_state["p3_analysis_data"] = fetch_analysis_data(params)

analysis_data = st.session_state["p3_analysis_data"]

if analysis_data:
    count = analysis_data.get("count", 0)
    kpis = analysis_data.get("kpis", {})
    charts = analysis_data.get("charts", {})
    recommend_action = analysis_data.get("recommend_action", "추천 조치가 없습니다.")
    raw_rows = analysis_data.get("raw_rows", [])
else:
    count = 0
    kpis = {}
    charts = {}
    recommend_action = "필터를 설정한 뒤 '분석 실행' 버튼을 눌러주세요."
    raw_rows = []

# 데이터프레임 변환 시 강제로 숫자(int)로 변환하여 에러 방지
time_df = pd.DataFrame(charts.get("time_chart", []))
if not time_df.empty: time_df["count"] = pd.to_numeric(time_df["count"], errors="coerce").fillna(0).astype(int)

ppe_df = pd.DataFrame(charts.get("ppe_chart", []))
if not ppe_df.empty: ppe_df["count"] = pd.to_numeric(ppe_df["count"], errors="coerce").fillna(0).astype(int)

zone_df = pd.DataFrame(charts.get("zone_chart", []))
if not zone_df.empty: zone_df["count"] = pd.to_numeric(zone_df["count"], errors="coerce").fillna(0).astype(int)

task_df = pd.DataFrame(charts.get("task_chart", []))
if not task_df.empty: task_df["count"] = pd.to_numeric(task_df["count"], errors="coerce").fillna(0).astype(int)

download_df = pd.DataFrame(raw_rows)

top_time = kpis.get("top_time") or "-"
top_zone = kpis.get("top_zone") or "-"
top_task = kpis.get("top_task_type") or "-"
top_ppe = kpis.get("top_ppe") or "-"

# =========================
# KPI
# =========================
c1, c2, c3, c4 = st.columns(4)

with c1:
    render_metric_card("가장 위험한 시간대", top_time, "위반 집중", "#ef4444", "#fef2f2", "#b91c1c", "#fef2f2", "#ef4444", "⏰")
with c2:
    render_metric_card("가장 취약한 구역", top_zone, "위험 패턴 상위", "#f97316", "#fff7ed", "#c2410c", "#fff7ed", "#f97316", "📍")
with c3:
    render_metric_card("반복 위험 작업유형", top_task, "반복 분석", "#eab308", "#fefce8", "#a16207", "#fefce8", "#ca8a04", "📈")
with c4:
    render_metric_card("가장 많이 누락된 PPE", top_ppe, "누락 상위", "#a855f7", "#faf5ff", "#7e22ce", "#faf5ff", "#9333ea", "⛑")

st.markdown(f'<div class="small-stat">현재 필터 조건에 맞는 데이터 건수: <b>{count}</b></div>', unsafe_allow_html=True)

if analysis_data is not None and not download_df.empty:
    st.download_button(
        label="분석 결과 CSV 다운로드",
        data=download_df.to_csv(index=False, encoding="utf-8-sig"),
        file_name="analysis_filtered_result.csv",
        mime="text/csv",
        use_container_width=True
    )

# =========================
# 차트 1행
# =========================
r1c1, r1c2 = st.columns(2)

with r1c1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">시간대별 위반 건수</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">시간대별 반복 위반 분포를 확인합니다</div>', unsafe_allow_html=True)

    if analysis_data is None:
        render_empty_chart_message("필터를 설정하고 <b>분석 실행</b>을 누르면 시간대별 위반 건수가 표시됩니다.")
    elif count == 0:
        render_empty_chart_message("🚨 <b>선택한 필터 조건에 맞는 데이터가 0건입니다.</b><br>필터(X 버튼)를 비우거나 다른 조건으로 다시 검색해 보세요.")
    else:
        fig_time = go.Figure()
        if not time_df.empty:
            fig_time.add_trace(
                go.Bar(
                    x=time_df["label"].astype(str).tolist(),
                    y=time_df["count"].tolist(),
                    orientation="v", # 정상적인 세로 막대
                    marker=dict(color="#3b82f6"),
                    hovertemplate="%{x}: %{y}건<extra></extra>"
                )
            )

        fig_time.update_layout(
            height=320, margin=dict(l=10, r=10, t=8, b=8),
            plot_bgcolor="white", paper_bgcolor="white",
            showlegend=False, bargap=0.4,
            xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#334155")),
            yaxis=dict(showgrid=True, gridcolor="#e2e8f0", zeroline=False, tickfont=dict(size=11, color="#475569")) # dtick 삭제로 자동 스케일링
        )
        try: fig_time.update_layout(barcornerradius=12)
        except Exception: pass
        st.plotly_chart(fig_time, use_container_width=True, config={"displayModeBar": False})
        
        st.markdown(f'<div class="insight-box" style="background:#eff6ff; border-color:#bfdbfe; color:#1e3a8a;">💡 패턴 해석: 가장 위반이 집중된 시간대는 <b>{top_time}</b>입니다.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r1c2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">PPE별 위반 건수</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">누락 빈도가 높은 보호구를 확인합니다</div>', unsafe_allow_html=True)

    if analysis_data is None:
        render_empty_chart_message("분석 실행 후 누락 빈도가 높은 PPE 패턴이 표시됩니다.")
    elif count == 0:
        render_empty_chart_message("🚨 <b>선택한 필터 조건에 맞는 데이터가 0건입니다.</b><br>필터(X 버튼)를 비우거나 다른 조건으로 다시 검색해 보세요.")
    else:
        fig_ppe = go.Figure()
        if not ppe_df.empty:
            ppe_color_map = {"장갑": "#f59e0b", "안전모": "#3b82f6", "랜야드": "#8b5cf6"}
            ppe_colors = [ppe_color_map.get(label, "#94a3b8") for label in ppe_df["label"].astype(str)]
            fig_ppe.add_trace(
                go.Bar(
                    x=ppe_df["label"].astype(str).tolist(),
                    y=ppe_df["count"].tolist(),
                    orientation="v",
                    marker=dict(color=ppe_colors),
                    hovertemplate="%{x}: %{y}건<extra></extra>"
                )
            )

        fig_ppe.update_layout(
            height=320, margin=dict(l=10, r=10, t=8, b=8),
            plot_bgcolor="white", paper_bgcolor="white",
            showlegend=False, bargap=0.4,
            xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#334155")),
            yaxis=dict(showgrid=True, gridcolor="#e2e8f0", zeroline=False, tickfont=dict(size=11, color="#475569"))
        )
        try: fig_ppe.update_layout(barcornerradius=12)
        except Exception: pass
        st.plotly_chart(fig_ppe, use_container_width=True, config={"displayModeBar": False})
        
        st.markdown(f'<div class="insight-box" style="background:#fff7ed; border-color:#fed7aa; color:#9a3412;">💡 패턴 해석: 가장 많이 누락되는 보호구는 <b>{top_ppe}</b>입니다.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 차트 2행
# =========================
r2c1, r2c2 = st.columns(2)

with r2c1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">구역별 위반 건수</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">어느 작업구역에서 위반이 반복되는지 확인합니다</div>', unsafe_allow_html=True)

    if analysis_data is None:
        render_empty_chart_message("분석 실행 후 구역별 위반 분포가 표시됩니다.")
    elif count == 0:
        render_empty_chart_message("🚨 <b>선택한 필터 조건에 맞는 데이터가 0건입니다.</b><br>필터(X 버튼)를 비우거나 다른 조건으로 다시 검색해 보세요.")
    else:
        fig_zone = go.Figure()
        if not zone_df.empty:
            zone_colors = ["#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe"][:len(zone_df)]
            fig_zone.add_trace(
                go.Bar(
                    x=zone_df["count"].tolist(),             
                    y=zone_df["label"].astype(str).tolist(), 
                    orientation="h", # 가로 막대
                    marker=dict(color=zone_colors),
                    hovertemplate="%{y}: %{x}건<extra></extra>"
                )
            )

        fig_zone.update_layout(
            height=320, margin=dict(l=10, r=10, t=8, b=8),
            plot_bgcolor="white", paper_bgcolor="white",
            showlegend=False, bargap=0.4,
            xaxis=dict(showgrid=True, gridcolor="#e2e8f0", zeroline=False, tickfont=dict(size=11, color="#475569")),
            yaxis=dict(showgrid=False, autorange="reversed", tickfont=dict(size=12, color="#334155"))
        )
        try: fig_zone.update_layout(barcornerradius=12)
        except Exception: pass
        st.plotly_chart(fig_zone, use_container_width=True, config={"displayModeBar": False})
        
        st.markdown(f'<div class="insight-box" style="background:#eff6ff; border-color:#bfdbfe; color:#1e3a8a;">💡 패턴 해석: 가장 취약한 구역은 <b>{top_zone}</b>입니다.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r2c2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">작업유형별 반복 횟수</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">반복 개입 우선순위가 높은 작업유형을 확인합니다</div>', unsafe_allow_html=True)

    if analysis_data is None:
        render_empty_chart_message("분석 실행 후 작업유형별 반복 패턴이 표시됩니다.")
    elif count == 0:
        render_empty_chart_message("🚨 <b>선택한 필터 조건에 맞는 데이터가 0건입니다.</b><br>필터(X 버튼)를 비우거나 다른 조건으로 다시 검색해 보세요.")
    else:
        fig_task = go.Figure()
        if not task_df.empty:
            fig_task.add_trace(
                go.Bar(
                    x=task_df["count"].tolist(),             
                    y=task_df["label"].astype(str).tolist(), 
                    orientation="h", # 가로 막대
                    marker=dict(color="#8b5cf6"),
                    hovertemplate="%{y}: %{x}건<extra></extra>"
                )
            )

        fig_task.update_layout(
            height=320, margin=dict(l=10, r=10, t=8, b=8),
            plot_bgcolor="white", paper_bgcolor="white",
            showlegend=False, bargap=0.4,
            xaxis=dict(showgrid=True, gridcolor="#e2e8f0", zeroline=False, tickfont=dict(size=11, color="#475569")),
            yaxis=dict(showgrid=False, autorange="reversed", tickfont=dict(size=12, color="#334155"))
        )
        try: fig_task.update_layout(barcornerradius=12)
        except Exception: pass
        st.plotly_chart(fig_task, use_container_width=True, config={"displayModeBar": False})
        
        st.markdown(f'<div class="insight-box" style="background:#faf5ff; border-color:#e9d5ff; color:#6b21a8;">💡 패턴 해석: 반복 개입 우선 작업은 <b>{top_task}</b>입니다.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 추천 개입 조치
# =========================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">추천 개입 조치</div>', unsafe_allow_html=True)

if analysis_data is None:
    st.markdown('<div class="recommend-box">필터를 설정한 뒤 <b>분석 실행</b> 버튼을 누르면 현재 조건에 맞는 개입 조치가 생성됩니다.</div>', unsafe_allow_html=True)
elif count == 0:
    st.markdown('<div class="recommend-box">데이터가 부족하여 개입 조치를 추천할 수 없습니다.</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="recommend-box">{recommend_action}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)