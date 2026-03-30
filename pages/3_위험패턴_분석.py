import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="위험패턴 분석", page_icon="📊", layout="wide")

API_BASE = "https://ppe-dashboard-backend.onrender.com"

# =========================
# 1. 스타일
# =========================
st.markdown("""
<style>
.block-container { padding-top: 1.7rem; padding-bottom: 2rem; max-width: 1500px; }
.main-title { font-size: 2.15rem; font-weight: 800; color: #0f172a; line-height: 1.2; letter-spacing: -0.02em; margin-bottom: 0.25rem; }
.sub-title { font-size: 0.98rem; color: #64748b; margin-bottom: 1.1rem; }
.filter-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 24px; padding: 22px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05); margin-bottom: 1rem; }
.section-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 22px; padding: 22px 22px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05); margin-bottom: 1rem; height: 100%; }
.section-title { font-size: 1.16rem; font-weight: 800; color: #0f172a; margin-bottom: 0.35rem; }
.section-sub { color: #64748b; font-size: 0.88rem; margin-bottom: 1.2rem; }
.metric-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 20px; padding: 18px 20px; min-height: 158px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05); }
.metric-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; }
.metric-left { flex: 1; min-width: 0; }
.metric-label { color: #64748b; font-size: 0.92rem; font-weight: 700; margin-bottom: 10px; line-height: 1.45; word-break: keep-all; }
.metric-value { color: #0f172a; font-size: 1.72rem; font-weight: 800; line-height: 1.18; letter-spacing: -0.02em; margin-bottom: 10px; word-break: keep-all; white-space: normal; }
.metric-badge { display: inline-block; padding: 7px 11px; border-radius: 999px; font-size: 0.76rem; font-weight: 800; }
.metric-icon { width: 52px; height: 52px; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 1.28rem; flex-shrink: 0; }
.insight-box { border-radius: 16px; padding: 16px 18px; margin-top: 0.5rem; font-size: 0.92rem; font-weight: 700; border: 1px solid; line-height: 1.6; }
.recommend-box { background: linear-gradient(135deg, #eef4ff 0%, #dbeafe 100%); border: 1px solid #bfdbfe; border-radius: 18px; padding: 18px; color: #1e3a8a; font-size: 0.96rem; font-weight: 700; }
.analysis-guide { background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 18px; padding: 18px; color: #475569; font-size: 0.92rem; text-align: center; }
.small-stat { color: #64748b; font-size: 0.9rem; margin: 0.2rem 0 0.9rem 0; }
.stButton > button { border-radius: 14px; font-weight: 800; min-height: 46px; }
div[data-testid="stDateInput"] label, div[data-testid="stSelectbox"] label { font-weight: 700; color: #334155; }
</style>
""", unsafe_allow_html=True)

# =========================
# 2. 렌더링 함수들
# =========================
def render_metric_card(title, value, badge_text, accent, badge_bg, badge_fg, icon_bg, icon_fg, icon_symbol):
    st.markdown(f"""
        <div class="metric-card" style="border-left:6px solid {accent};">
            <div class="metric-top">
                <div class="metric-left">
                    <div class="metric-label" title="{title}">{title}</div>
                    <div class="metric-value" title="{value}">{value}</div>
                    <span class="metric-badge" style="background:{badge_bg}; color:{badge_fg};">{badge_text}</span>
                </div>
                <div class="metric-icon" style="background:{icon_bg}; color:{icon_fg};">{icon_symbol}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_empty_chart_message(message: str):
    st.markdown(f'<div class="analysis-guide">{message}</div>', unsafe_allow_html=True)

def fetch_analysis_data(params: dict):
    try:
        clean_params = {k: v for k, v in params.items() if v is not None and v != ""}
        res = requests.get(f"{API_BASE}/analysis/detail", params=clean_params, timeout=60)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"분석 데이터 조회 실패: {e}")
        return None

def _safe_counts_df(df_data, all_categories=None) -> pd.DataFrame:
    df = pd.DataFrame(df_data)
    if df.empty or "label" not in df.columns or "count" not in df.columns:
        df = pd.DataFrame(columns=["label", "count", "compliance_rate", "risk_rate"])
    else:
        df["label"] = df["label"].fillna("").astype(str)
        df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)

    if all_categories:
        cat_df = pd.DataFrame({"label": all_categories})
        df = pd.merge(cat_df, df, on="label", how="left").fillna(0)
        if "count" in df.columns: df["count"] = df["count"].astype(int)
        if "compliance_rate" not in df.columns: df["compliance_rate"] = 0.0
        if "risk_rate" not in df.columns: df["risk_rate"] = 0.0
        
    return df[df["label"] != ""].reset_index(drop=True)

# =========================
# 3. 화면 UI 및 필터
# =========================
if "p3_analysis_data" not in st.session_state:
    st.session_state["p3_analysis_data"] = None

st.markdown('<div class="main-title">위험패턴 분석</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">필터 조건에 맞는 반복 위험 패턴을 분석하고 개입 우선순위를 확인합니다</div>', unsafe_allow_html=True)

st.markdown('<div class="filter-card"><div class="section-title">분석 필터</div><div class="section-sub">현장, 날짜, 작업 조건에 따라 반복 위험 패턴을 좁혀서 볼 수 있습니다</div>', unsafe_allow_html=True)

f1, f2, f3 = st.columns(3)
f4, f5, f6 = st.columns(3)
f7, f8 = st.columns([1, 2])

with f1: start_date = st.text_input("시작 날짜", value="2026-03-01")
with f2: end_date = st.text_input("종료 날짜", value="2026-03-31")
with f3: site = st.selectbox("현장", ["", "현장1", "현장2", "현장3"])
with f4: zone = st.selectbox("작업구역", ["", "고소작업구역", "절단작업구역", "자재운반구역", "설비점검구역"])
with f5: task_type = st.selectbox("작업유형", ["", "고소작업", "절단작업", "자재운반", "설비점검"])
with f6: ppe_type = st.selectbox("PPE 종류", ["", "장갑", "안전모", "랜야드"])
with f7: risk_exposure = st.selectbox("위험노출 여부", ["", "O", "X"])
with f8:
    st.markdown("<div style='margin-top: 28.5px;'></div>", unsafe_allow_html=True)
    run_analysis = st.button("분석 실행", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

params = {
    "start_date": start_date or None, "end_date": end_date or None, "site": site or None,
    "zone": zone or None, "task_type": task_type or None, "ppe_type": ppe_type or None,
    "risk_exposure": (1 if risk_exposure == "O" else 0) if risk_exposure in ["O", "X"] else None,
}

if run_analysis:
    st.session_state["p3_analysis_data"] = fetch_analysis_data(params)

analysis_data = st.session_state["p3_analysis_data"]

if analysis_data:
    count = analysis_data.get("count", 0)
    kpis = analysis_data.get("kpis", {})
    charts = analysis_data.get("charts", {})
    recommend_action = analysis_data.get("recommend_action", "추천 조치가 없습니다.")
else:
    count, kpis, charts, recommend_action = 0, {}, {}, "필터를 설정한 뒤 '분석 실행' 버튼을 눌러주세요."

time_cats = ["오전", "점심직후", "오후"]
ppe_cats = ["안전모", "랜야드", "장갑"]
zone_cats = ["고소작업구역", "절단작업구역", "자재운반구역", "설비점검구역"]
task_cats = ["고소작업", "절단작업", "자재운반", "설비점검"]

time_df = _safe_counts_df(charts.get("time_chart", []), time_cats)
ppe_df = _safe_counts_df(charts.get("ppe_chart", []), ppe_cats)
zone_df = _safe_counts_df(charts.get("zone_chart", []), zone_cats)
task_df = _safe_counts_df(charts.get("task_chart", []), task_cats)

top_time, top_zone, top_task, top_ppe = kpis.get("top_time") or "-", kpis.get("top_zone") or "-", kpis.get("top_task_type") or "-", kpis.get("top_ppe") or "-"

# =========================
# 4. KPI 카드
# =========================
c1, c2, c3, c4 = st.columns(4)
with c1: render_metric_card("가장 위험한 시간대", top_time, "위반 집중", "#ef4444", "#fef2f2", "#b91c1c", "#fef2f2", "#ef4444", "⏰")
with c2: render_metric_card("가장 취약한 구역", top_zone, "위험 패턴 상위", "#f97316", "#fff7ed", "#c2410c", "#fff7ed", "#f97316", "📍")
with c3: render_metric_card("반복 위험 작업유형", top_task, "반복 분석", "#eab308", "#fefce8", "#a16207", "#fefce8", "#ca8a04", "📉")
with c4: render_metric_card("가장 많이 누락된 PPE", top_ppe, "누락 상위", "#a855f7", "#faf5ff", "#7e22ce", "#faf5ff", "#9333ea", "⛑")
st.markdown(f'<div class="small-stat">현재 필터 조건에 맞는 데이터 건수: <b>{count}</b></div>', unsafe_allow_html=True)

# =========================
# 5. 차트 렌더링
# =========================
r1c1, r1c2 = st.columns(2)

with r1c1:
    st.markdown('<div class="section-card"><div class="section-title">시간대별 위반 건수</div><div class="section-sub">시간대별 반복 위반 분포를 확인합니다</div>', unsafe_allow_html=True)
    if analysis_data is None: render_empty_chart_message("필터를 설정하고 <b>분석 실행</b>을 누르면 데이터가 표시됩니다.")
    else:
        fig_time = go.Figure(go.Bar(
            x=time_df["label"].tolist(), y=time_df["count"].tolist(), 
            marker=dict(color="rgba(59, 130, 246, 0.75)", line=dict(color="#2563eb", width=1.5)), 
            width=0.45
        ))
        y_max = max(4, int(time_df["count"].max()) + (int(time_df["count"].max()) * 0.1))
        fig_time.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", paper_bgcolor="white", xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#334155")), yaxis=dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False, tickfont=dict(size=11, color="#94a3b8"), range=[0, y_max]))
        st.plotly_chart(fig_time, use_container_width=True, config={"displayModeBar": False}, key="p3_violation_chart")
    st.markdown('</div>', unsafe_allow_html=True)

with r1c2:
    st.markdown('<div class="section-card"><div class="section-title">PPE별 위반 건수</div><div class="section-sub">누락 빈도가 높은 보호구를 확인합니다</div>', unsafe_allow_html=True)
    if analysis_data is None: render_empty_chart_message("필터를 설정하고 <b>분석 실행</b>을 누르면 데이터가 표시됩니다.")
    else:
        fig_ppe = go.Figure(go.Bar(
            x=ppe_df["label"].tolist(), y=ppe_df["count"].tolist(), 
            marker=dict(color="rgba(168, 85, 247, 0.75)", line=dict(color="#9333ea", width=1.5)), 
            width=0.45
        ))
        y_max = max(4, int(ppe_df["count"].max()) + (int(ppe_df["count"].max()) * 0.1))
        fig_ppe.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", paper_bgcolor="white", xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#334155")), yaxis=dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False, tickfont=dict(size=11, color="#94a3b8"), range=[0, y_max]))
        st.plotly_chart(fig_ppe, use_container_width=True, config={"displayModeBar": False}, key="p3_ppe_chart")
    st.markdown('</div>', unsafe_allow_html=True)

r2c1, r2c2 = st.columns(2)

with r2c1:
    st.markdown('<div class="section-card"><div class="section-title">특정별 위험노출 준수율</div><div class="section-sub">구역별 준수율과 위험도를 100% 기준으로 비교합니다</div>', unsafe_allow_html=True)
    if analysis_data is None: render_empty_chart_message("필터를 설정하고 <b>분석 실행</b>을 누르면 데이터가 표시됩니다.")
    else:
        fig_zone = go.Figure()
        fig_zone.add_trace(go.Bar(
            x=zone_df["label"].tolist(), y=zone_df["compliance_rate"].tolist(), 
            name="준수율 %", 
            marker=dict(color="rgba(34, 197, 94, 0.75)", line=dict(color="#16a34a", width=1.5)), 
            width=0.35
        ))
        fig_zone.add_trace(go.Bar(
            x=zone_df["label"].tolist(), y=zone_df["risk_rate"].tolist(), 
            name="위험도 %", 
            marker=dict(color="rgba(239, 68, 68, 0.75)", line=dict(color="#dc2626", width=1.5)), 
            width=0.35
        ))
        
        fig_zone.update_layout(
            barmode="group", height=360, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", paper_bgcolor="white", 
            showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
            bargap=0.45, bargroupgap=0.1,
            yaxis=dict(range=[0, 100], dtick=20, gridcolor="#f1f5f9", zeroline=False, tickfont=dict(size=11, color="#94a3b8"), ticksuffix="%"),
            xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#334155"))
        )
        st.plotly_chart(fig_zone, use_container_width=True, config={"displayModeBar": False}, key="p3_zone_chart")
    st.markdown('</div>', unsafe_allow_html=True)

with r2c2:
    st.markdown('<div class="section-card"><div class="section-title">작업유형별 위반 분포</div><div class="section-sub">개입이 필요한 고위험 작업유형 분포를 확인합니다</div>', unsafe_allow_html=True)
    if analysis_data is None: render_empty_chart_message("필터를 설정하고 <b>분석 실행</b>을 누르면 데이터가 표시됩니다.")
    else:
        fig_task = go.Figure(go.Bar(
            y=task_df["label"].tolist(), x=task_df["count"].tolist(), orientation="h", 
            marker=dict(color="rgba(59, 130, 246, 0.75)", line=dict(color="#2563eb", width=1.5)), 
            width=0.45, hovertemplate="작업유형: %{y}<br>건수: %{x}건<extra></extra>"
        ))
        x_max = max(4, int(task_df["count"].max()) + (int(task_df["count"].max()) * 0.1))
        fig_task.update_layout(
            height=360, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", paper_bgcolor="white", 
            showlegend=False, bargap=0.45,
            yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(size=12, color="#334155")),
            xaxis=dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False, tickfont=dict(size=11, color="#94a3b8"), range=[0, x_max])
        )
        st.plotly_chart(fig_task, use_container_width=True, config={"displayModeBar": False}, key="p3_task_chart")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card"><div class="section-title">추천 개입 조치</div>', unsafe_allow_html=True)
st.markdown(f'<div class="recommend-box">{recommend_action}</div></div>', unsafe_allow_html=True)