import streamlit as st
import requests

API_BASE = "https://ppe-dashboard-backend.onrender.com"

st.set_page_config(page_title="메인 대시보드", page_icon="🦺", layout="wide")

st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
.metric-card {
    background: #ffffff;
    border-radius: 22px;
    padding: 22px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    border: 1px solid #eef2f7;
    min-height: 150px;
}
.metric-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
}
.metric-title {
    font-size: 17px;
    font-weight: 800;
    color: #334155;
    margin-bottom: 10px;
}
.metric-value {
    font-size: 34px;
    font-weight: 900;
    color: #0f172a;
    line-height: 1.1;
}
.metric-sub {
    margin-top: 12px;
    font-size: 14px;
    font-weight: 700;
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
}
.metric-icon {
    width: 46px;
    height: 46px;
    border-radius: 14px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 22px;
}
.section-card {
    background: #ffffff;
    border-radius: 24px;
    padding: 22px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    border: 1px solid #eef2f7;
}
.section-title {
    font-size: 26px;
    font-weight: 900;
    color: #111827;
    margin-bottom: 6px;
}
.section-sub {
    font-size: 15px;
    color: #64748b;
    margin-bottom: 18px;
}
.small-note {
    margin-top: 10px;
    color: #475569;
    font-size: 15px;
    font-weight: 600;
}
.bar-row {
    margin-bottom: 16px;
}
.bar-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}
.bar-label {
    font-size: 15px;
    font-weight: 700;
    color: #334155;
}
.bar-value {
    font-size: 14px;
    font-weight: 800;
    color: #111827;
}
.bar-bg {
    width: 100%;
    height: 14px;
    background: #eef2f7;
    border-radius: 999px;
    overflow: hidden;
}
.bar-fill {
    height: 14px;
    border-radius: 999px;
}
.guide-box {
    border: 1px dashed #e2e8f0;
    border-radius: 18px;
    padding: 18px;
    color: #475569;
    background: #fafafa;
}
</style>
""", unsafe_allow_html=True)


def render_metric_card(title, value, sub, accent, sub_bg, sub_fg, icon, icon_bg):
    st.markdown(
        f"""
        <div class="metric-card" style="border-left:6px solid {accent};">
            <div class="metric-top">
                <div>
                    <div class="metric-title">{title}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-sub" style="background:{sub_bg}; color:{sub_fg};">{sub}</div>
                </div>
                <div class="metric-icon" style="background:{icon_bg};">{icon}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_empty(msg="데이터가 없습니다."):
    st.markdown(f'<div class="guide-box">{msg}</div>', unsafe_allow_html=True)


def safe_df(data):
    import pandas as pd
    if not data:
        return pd.DataFrame(columns=["label", "count"])
    df = pd.DataFrame(data)
    if "label" not in df.columns:
        df["label"] = ""
    if "count" not in df.columns:
        df["count"] = 0
    df["label"] = df["label"].fillna("").astype(str)
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
    df = df[df["label"] != ""].reset_index(drop=True)
    return df


def render_bar_list(df, color):
    df = safe_df(df)
    if df.empty:
        render_empty("표시할 데이터가 없습니다.")
        return

    max_count = max(int(df["count"].max()), 1)
    html = ""
    for _, row in df.iterrows():
        label = str(row["label"])
        count = int(row["count"])
        width = max((count / max_count) * 100, 8)

        html += f"""
        <div class="bar-row">
            <div class="bar-head">
                <div class="bar-label">{label}</div>
                <div class="bar-value">{count}</div>
            </div>
            <div class="bar-bg">
                <div class="bar-fill" style="width:{width}%; background:{color};"></div>
            </div>
        </div>
        """
    st.markdown(html, unsafe_allow_html=True)


@st.cache_data(ttl=30)
def fetch_dashboard_data():
    try:
        response = requests.get(f"{API_BASE}/dashboard/summary", timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"대시보드 데이터 조회 실패: {e}")
        return None


st.markdown("## PPE 안전관리 메인 대시보드")
st.caption("현장 전체 안전 현황을 한눈에 확인합니다.")

data = fetch_dashboard_data()

if not data:
    render_empty("백엔드 응답이 없어서 대시보드를 불러오지 못했습니다.")
    st.stop()

# 백엔드 응답 구조 가정
overall_compliance = data.get("overall_compliance_rate", 0)
total_logs = data.get("total_logs", 0)
violations = data.get("total_violations", 0)
weakest_zone = data.get("weakest_zone", {}).get("zone", "-")
weakest_zone_count = data.get("weakest_zone", {}).get("count", 0)
most_missing = data.get("most_missing_ppe", {}).get("ppe", "-")
most_missing_count = data.get("most_missing_ppe", {}).get("count", 0)

hourly_data = data.get("hourly_violations", [])
zone_risk_data = data.get("zone_risk_scores", [])
safety_points = data.get("safety_points", [])

c1, c2, c3, c4 = st.columns(4)

with c1:
    render_metric_card(
        "전체 준수율",
        f"{overall_compliance}%",
        "종합 안전 수준",
        "#22c55e",
        "#f0fdf4",
        "#166534",
        "✅",
        "#dcfce7"
    )

with c2:
    render_metric_card(
        "전체 점검 건수",
        f"{total_logs}",
        "누적 로그 수",
        "#3b82f6",
        "#eff6ff",
        "#1d4ed8",
        "📋",
        "#dbeafe"
    )

with c3:
    render_metric_card(
        "전체 위반 건수",
        f"{violations}",
        "위험 감지",
        "#ef4444",
        "#fef2f2",
        "#b91c1c",
        "🚨",
        "#fee2e2"
    )

with c4:
    render_metric_card(
        "취약 구역",
        weakest_zone,
        f"위반 {weakest_zone_count}건",
        "#f97316",
        "#fff7ed",
        "#c2410c",
        "📍",
        "#ffedd5"
    )

st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

r1c1, r1c2 = st.columns(2)

with r1c1:
    st.markdown(
        '<div class="section-card"><div class="section-title">시간대별 위반 현황</div><div class="section-sub">어느 시간대에 위반이 많이 몰리는지 확인합니다</div>',
        unsafe_allow_html=True
    )
    render_bar_list(hourly_data, "#3b82f6")
    st.markdown('</div>', unsafe_allow_html=True)

with r1c2:
    st.markdown(
        '<div class="section-card"><div class="section-title">구역별 위험도</div><div class="section-sub">구역별 위험 수준을 비교합니다</div>',
        unsafe_allow_html=True
    )
    render_bar_list(zone_risk_data, "#f97316")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

r2c1, r2c2 = st.columns(2)

with r2c1:
    st.markdown(
        '<div class="section-card"><div class="section-title">반복 누락 PPE</div><div class="section-sub">가장 자주 빠지는 보호구를 봅니다</div>',
        unsafe_allow_html=True
    )
    render_bar_list(
        [{"label": most_missing, "count": most_missing_count}] if most_missing != "-" else [],
        "#8b5cf6"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with r2c2:
    st.markdown(
        '<div class="section-card"><div class="section-title">안전 포인트</div><div class="section-sub">바로 확인할 핵심 요약입니다</div>',
        unsafe_allow_html=True
    )

    if safety_points:
        for point in safety_points:
            st.markdown(
                f"""
                <div style="margin-bottom:12px; padding:14px 16px; border-radius:16px; background:#f8fafc; border:1px solid #e2e8f0; font-size:15px; font-weight:600; color:#334155;">
                    • {point}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        render_empty("안전 포인트 데이터가 없습니다.")

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    f'<div class="small-note">가장 많이 누락된 PPE는 <b>{most_missing}</b>이며, 총 <b>{most_missing_count}</b>건입니다.</div>',
    unsafe_allow_html=True
)