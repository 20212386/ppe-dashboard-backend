import streamlit as st
import pandas as pd
import requests

API_BASE = "https://ppe-dashboard-backend.onrender.com"

st.set_page_config(page_title="위험패턴 분석", page_icon="📊", layout="wide")

st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
.metric-card {
    background: #ffffff;
    border-radius: 24px;
    padding: 22px 22px 18px 22px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    min-height: 152px;
    border: 1px solid #f1f5f9;
}
.metric-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
}
.metric-label {
    font-size: 18px;
    font-weight: 800;
    color: #1f2937;
    line-height: 1.35;
    margin-bottom: 10px;
}
.metric-value {
    font-size: 32px;
    font-weight: 900;
    color: #111827;
    line-height: 1.1;
    word-break: keep-all;
}
.metric-badge {
    display: inline-block;
    margin-top: 12px;
    border-radius: 999px;
    padding: 6px 12px;
    font-size: 14px;
    font-weight: 700;
}
.metric-icon {
    min-width: 48px;
    height: 48px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
}
.small-stat {
    margin-top: 10px;
    color: #475569;
    font-size: 16px;
    font-weight: 600;
}
.section-card {
    background: #ffffff;
    border-radius: 24px;
    padding: 22px 22px 18px 22px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    border: 1px solid #f1f5f9;
    min-height: 420px;
}
.section-title {
    font-size: 28px;
    font-weight: 900;
    color: #111827;
    margin-bottom: 6px;
}
.section-sub {
    font-size: 16px;
    color: #64748b;
    margin-bottom: 18px;
}
.analysis-guide {
    margin-top: 18px;
    border: 1px dashed #e2e8f0;
    border-radius: 18px;
    padding: 18px;
    color: #475569;
    font-size: 16px;
    background: #fafafa;
}
.insight-box {
    margin-top: 14px;
    border-radius: 18px;
    padding: 14px 16px;
    font-size: 15px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


def render_metric_card(title, value, badge_text, accent, badge_bg, badge_fg, icon_bg, icon, icon_fg="#111827"):
    st.markdown(
        f"""
        <div class="metric-card" style="border-left:6px solid {accent};">
            <div class="metric-top">
                <div style="width: 72%;">
                    <div class="metric-label">{title}</div>
                    <div class="metric-value">{value}</div>
                    <span class="metric-badge" style="background:{badge_bg}; color:{badge_fg};">{badge_text}</span>
                </div>
                <div class="metric-icon" style="background:{icon_bg}; color:{icon_fg};">
                    {icon}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_empty_chart_message(message: str):
    st.markdown(f'<div class="analysis-guide">{message}</div>', unsafe_allow_html=True)


def fetch_analysis_data(params: dict):
    try:
        response = requests.get(
            f"{API_BASE}/analysis/detail",
            params=params,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"분석 데이터 조회 실패: {e}")
        return None


def _safe_counts_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["label", "count"])

    out = df.copy()

    if "label" not in out.columns:
        out["label"] = ""
    if "count" not in out.columns:
        out["count"] = 0

    out["label"] = out["label"].fillna("").astype(str)
    out["count"] = pd.to_numeric(out["count"], errors="coerce").fillna(0).astype(int)

    out = out[out["label"] != ""].reset_index(drop=True)
    return out


def render_html_bar_chart(df: pd.DataFrame, color: str = "#3b82f6"):
    df = _safe_counts_df(df)

    if df.empty:
        render_empty_chart_message("🚨 <b>조건에 맞는 데이터가 없습니다.</b>")
        return

    max_count = max(int(df["count"].max()), 1)

    rows = []
    for _, row in df.iterrows():
        label = str(row["label"])
        count = int(row["count"])
        width = max((count / max_count) * 100, 6)

        rows.append(
            f"""
            <div style="margin-bottom:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; gap:10px;">
                    <div style="font-size:15px; font-weight:700; color:#334155; word-break:keep-all;">{label}</div>
                    <div style="font-size:14px; font-weight:800; color:#0f172a;">{count}</div>
                </div>
                <div style="width:100%; height:14px; background:#eef2f7; border-radius:999px; overflow:hidden;">
                    <div style="width:{width}%; height:14px; background:{color}; border-radius:999px;"></div>
                </div>
            </div>
            """
        )

    st.markdown(
        f"""
        <div style="margin-top:8px;">
            {''.join(rows)}
        </div>
        """,
        unsafe_allow_html=True
    )


if "p3_analysis_data" not in st.session_state:
    st.session_state["p3_analysis_data"] = None

st.markdown("## 위험패턴 분석")
st.caption("현장, 날짜, 작업 조건에 따라 반복 위험 패턴을 좁혀서 볼 수 있습니다.")

f1, f2, f3 = st.columns(3)
f4, f5, f6 = st.columns(3)
f7, f8 = st.columns([1, 2])

with f1:
    start_date = st.text_input("시작 날짜", value="2026-03-01")

with f2:
    end_date = st.text_input("종료 날짜", value="2026-03-31")

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
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    run_analysis = st.button("분석 실행", use_container_width=True)

params = {
    "start_date": start_date or None,
    "end_date": end_date or None,
    "site": site or None,
    "zone": zone or None,
    "task_type": task_type or None,
    "ppe_type": ppe_type or None,
    "risk_exposure": (1 if risk_exposure == "O" else 0) if risk_exposure in ["O", "X"] else None,
}

if run_analysis:
    st.session_state["p3_analysis_data"] = fetch_analysis_data(params)

st.markdown("### DDEBUG PARAMS:")
with st.expander("", expanded=True):
    st.json(params)

analysis_data = st.session_state.get("p3_analysis_data")

if analysis_data:
    count = analysis_data.get("count", 0)
    kpis = analysis_data.get("kpis", {})
    charts = analysis_data.get("charts", {})
    recommend_action = analysis_data.get("recommend_action", "추천 조치가 없습니다.")
else:
    count = 0
    kpis = {}
    charts = {}
    recommend_action = "필터를 설정한 뒤 분석 실행 버튼을 눌러주세요."

time_df = _safe_counts_df(pd.DataFrame(charts.get("time_chart", [])))
ppe_df = _safe_counts_df(pd.DataFrame(charts.get("ppe_chart", [])))
zone_df = _safe_counts_df(pd.DataFrame(charts.get("zone_chart", [])))
task_df = _safe_counts_df(pd.DataFrame(charts.get("task_chart", [])))

top_time = kpis.get("top_time") or "-"
top_zone = kpis.get("top_zone") or "-"
top_task = kpis.get("top_task_type") or "-"
top_ppe = kpis.get("top_ppe") or "-"

c1, c2, c3, c4 = st.columns(4)

with c1:
    render_metric_card("가장 위험한 시간대", top_time, "위반 집중", "#ef4444", "#fef2f2", "#b91c1c", "#fff1f2", "⏰")

with c2:
    render_metric_card("가장 취약한 구역", top_zone, "위험 패턴 상위", "#f97316", "#fff7ed", "#c2410c", "#fff7ed", "📍")

with c3:
    render_metric_card("반복 위험 작업유형", top_task, "반복 분석", "#eab308", "#fefce8", "#a16207", "#fefce8", "📉")

with c4:
    render_metric_card("가장 많이 누락된 PPE", top_ppe, "누락 상위", "#a855f7", "#faf5ff", "#7e22ce", "#faf5ff", "👜")

st.markdown(f'<div class="small-stat">현재 필터 조건에 맞는 데이터 건수: <b>{count}</b></div>', unsafe_allow_html=True)

r1c1, r1c2 = st.columns(2)

with r1c1:
    st.markdown(
        '<div class="section-card"><div class="section-title">시간대별 위반 건수</div><div class="section-sub">시간대별 반복 위반 분포를 확인합니다</div>',
        unsafe_allow_html=True
    )

    if analysis_data is None:
        render_empty_chart_message("필터를 설정하고 <b>분석 실행</b>을 누르세요.")
    elif time_df.empty:
        render_empty_chart_message("🚨 <b>조건에 맞는 데이터가 없습니다.</b>")
    else:
        render_html_bar_chart(time_df, color="#3b82f6")
        st.markdown(
            f'<div class="insight-box" style="background:#eff6ff; border:1px solid #bfdbfe; color:#1e3a8a;">패턴 해석: 가장 위반이 집중된 시간대는 <b>{top_time}</b>입니다.</div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

with r1c2:
    st.markdown(
        '<div class="section-card"><div class="section-title">PPE별 위반 건수</div><div class="section-sub">누락 빈도가 높은 보호구를 확인합니다</div>',
        unsafe_allow_html=True
    )

    if analysis_data is None:
        render_empty_chart_message("필터를 설정하고 <b>분석 실행</b>을 누르세요.")
    elif ppe_df.empty:
        render_empty_chart_message("🚨 <b>조건에 맞는 데이터가 없습니다.</b>")
    else:
        render_html_bar_chart(ppe_df, color="#8b5cf6")
        st.markdown(
            f'<div class="insight-box" style="background:#faf5ff; border:1px solid #e9d5ff; color:#6b21a8;">패턴 해석: 가장 많이 누락된 PPE는 <b>{top_ppe}</b>입니다.</div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

r2c1, r2c2 = st.columns(2)

with r2c1:
    st.markdown(
        '<div class="section-card"><div class="section-title">구역별 위반 건수</div><div class="section-sub">어느 작업구역에 위반이 몰리는지 봅니다</div>',
        unsafe_allow_html=True
    )

    if analysis_data is None:
        render_empty_chart_message("필터를 설정하고 <b>분석 실행</b>을 누르세요.")
    elif zone_df.empty:
        render_empty_chart_message("🚨 <b>조건에 맞는 데이터가 없습니다.</b>")
    else:
        render_html_bar_chart(zone_df, color="#f97316")
        st.markdown(
            f'<div class="insight-box" style="background:#fff7ed; border:1px solid #fed7aa; color:#9a3412;">패턴 해석: 가장 취약한 구역은 <b>{top_zone}</b>입니다.</div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

with r2c2:
    st.markdown(
        '<div class="section-card"><div class="section-title">작업유형별 위반 건수</div><div class="section-sub">반복 위반이 몰리는 작업유형을 확인합니다</div>',
        unsafe_allow_html=True
    )

    if analysis_data is None:
        render_empty_chart_message("필터를 설정하고 <b>분석 실행</b>을 누르세요.")
    elif task_df.empty:
        render_empty_chart_message("🚨 <b>조건에 맞는 데이터가 없습니다.</b>")
    else:
        render_html_bar_chart(task_df, color="#eab308")
        st.markdown(
            f'<div class="insight-box" style="background:#fefce8; border:1px solid #fde68a; color:#854d0e;">패턴 해석: 반복 위험 작업유형은 <b>{top_task}</b>입니다.</div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("### 권장 조치")
st.markdown(
    f"""
    <div class="analysis-guide">
        {recommend_action}
    </div>
    """,
    unsafe_allow_html=True
)